import collections

import h3

from .footprint import footprint
from .models import CATEGORIES

RESOLVING_S = 600   


def _flood_fill(cells):
    
    seen, groups = set(), []
    for c in cells:
        if c in seen:
            continue
        comp, stack = set(), [c]
        while stack:
            x = stack.pop()
            if x in seen or x not in cells:
                continue
            seen.add(x)
            comp.add(x)
            stack.extend(h3.grid_disk(x, 1))
        groups.append(comp)
    return groups


class Detector:
    

    def __init__(self, data):
        self.data = data
        self.reset()

    def reset(self):
        self.levels = {}          
        self.incidents = {}       
        self._cells = {}          
        self._last_seen = {}      
        self._sig = {}            
        self._next = 1
        self.detect = {}          
        self.false_alarms = set()
        self.reports_10min = 0

    def run(self, reports, now, notices, truth):
        
        agg = collections.defaultdict(lambda: {"dev": set(), "bld": set(), "fine": set(), "reps": []})
        self.reports_10min = 0
        for r in reports:
            if r.t > now or r.t < now - CATEGORIES[r.category][0]:
                continue
            if r.t >= now - 600:
                self.reports_10min += 1
            a = agg[(r.cell8, r.category)]
            if r.kind == "fine":
                a["fine"].add(r.device_id)
            else:
                a["dev"].add(r.device_id)
                a["bld"].add(r.cell11)
                a["reps"].append(r)
        
        self.levels = {}
        for (c, cat), a in agg.items():
            _, yellow, red, min_b = CATEGORIES[cat]
            n, lvl = len(a["dev"]), 0
            if red is not None:
                if n >= red and len(a["bld"]) >= min_b:
                    lvl = 2
                elif n >= yellow:
                    lvl = 1
                if lvl and len(a["fine"]) >= n:
                    lvl -= 1
            if n or a["fine"]:
                self.levels[(c, cat)] = (lvl, n, len(a["fine"]))
        
        flagged = collections.defaultdict(set)
        for (c, cat), (lvl, _, _) in self.levels.items():
            if lvl:
                flagged[cat].add(c)
        groups = [(cat, comp) for cat, cells in flagged.items() for comp in _flood_fill(cells)]
        groups.sort(key=lambda g: -len(g[1]))
        
        cells_now = {}
        for cat, comp in groups:
            old = [i for i, (pc, cells) in self._cells.items() if pc == cat and cells & comp and i not in cells_now]
            iid = min(old, key=lambda s: int(s[4:])) if old else self._new_id()
            cells_now[iid] = (cat, comp)
            self._last_seen[iid] = now
            self.incidents[iid] = self._describe(iid, cat, comp, agg, notices, now)
        for iid in list(self.incidents):
            if iid in cells_now:
                continue
            cat, cells = self._cells.get(iid, (None, set()))
            merged = any(c == cat and cells & comp for c, comp in cells_now.values())
            if merged or now - self._last_seen.get(iid, now) > RESOLVING_S:
                del self.incidents[iid]                     
            else:
                self.incidents[iid].update(status="resolving", level=0)
        self._cells = {**{i: v for i, v in self._cells.items() if i in self.incidents}, **cells_now}
        self._link_related()
        
        self._measure(now, truth)

    def _link_related(self):
        active = [i for i in self.incidents.values() if i["status"] == "active"]
        for a in active:
            a["related_to"] = None
            for b in active:
                if a is not b and a["cat"] != b["cat"] and set(a["cells8"]) & set(b["cells8"]) \
                        and (b["devices"], b["id"]) > (a["devices"], a["id"]):
                    a["related_to"] = b["id"]
                    break

    def _new_id(self):
        self._next += 1
        return f"inc-{self._next - 1}"

    def _describe(self, iid, cat, comp, agg, notices, now):
        reps = [r for c in comp for r in agg[(c, cat)]["reps"]]
        devices = {r.device_id for r in reps}
        cells10, outline = footprint(reps)
        look = self.data.look10
        seeds = {r.cell10 for r in reps}
        res_min = sum(look.get(c, {}).get("residents", 0) for c in seeds & cells10)
        res_max = sum(look.get(c, {}).get("residents", 0) for c in cells10)
        streets, dist = collections.Counter(), collections.Counter()
        for c in (cells10 or seeds):
            v = look.get(c)
            if v:
                dist[v["district_id"]] += v["residents"] + 1
                streets.update(v["streets"])
        if not dist:
            for c in comp:
                dist[self.data.cells8[c]["district_id"]] += 1
        srcs = [n for n in notices.values() if n["cat"] == cat and n["cells8"] & comp]
        official = [n for n in srcs if n["kind"] == "official"]
        news = [n for n in srcs if n["kind"] == "news"]
        level = max(self.levels[(c, cat)][0] for c in comp)
        if official:
            conf, label = "official", f"Confirmed by {official[0]['source']}"
        elif level == 2:
            conf, label = "residents", "Reported by residents"
        else:
            conf, label = "possible", "Possible – few reports"
        lat = sum(self.data.cells8[c]["lat"] for c in comp) / len(comp)
        lng = sum(self.data.cells8[c]["lng"] for c in comp) / len(comp)
        official10 = set().union(*(n["cells10"] for n in official)) if official else set()
        facilities = [f for c in sorted(cells10) for f in self.data.facilities10.get(c, [])]
        return {
            "id": iid, "cat": cat, "level": level, "status": "active",
            "confidence": conf, "label": label,
            "district": self.data.district_names.get(dist.most_common(1)[0][0], ""),
            "devices": len(devices), "first_t": min((r.t for r in reps), default=now),
            "center": {"lat": round(lat, 5), "lng": round(lng, 5)},
            "cells8": sorted(comp), "footprint": outline, "footprint_cells10": sorted(cells10),
            "approximate": len(devices) < 10,
            "residents_at_least": res_min, "residents_up_to": max(res_max, res_min),
            "streets": [s for s, _ in streets.most_common(5)],
            "facilities": facilities[:12], "facilities_total": len(facilities),
            "sources": [{"kind": n["kind"], "source": n["source"], "title": n["title"], "url": n.get("url")} for n in srcs],
            "cause": news[0].get("cause") if news else None,
            "wider_than_official": bool(official10) and bool(cells10 - official10),
            "related_to": None,
        }

    def _measure(self, now, truth):
        true_cells = set()
        for tr in truth:
            for c in tr["cells8"]:
                true_cells.add((c, tr["cat"]))
            if now < tr["start_t"]:
                continue
            best = max((self.levels.get((c, tr["cat"]), (0,))[0] for c in tr["cells8"]), default=0)
            d = self.detect.setdefault(tr["id"], {"category": tr["cat"], "yellow_min": None, "red_min": None})
            mins = round((now - tr["start_t"]) / 60, 1)
            if best >= 1 and d["yellow_min"] is None:
                d["yellow_min"] = mins
            if best >= 2 and d["red_min"] is None:
                d["red_min"] = mins
        for key, (lvl, _, _) in self.levels.items():
            if lvl == 2 and key not in true_cells:
                self.false_alarms.add(key)

    def changed_incidents(self):
        out = []
        for iid, i in self.incidents.items():
            sig = (i["level"], i["devices"], i["confidence"], i["status"], len(i["footprint_cells10"]))
            if self._sig.get(iid) != sig:
                self._sig[iid] = sig
                out.append(i)
        return out

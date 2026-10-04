import collections

WINDOW_S = 1200        
YELLOW, RED = 2, 3     
RESOLVING_S = 600


class LineDetector:
    def __init__(self, lines):
        self.lines = lines
        self.reset()

    def reset(self):
        self.incidents = {}       
        self._first = {}         
        self._last_seen = {}
        self._sig = {}
        self.detect = {}          
        self.false_alarms = set()

    def devices_on(self, line, reports, now):
        return len({r.device_id for r in reports if r.category == "transit" and r.line == line
                    and r.kind == "problem" and r.t >= now - WINDOW_S})

    def run(self, reports, now, notices, truth, area_incidents):
        agg = collections.defaultdict(lambda: {"dev": set(), "fine": set(), "stops": collections.defaultdict(set),
                                               "first": None})
        for r in reports:
            if r.category != "transit" or not r.line or r.t > now or r.t < now - WINDOW_S:
                continue
            a = agg[r.line]
            if r.kind == "fine":
                a["fine"].add(r.device_id)
                continue
            a["dev"].add(r.device_id)
            if r.stop_id:
                a["stops"][r.stop_id].add(r.device_id)
            a["first"] = r.t if a["first"] is None else min(a["first"], r.t)
        seen = set()
        for line, a in agg.items():
            n = len(a["dev"])
            lvl = 2 if n >= RED else 1 if n >= YELLOW else 0
            if lvl and len(a["fine"]) >= n:
                lvl -= 1
            if lvl == 0:
                continue
            iid = f"line-{line}"
            seen.add(iid)
            self._first[iid] = min(self._first.get(iid, a["first"]), a["first"])
            self._last_seen[iid] = now
            self.incidents[iid] = self._describe(iid, line, lvl, a, notices, area_incidents)
        for iid in list(self.incidents):
            if iid in seen:
                continue
            if now - self._last_seen.get(iid, now) > RESOLVING_S:
                del self.incidents[iid]
                self._first.pop(iid, None)
            else:
                self.incidents[iid].update(status="resolving", level=0)
        self._measure(now, truth)

    def _describe(self, iid, line, lvl, a, notices, area_incidents):
        L = self.lines
        stops = sorted(({"stop_id": sid, "name": L.stops[sid]["name"], "lat": L.stops[sid]["lat"],
                         "lng": L.stops[sid]["lng"], "devices": len(devs)} for sid, devs in a["stops"].items()),
                       key=lambda s: -s["devices"])
        srcs = [n for n in notices.values() if n["cat"] == "transit" and line in n.get("lines", ())]
        official = [n for n in srcs if n["kind"] == "official"]
        news = [n for n in srcs if n["kind"] == "news"]
        cells = {L.stops[s["stop_id"]]["cell8"] for s in stops}
        related = next((i["id"] for i in area_incidents.values()
                        if i["status"] == "active" and i["cat"] in ("flood", "road", "power") and cells & set(i["cells8"])), None)
        if official:
            conf, label = "official", f"Confirmed by {official[0]['source']}"
        elif lvl == 2:
            conf, label = "residents", "Reported by passengers"
        else:
            conf, label = "possible", "Possible – few reports"
        if stops:
            lat = sum(s["lat"] for s in stops) / len(stops)
            lng = sum(s["lng"] for s in stops) / len(stops)
        else:
            mid = L.stops[L.line_stops[line][len(L.line_stops[line]) // 2]] if L.line_stops.get(line) else {"lat": 50.06, "lng": 19.94}
            lat, lng = mid["lat"], mid["lng"]
        return {"id": iid, "cat": "transit", "line": line, "mode": L.line_mode.get(line, "bus"),
                "color": L.line_color.get(line, "#5c6b7a"), "level": lvl, "status": "active",
                "confidence": conf, "label": label, "devices": len(a["dev"]), "first_t": self._first[iid],
                "stops": stops[:12], "center": {"lat": round(lat, 5), "lng": round(lng, 5)},
                "sources": [{"kind": n["kind"], "source": n["source"], "title": n["title"], "url": n.get("url")} for n in srcs],
                "cause": news[0].get("cause") if news else None, "related_to": related,
                "district": f"line {line}"}

    def _measure(self, now, truth):
        true_lines = set()
        for tr in truth:
            true_lines |= set(tr["lines"])
            if now < tr["start_t"]:
                continue
            best = max((self.incidents.get(f"line-{l}", {}).get("level", 0) for l in tr["lines"]), default=0)
            d = self.detect.setdefault(tr["id"], {"category": "transit", "yellow_min": None, "red_min": None})
            mins = round((now - tr["start_t"]) / 60, 1)
            if best >= 1 and d["yellow_min"] is None:
                d["yellow_min"] = mins
            if best >= 2 and d["red_min"] is None:
                d["red_min"] = mins
        for i in self.incidents.values():
            if i["level"] == 2 and i["line"] not in true_lines:
                self.false_alarms.add(i["line"])

    def public(self, clock):
        out = sorted(self.incidents.values(), key=lambda i: (-i["level"], -i["devices"]))
        return [{**i, "first_clock": clock.label(i["first_t"])} for i in out]

    def changed(self):
        out = []
        for iid, i in self.incidents.items():
            sig = (i["level"], i["devices"], i["confidence"], i["status"])
            if self._sig.get(iid) != sig:
                self._sig[iid] = sig
                out.append(i)
        return out

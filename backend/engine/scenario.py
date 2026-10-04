import h3
import yaml
from shapely.geometry import shape


def _cells11(geom):
    return set(h3.geo_to_cells(geom, 11))


def _line_points(geom, step_m=25):
    ls = shape(geom)
    n = max(2, int(ls.length * 80_000 / step_m))      
    return [ls.interpolate(i / (n - 1), normalized=True).coords[0] for i in range(n)]


def _find(data, scenario_id):
    for d in data.scenario_dirs:
        p = d / f"{scenario_id}.yaml"
        if p.exists():
            return p
    raise FileNotFoundError(f"scenario {scenario_id} not found")


class Scenario:
    def __init__(self, data, scenario_id):
        self.data = data
        cfg = yaml.safe_load(open(_find(data, scenario_id), encoding="utf-8"))
        self.id, self.title, self.start_clock = scenario_id, cfg.get("title", scenario_id), cfg["start_clock"]
        self.bg_rate = cfg.get("background", {}).get("reports_per_user_per_day", 0.02)
        self.random = cfg.get("random_incidents") or {}          
        self.random_lines = cfg.get("random_line_incidents") or {}
        self.incidents, self.truth, self.line_truth = [], [], []
        for inc in cfg.get("incidents") or []:
            inc = dict(inc)
            inc["start_t"] = inc["start_min"] * 60
            inc["end_t"] = inc.get("end_min", inc["start_min"] + inc.get("duration_min", 60)) * 60
            if inc["mode"] == "line":                             
                inc["lines"] = [str(l) for l in inc["lines"]]
                self.incidents.append(inc)
                self.line_truth.append({"id": inc["id"], "lines": inc["lines"], "start_t": inc["start_t"]})
                continue
            if "area" in inc:
                inc["cells11"] = _cells11(data.feature(inc["area"])["geometry"])
                cells8 = {h3.cell_to_parent(c, 8) for c in inc["cells11"]}
            elif "line" in inc:
                inc["points"] = _line_points(data.feature(inc["line"])["geometry"])
                cells8 = {h3.latlng_to_cell(lat, lng, 8) for lng, lat in inc["points"]}
            else:                                                 
                lng, lat = data.feature(inc["point"])["geometry"]["coordinates"]
                inc["point_cell11"] = h3.latlng_to_cell(lat, lng, 11)
                cells8 = set()
            self.incidents.append(inc)
            if inc["mode"] != "spam":                             
                self.truth.append({"id": inc["id"], "cat": inc["category"], "cells8": cells8,
                                   "start_t": inc["start_t"]})
                wrong = inc.get("wrong_category")
                if wrong:                                         
                    self.truth.append({"id": f"{inc['id']} (as {wrong['category']})", "cat": wrong["category"],
                                       "cells8": cells8, "start_t": inc["start_t"]})
        self.events = sorted(cfg.get("events") or [], key=lambda e: e["at_min"])

    def events_between(self, t0, t1):
        return [e for e in self.events if t0 <= e["at_min"] * 60 < t1]

    def load_notice(self, rel):
        n = self.data.json(rel)
        area = self.data.feature({"file": n["area_file"], "feature": n["area_feature"]})["geometry"]
        c11 = _cells11(area)
        return {"id": n["id"], "kind": n["kind"], "source": n["source"], "cat": n["category"],
                "title": n["title"], "summary": n.get("summary"), "url": n.get("url"), "cause": n.get("cause"),
                "area": area, "lines": [str(l) for l in (n.get("affected_lines") or n.get("lines") or [])],
                "cells8": {h3.cell_to_parent(c, 8) for c in c11},
                "cells10": {h3.cell_to_parent(c, 10) for c in c11}}


def list_scenarios(data):
    out, seen = [], set()
    for d in data.scenario_dirs:
        for p in sorted(d.glob("*.yaml")):
            c = yaml.safe_load(open(p, encoding="utf-8"))
            if c["id"] not in seen:
                seen.add(c["id"])
                out.append({"id": c["id"], "title": c.get("title", c["id"]),
                            "recommended_users": c.get("recommended_users", 20000)})
    return out

import collections
import json
from pathlib import Path

import h3
import pyproj
from shapely.geometry import Point, shape
from shapely.ops import transform

_TO_M = pyproj.Transformer.from_crs(4326, 2180, always_xy=True).transform


class LineIndex:
    def __init__(self, data):
        self.stops = {}                                  
        for f in data.json("transit_stops.geojson")["features"]:
            p = f["properties"]
            lng, lat = f["geometry"]["coordinates"]
            c11 = h3.latlng_to_cell(lat, lng, 11)
            self.stops[p["stop_id"]] = {"id": p["stop_id"], "name": p["name"], "lat": lat, "lng": lng,
                                        "lines": p["lines"], "mode": p["mode"], "cell11": c11,
                                        "cell8": h3.cell_to_parent(c11, 8)}
        self.line_mode, self.line_color, shapes = {}, {}, {}
        for fn, mode in (("tram_lines.geojson", "tram"), ("bus_lines.geojson", "bus")):
            for f in data.json(fn)["features"]:
                line = f["properties"]["line"]
                self.line_mode[line] = mode
                self.line_color[line] = f["properties"]["color"] if mode == "tram" else "#5c6b7a"
                if str(f["properties"].get("direction")) in ("0", "") or line not in shapes:
                    shapes[line] = transform(_TO_M, shape(f["geometry"]))
        metric = {sid: transform(_TO_M, Point(s["lng"], s["lat"])) for sid, s in self.stops.items()}
        serving = collections.defaultdict(list)
        for s in self.stops.values():
            for line in s["lines"]:
                serving[line].append(s["id"])
        self.line_stops = collections.defaultdict(list)    
        for line, geom in shapes.items():
            self.line_stops[line] = sorted(serving[line], key=lambda sid: geom.project(metric[sid]))
        self.by_cell8 = collections.defaultdict(list)       
        for s in self.stops.values():
            self.by_cell8[s["cell8"]].append(s["id"])
        self.by_name = collections.defaultdict(list)
        for s in self.stops.values():
            self.by_name[s["name"]].append(s["id"])
        routes = Path(__file__).resolve().parent.parent / "data" / "transit_routes.json"
        self.routes = json.load(open(routes, encoding="utf-8"))["routes"] if routes.exists() else {}

    def stops_near(self, cell8):
        return [sid for c in h3.grid_disk(cell8, 1) for sid in self.by_cell8.get(c, ())]

    def stops_for(self, line, names=None):
        ids = self.line_stops.get(line, [])
        return [sid for sid in ids if names is None or self.stops[sid]["name"] in names]

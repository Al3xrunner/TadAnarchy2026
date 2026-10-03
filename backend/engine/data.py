import json
from collections import defaultdict
from pathlib import Path

import h3

from .models import VULNERABLE


class DataPack:


    def __init__(self, root, extra_scenarios=None):
        self.root = Path(root)
        self.scenario_dirs = [self.root / "scenarios"] + ([Path(extra_scenarios)] if extra_scenarios else [])
        self.cells8 = self.json("cells_res8.json")["cells"]      
        self.pop11 = self.json("cells_res11.json")["cells"]      
        self.look10 = self.json("lookup_res10.json")["cells"]    
        self.district_names = {f["id"]: f["properties"]["name"] for f in self.json("districts.geojson")["features"]}
        self.facilities10 = defaultdict(list)                    
        for f in self.json("facilities.geojson")["features"]:
            p = f["properties"]
            if p["type"] in VULNERABLE:
                self.facilities10[h3.cell_to_parent(p["h3_11"], 10)].append({"name": p["name"], "type": p["type"]})
        self._cache = {}

    def json(self, rel):
        with open(self.root / rel, encoding="utf-8") as f:
            return json.load(f)

    def feature(self, ref):
        """ref = {"file": "scenarios/areas/x.geojson", "feature": "zone"} -> GeoJSON feature"""
        if ref["file"] not in self._cache:
            self._cache[ref["file"]] = self.json(ref["file"])
        return next(f for f in self._cache[ref["file"]]["features"] if f.get("id") == ref["feature"])

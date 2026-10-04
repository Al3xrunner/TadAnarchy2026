import math
import time
from dataclasses import asdict

import h3

from .clock import SimClock
from .data import DataPack
from .detection import Detector
from .ingest import Ingest
from .line_detection import LineDetector
from .lines import LineIndex
from .models import CATEGORIES
from .scenario import Scenario, list_scenarios
from .simulator import Simulator
from .store import ReportStore

NOTICE_PUBLIC = ("id", "kind", "source", "cat", "title", "summary", "url", "area", "lines")


class Engine:

    def __init__(self, data_dir, extra_scenarios=None):
        self.data = DataPack(data_dir, extra_scenarios)
        self.store = ReportStore()
        self.ingest = Ingest(self.store, self.data)
        self.detector = Detector(self.data)
        self.lines = LineIndex(self.data)
        self.line_detector = LineDetector(self.lines)
        self.clock = SimClock()
        self.scenario = self.sim = None
        self.notices = {}
        self.run = {}
        self.version = 0
        self._db_rows = []

    def handle(self, command, d):
        if command == "report":
            stop = self.lines.stops.get(d.get("stop_id"))
            lat, lng = (stop["lat"], stop["lng"]) if stop else (d["lat"], d["lng"])   
            res = self.ingest(d["device_id"], d["category"], d["kind"], self.clock.t, lat=lat, lng=lng,
                              source="human", text=d.get("text"), line=d.get("line"), stop_id=d.get("stop_id"))
            r = res["report"]
            if r and r.category == "transit":
                nearby = self.line_detector.devices_on(r.line, self.store.reports, self.clock.t)
            else:
                nearby = self.devices_near(r.cell8, r.category) if r else 0
            return {"accepted": res["accepted"], "reason": res["reason"], "nearby_devices": nearby,
                    "cell8": r.cell8 if r else None}
        if command == "speed":
            self.clock.speed = max(0.0, float(d["speed"]))
            return {"ok": True, "speed": self.clock.speed}
        if command == "scenarios":
            return list_scenarios(self.data)
        if command == "load":
            return self.load(d["scenario"], int(d.get("users", 20000)), int(d.get("seed", 42)))
        if command == "add_notice":
            self.notices[d["id"]] = {**d, "added_t": self.clock.t}
            return {"ok": True}
        raise ValueError(f"unknown command {command}")

    def devices_near(self, cell8, category):
        win = CATEGORIES[category][0]
        now = self.clock.t
        return len({r.device_id for r in self.store.reports
                    if r.cell8 == cell8 and r.category == category and r.kind == "problem" and r.t >= now - win})

    def load(self, scenario_id, users, seed):
        t0 = time.time()
        self.scenario = Scenario(self.data, scenario_id)
        self.clock = SimClock(self.scenario.start_clock, self.clock.speed)
        self.store.clear()
        self.ingest.reset()
        self.detector.reset()
        self.line_detector.reset()
        self.notices.clear()
        self.sim = Simulator(self.data, self.scenario, users, seed, self.lines)
        self.run = {"id": int(time.time() * 1000), "scenario": scenario_id, "title": self.scenario.title,
                    "users": users, "seed": seed}
        self._db_rows.append(("run", dict(self.run)))
        self.clock.t = -3600.0                      
        while self.clock.t < 0:
            self._advance(60.0)
        self.store.new.clear()                      
        return {"ok": True, "run": self.run, "load_s": round(time.time() - t0, 2)}

    def step(self, real_dt):
        if self.sim is None or self.clock.speed == 0:
            return
        self._advance(real_dt * self.clock.speed)

    def _advance(self, dt):
        t0, t1 = self.clock.t, self.clock.t + dt
        self.clock.t = t1
        for r in self.sim.reports_between(t0, t1):
            self.ingest(r.device_id, r.category, r.kind, r.t, cell11=r.cell11, source="sim", line=r.line, stop_id=r.stop_id)
        for ev in self.scenario.events_between(t0, t1):
            if ev["type"] == "notice_add":
                n = self.scenario.load_notice(ev["file"])
                self.notices[n["id"]] = {**n, "added_t": t1}
            elif ev["type"] == "notice_remove":
                self.notices.pop(ev["id"], None)
        for n in self.sim.notices_between(t0, t1):
            self.notices[n["id"]] = {**n, "added_t": t1}
        for nid in [i for i, n in self.notices.items() if n.get("end_t", math.inf) < t1]:
            del self.notices[nid]
        self.store.expire(t1)
        self.detector.run(self.store.reports, t1, self.notices, self.scenario.truth)
        self.line_detector.run(self.store.reports, t1, self.notices, self.scenario.line_truth, self.detector.incidents)

    def snapshot(self):
        self.version += 1
        det = self.detector
        incidents = sorted(det.incidents.values(), key=lambda i: (-i["level"], -i["devices"]))
        return {
            "v": self.version, "sim_clock": self.clock.label(), "sim_t": round(self.clock.t, 1),
            "speed": self.clock.speed, "run": self.run,
            "cells": [{"h3": c, "cat": cat, "level": l, "devices": n, "fine": f}
                      for (c, cat), (l, n, f) in det.levels.items()],
            "incidents": [{**i, "first_clock": self.clock.label(i["first_t"])} for i in incidents],
            "line_incidents": self.line_detector.public(self.clock),
            "notices": [{k: n.get(k) for k in NOTICE_PUBLIC} for n in self.notices.values()],
            "metrics": {"reports_10min": det.reports_10min, "rejected": self.ingest.rejected,
                        "false_alarms": len(det.false_alarms) + len(self.line_detector.false_alarms),
                        "active_reports": len(self.store.reports),
                        "detect": {**det.detect, **self.line_detector.detect}},
        }

    def drain_db_rows(self):
        run_id = self.run.get("id")
        rows = self._db_rows + [("report", {**asdict(r), "run_id": run_id}) for r in self.store.new]
        rows += [("incident", {**i, "run_id": run_id}) for i in self.detector.changed_incidents()]
        rows += [("incident", {**i, "run_id": run_id}) for i in self.line_detector.changed()]
        self._db_rows, self.store.new = [], []
        return rows

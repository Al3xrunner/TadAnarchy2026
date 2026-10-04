import collections
import heapq
import math
from collections import namedtuple

import h3
import numpy as np

from .line_sim import LineSim

SimReport = namedtuple("SimReport", "t device_id category kind cell11 line stop_id", defaults=(None, None))
HOURLY = [.2, .15, .1, .1, .15, .4, .9, 1.6, 1.8, 1.4, 1.1, 1, 1.1, 1, 1, 1.2, 1.4, 1.6, 1.8, 1.8, 1.6, 1.2, .8, .4]
MIX = {"heating": .20, "water": .20, "power": .10, "transit": .25, "flood": .05, "danger": .02, "other": .18}
KRAKOW_POP = 809_168
NOTICE_TITLES = {"water": "Awaria sieci wodociągowej", "power": "Awaria sieci energetycznej",
                 "heating": "Awaria sieci ciepłowniczej", "flood": "Podtopienia"}


class Simulator:
    def __init__(self, data, scenario, users, seed, lines=None):
        self.rng = np.random.default_rng(seed)
        self.scenario, self.users = scenario, users
        h, m = map(int, scenario.start_clock.split(":"))
        self.start_s = h * 3600 + m * 60
        self.cells = list(data.pop11)
        w = np.array([data.pop11[c] for c in self.cells], dtype=float)
        self.cell_p = w / w.sum()
        self.home = [self.cells[i] for i in self.rng.choice(len(self.cells), size=users, p=self.cell_p)]
        self.by_home = collections.defaultdict(list)           
        for d, c in enumerate(self.home):
            self.by_home[c].append(d)
        act = self.rng.choice([0.3, 1.0, 4.0], size=users, p=[0.7, 0.25, 0.05])
        self.activity = act / act.sum()
        self.cats = list(MIX)
        self.cat_p = np.array(list(MIX.values())) / sum(MIX.values())
        self.look10, self.pop11 = data.look10, data.pop11
        self.heap, self.seq, self.started = [], 0, set()
        self.pending_notices, self.n_random = [], 0
        self.SimReport = SimReport
        self.home8 = [h3.cell_to_parent(c, 8) for c in self.home]
        self.line_sim = LineSim(self, lines) if lines else None      

    def reports_between(self, t0, t1):
        lam = self.users * self.scenario.bg_rate * HOURLY[int(((self.start_s + t0) / 3600) % 24)] * (t1 - t0) / 86400
        n = int(self.rng.poisson(lam))
        if n:
            devs = self.rng.choice(self.users, size=n, p=self.activity)
            cats = self.rng.choice(len(self.cats), size=n, p=self.cat_p)
            for d, c in zip(devs, cats):
                t = float(self.rng.uniform(t0, t1))
                if self.cats[c] == "transit" and self.line_sim:
                    yield self.line_sim.background(t, int(d))      
                else:
                    yield SimReport(t, f"sim-{d}", self.cats[c], "problem", self.home[d])
        self._spawn_random(t0, t1)
        for inc in self.scenario.incidents:
            if inc["id"] not in self.started and inc["start_t"] < t1:
                self.started.add(inc["id"])
                self._schedule(inc)
        while self.heap and self.heap[0][0] < t1:
            yield heapq.heappop(self.heap)[2]

    def notices_between(self, t0, t1):
        due = [n for at, n in self.pending_notices if at < t1]
        self.pending_notices = [(at, n) for at, n in self.pending_notices if at >= t1]
        return due

    def _push(self, rep):
        heapq.heappush(self.heap, (rep.t, self.seq, rep))     
        self.seq += 1

    def _schedule(self, inc):
        delay = inc.get("delay", {})
        med, sigma = delay.get("median_min", 10), delay.get("sigma", 0.6)
        wrong = inc.get("wrong_category")

        def when(start):
            return start + float(self.rng.lognormal(math.log(med), sigma)) * 60

        def category():
            return wrong["category"] if wrong and self.rng.random() < wrong["prob"] else inc["category"]

        if inc["mode"] == "line":
            if self.line_sim:
                self.line_sim.schedule(inc)
        elif inc["mode"] == "residents":
            for c in inc["cells11"]:
                for d in self.by_home.get(c, ()):
                    if self.rng.random() < inc["p_report"]:
                        t = when(inc["start_t"])
                        if t < inc["end_t"]:
                            self._push(SimReport(t, f"sim-{d}", category(), "problem", c))
        elif inc["mode"] == "passersby":
            hours = (inc["end_t"] - inc["start_t"]) / 3600
            n = min(self.users, int(self.rng.poisson(inc["flow_per_hour"] * hours * self.users / KRAKOW_POP)))
            for d in self.rng.choice(self.users, size=n, replace=False):
                if self.rng.random() < inc["p_report"]:
                    lng, lat = inc["points"][int(self.rng.integers(len(inc["points"])))]
                    t = when(float(self.rng.uniform(inc["start_t"], inc["end_t"])))
                    self._push(SimReport(t, f"sim-{d}", category(), "problem", h3.latlng_to_cell(lat, lng, 11)))
        elif inc["mode"] == "spam":
            for k in range(inc["devices"]):
                for _ in range(inc["reports_per_device"]):
                    t = inc["start_t"] + float(self.rng.uniform(0, inc.get("duration_min", 5) * 60))
                    self._push(SimReport(t, f"troll-{k}", inc["category"], "problem", inc["point_cell11"]))

    def _spawn_random(self, t0, t1):
        if self.line_sim:
            self.line_sim.spawn_random(t0, t1)
        for cat, cfg in self.scenario.random.items():
            for _ in range(int(self.rng.poisson(cfg["per_day"] * (t1 - t0) / 86400))):
                start = float(self.rng.uniform(t0, t1))
                center = self.cells[int(self.rng.choice(len(self.cells), p=self.cell_p))]
                rings = int(self.rng.integers(cfg["rings"][0], cfg["rings"][1] + 1))
                cells10 = set(h3.grid_disk(h3.cell_to_parent(center, 10), rings))
                cells11 = {c for c10 in cells10 for c in h3.cell_to_children(c10, 11) if c in self.pop11}
                self.n_random += 1
                inc = {"id": f"rnd-{cat}-{self.n_random}", "category": cat, "mode": "residents",
                       "cells11": cells11, "start_t": start,
                       "end_t": start + float(self.rng.uniform(*cfg["hours"])) * 3600,
                       "p_report": cfg["p_report"], "delay": cfg["delay"]}
                self.scenario.incidents.append(inc)            
                self.scenario.truth.append({"id": inc["id"], "cat": cat, "start_t": start,
                                            "cells8": {h3.cell_to_parent(c, 8) for c in cells10}})
                n = cfg.get("notice")
                if n and self.rng.random() < n["prob"]:
                    at = start + float(self.rng.uniform(*n["after_min"])) * 60
                    self.pending_notices.append((at, self._make_notice(inc, cells10, n["source"])))

    def _make_notice(self, inc, cells10, source):
        streets = collections.Counter(s for c in cells10 for s in self.look10.get(c, {}).get("streets", []))
        where = ", ".join(s for s, _ in streets.most_common(2)) or "Kraków"
        title = f"{NOTICE_TITLES.get(inc['category'], 'Awaria')} – {where}"
        return {"id": f"notice-{inc['id']}", "kind": "official", "source": source, "cat": inc["category"],
                "title": title, "summary": title, "url": None, "cause": None, "end_t": inc["end_t"],
                "area": h3.cells_to_geo(list(cells10)),
                "cells8": {h3.cell_to_parent(c, 8) for c in cells10}, "cells10": set(cells10)}

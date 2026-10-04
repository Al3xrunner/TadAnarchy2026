import math

KRAKOW_POP = 809_168


class LineSim:
    def __init__(self, sim, lines):
        self.sim, self.lines, self.rng = sim, lines, sim.rng
        self.all_lines = [l for l, s in lines.line_stops.items() if len(s) >= 4]
        w = [len(lines.line_stops[l]) for l in self.all_lines]           # longer lines carry more people
        self.line_p = [x / sum(w) for x in w]
        self.n_random = 0

    def _report(self, t, device, stop_id, line):
        s = self.lines.stops[stop_id]
        return self.sim.SimReport(t, device, "transit", "problem", s["cell11"], line, stop_id)

    def background(self, t, d):
        near = self.lines.stops_near(self.sim.home8[d]) or list(self.lines.stops)
        sid = near[int(self.rng.integers(len(near)))]
        lines = self.lines.stops[sid]["lines"]
        return self._report(t, f"sim-{d}", sid, lines[int(self.rng.integers(len(lines)))])

    def schedule(self, inc):
        delay = inc.get("delay", {})
        med, sigma = delay.get("median_min", 6), delay.get("sigma", 0.6)
        hours = (inc["end_t"] - inc["start_t"]) / 3600
        for line in inc["lines"]:
            stops = inc.get("stop_ids") or self.lines.stops_for(line, set(inc["stops"]) if inc.get("stops") else None)
            stops = [s for s in stops if line in self.lines.stops[s]["lines"]]
            if not stops:
                continue
            riders = int(self.rng.poisson(inc.get("riders_per_hour", 600) * hours * self.sim.users / KRAKOW_POP))
            for d in self.rng.choice(self.sim.users, size=min(riders, self.sim.users), replace=False):
                if self.rng.random() < inc["p_report"]:
                    arrive = float(self.rng.uniform(inc["start_t"], inc["end_t"]))
                    t = arrive + float(self.rng.lognormal(math.log(med), sigma)) * 60
                    if t < inc["end_t"]:
                        self.sim._push(self._report(t, f"sim-{d}", stops[int(self.rng.integers(len(stops)))], line))

    def spawn_random(self, t0, t1):
        cfg = self.sim.scenario.random_lines
        if not cfg:
            return
        for _ in range(int(self.rng.poisson(cfg["per_day"] * (t1 - t0) / 86400))):
            start = float(self.rng.uniform(t0, t1))
            line = self.all_lines[int(self.rng.choice(len(self.all_lines), p=self.line_p))]
            ids = self.lines.line_stops[line]
            span = int(self.rng.integers(cfg["stops_span"][0], cfg["stops_span"][1] + 1))
            first = int(self.rng.integers(0, max(1, len(ids) - span)))
            self.n_random += 1
            inc = {"id": f"rnd-line-{line}-{self.n_random}", "category": "transit", "mode": "line", "lines": [line],
                   "stop_ids": ids[first:first + span], "start_t": start,
                   "end_t": start + float(self.rng.uniform(*cfg["hours"])) * 3600,
                   "riders_per_hour": float(self.rng.uniform(*cfg["riders_per_hour"])),
                   "p_report": cfg["p_report"], "delay": cfg["delay"]}
            self.sim.scenario.incidents.append(inc)              # scheduled like scripted incidents
            self.sim.scenario.line_truth.append({"id": inc["id"], "lines": [line], "start_t": start})
            n = cfg.get("notice")
            if n and self.rng.random() < n["prob"]:
                at = start + float(self.rng.uniform(*n["after_min"])) * 60
                where = self.lines.stops[ids[first]]["name"]
                self.sim.pending_notices.append((at, {
                    "id": f"notice-{inc['id']}", "kind": "official", "source": n["source"], "cat": "transit",
                    "title": f"Utrudnienia na linii {line} (rejon {where})", "summary": None, "url": None,
                    "cause": None, "end_t": inc["end_t"], "lines": [line], "area": None,
                    "cells8": {self.lines.stops[s]["cell8"] for s in inc["stop_ids"]}, "cells10": set()}))

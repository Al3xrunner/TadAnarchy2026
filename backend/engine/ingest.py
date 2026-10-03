import uuid
from collections import defaultdict, deque

import h3

from .models import CATEGORIES, Report

RATE_LIMIT = 5  


class Ingest:
  

    def __init__(self, store, data):
        self.store, self.data = store, data
        self.reset()

    def reset(self):
        self.recent = defaultdict(deque)   
        self.last = {}                     
        self.rejected = 0

    def __call__(self, device_id, category, kind, t, *, lat=None, lng=None, cell11=None, source="sim", text=None):
        if category not in CATEGORIES:
            return self._reject("bad_category")
        if cell11 is None:
            cell11 = h3.latlng_to_cell(lat, lng, 11)          
        cell8 = h3.cell_to_parent(cell11, 8)
        if cell8 not in self.data.cells8:
            return self._reject("outside_city")
        q = self.recent[device_id]
        while q and q[0] < t - 3600:
            q.popleft()
        if kind == "problem" and len(q) >= RATE_LIMIT:
            return self._reject("rate_limited")
        key = (device_id, category, cell8, kind)
        if key in self.last and t - self.last[key] < CATEGORIES[category][0]:
            return self._reject("duplicate")
        self.last[key] = t
        if kind == "problem":
            q.append(t)
        r = Report(uuid.uuid4().hex[:12], device_id, category, kind, t, cell11,
                   h3.cell_to_parent(cell11, 10), cell8, source, text)
        self.store.add(r)
        return {"accepted": True, "reason": None, "report": r}

    def _reject(self, reason):
        self.rejected += 1
        return {"accepted": False, "reason": reason, "report": None}

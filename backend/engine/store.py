from collections import deque

from .models import MAX_WINDOW


class ReportStore:
    def __init__(self):
        self.reports = deque()   
        self.new = []            

    def add(self, r):
        self.reports.append(r)
        self.new.append(r)

    def expire(self, now):
        while self.reports and self.reports[0].t < now - MAX_WINDOW:
            self.reports.popleft()

    def clear(self):
        self.reports.clear()
        self.new.clear()

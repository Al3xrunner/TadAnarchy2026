import queue
import threading
import time
import traceback

from sqlalchemy import insert

from .models import IncidentRow, ReportRow, Run
from .session import SessionLocal

REPORT_COLS = ("id", "run_id", "device_id", "category", "kind", "t", "cell11", "cell10", "cell8", "source", "text")


class DBWriter:


    def __init__(self, flush_s=1.0):
        self.queue = queue.Queue()
        self.flush_s = flush_s
        self.written = {"run": 0, "report": 0, "incident": 0}
        self.thread = threading.Thread(target=self._loop, name="db-writer", daemon=True)

    def start(self):
        self.thread.start()

    def _loop(self):
        while True:
            time.sleep(self.flush_s)
            batch = []
            while True:
                try:
                    batch.append(self.queue.get_nowait())
                except queue.Empty:
                    break
            if batch:
                try:
                    self._write(batch)
                except Exception:
                    traceback.print_exc()        

    def _write(self, batch):
        with SessionLocal() as s, s.begin():
            for kind, row in batch:
                if kind == "run":
                    s.merge(Run(id=row["id"], scenario=row["scenario"], title=row.get("title", ""),
                                users=row["users"], seed=row["seed"]))
                    self.written["run"] += 1
            s.flush()
            reports = [{c: r[c] for c in REPORT_COLS} for k, r in batch if k == "report" and r["run_id"]]
            if reports:
                s.execute(insert(ReportRow), reports)
                self.written["report"] += len(reports)
            latest = {}
            for kind, i in batch:                  
                if kind == "incident" and i["run_id"]:
                    latest[(i["run_id"], i["id"])] = i
            for (run_id, iid), i in latest.items():
                old = s.get(IncidentRow, (run_id, iid))
                s.merge(IncidentRow(
                    run_id=run_id, id=iid, category=i["cat"],
                    max_level=max(i["level"], old.max_level if old else 0),
                    status=i["status"], confidence=i["confidence"], district=i["district"],
                    devices=i["devices"], first_t=i["first_t"],
                    data={k: v for k, v in i.items() if k != "run_id"}))
                self.written["incident"] += 1

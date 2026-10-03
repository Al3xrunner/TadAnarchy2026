import json
import queue
import threading
import time
import traceback
from concurrent.futures import Future


class EngineRunner:


    def __init__(self, engine, db_queue=None, tick_s=1.0):
        self.engine, self.db_queue, self.tick_s = engine, db_queue, tick_s
        self.inbox = queue.Queue()
        self._cond = threading.Condition()
        self._version, self._payload = 0, "{}"
        self.last_tick_ms = 0.0
        self._thread = threading.Thread(target=self._loop, name="engine", daemon=True)

    def start(self):
        self._publish()
        self._thread.start()


    def call(self, command, data, timeout=3.0):
        fut = Future()
        self.inbox.put((command, data, fut))
        return fut.result(timeout=timeout)          # TimeoutError if the engine is stuck

    def wait_for_snapshot(self, last_version, timeout=15.0):
        with self._cond:
            self._cond.wait_for(lambda: self._version != last_version, timeout=timeout)
            return self._version, self._payload


    def _loop(self):
        next_tick = time.monotonic()
        while True:
            self._drain_inbox()
            t0 = time.monotonic()
            try:
                self.engine.step(self.tick_s)
            except Exception:
                traceback.print_exc()
            self.last_tick_ms = (time.monotonic() - t0) * 1000
            if self.last_tick_ms > 300:
                print(f"WARNING slow tick {self.last_tick_ms:.0f} ms", flush=True)
            self._publish()
            next_tick += self.tick_s
            time.sleep(max(0.0, next_tick - time.monotonic()))

    def _publish(self):
        try:
            snap = self.engine.snapshot()
            snap["metrics"]["tick_ms"] = round(self.last_tick_ms, 1)
            payload = json.dumps(snap, ensure_ascii=False, separators=(",", ":"))
        except Exception:
            traceback.print_exc()
            return
        with self._cond:
            self._version += 1
            self._payload = payload
            self._cond.notify_all()
        if self.db_queue is not None:
            for row in self.engine.drain_db_rows():
                self.db_queue.put(row)

    def _drain_inbox(self):
        while True:
            try:
                command, data, fut = self.inbox.get_nowait()
            except queue.Empty:
                return
            try:
                result = self.engine.handle(command, data)
                if command in ("report", "load", "add_notice"):
                    self.engine.detector.run(self.engine.store.reports, self.engine.clock.t,
                                             self.engine.notices, self.engine.scenario.truth)
                fut.set_result(result)
            except Exception as e:
                traceback.print_exc()
                fut.set_exception(e)

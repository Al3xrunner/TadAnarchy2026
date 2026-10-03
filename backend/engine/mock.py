import json
import time


class MockRunner:
    

    def __init__(self, path):
        self.snapshot = json.load(open(path, encoding="utf-8"))
        self.version = 0
        self.last_tick_ms = 0

    def start(self):
        pass

    def call(self, command, data, timeout=3.0):
        if command == "report":
            return {"accepted": True, "reason": None, "nearby_devices": 3}
        if command == "scenarios":
            return [{"id": "heating_azory", "title": "Mock", "recommended_users": 20000}]
        return {"ok": True}

    def wait_for_snapshot(self, last_version, timeout=15.0):
        if last_version >= 0:
            time.sleep(1)
        self.version += 1
        self.snapshot["v"] = self.version
        return self.version, json.dumps(self.snapshot, ensure_ascii=False)

import json

from config import Config
from engine.engine import Engine

e = Engine(Config.DATA_DIR, Config.EXTRA_SCENARIOS)
e.handle("load", {"scenario": "heating_azory", "users": 20000, "seed": 67})
for _ in range(60):
    e._advance(60.0)
json.dump(e.snapshot(), open("mock_snapshot.json", "w", encoding="utf-8"), ensure_ascii=False)
print("wrote mock_snapshot.json")

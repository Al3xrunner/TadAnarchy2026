import json

from config import Config
from engine.engine import Engine

e = Engine(Config.DATA_DIR, Config.EXTRA_SCENARIOS)
e.handle("load", {"scenario": "heating_azory", "users": 20000, "seed": 42})
for _ in range(45):
    e._advance(60)
json.dump(e.snapshot(), open("mock_snapshot.json", "w", encoding="utf-8"), ensure_ascii=False)
print("wrote mock_snapshot.json")

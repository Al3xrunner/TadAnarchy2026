import os
import threading
import time
import traceback
import urllib.request
from pathlib import Path

from google.transit import gtfs_realtime_pb2

BASE = "https://gtfs.ztp.krakow.pl/"
FEEDS = {"VehiclePositions_T": "tram", "VehiclePositions_A": "bus", "ServiceAlerts_T": "tram", "ServiceAlerts_A": "bus"}


class TransitFeed:
    def __init__(self, lines, every_s=15, cache_dir=None, offline_dir=None):
        self.lines, self.every_s = lines, every_s
        self.cache = Path(cache_dir or Path(__file__).resolve().parent.parent / "transit_cache")
        self.cache.mkdir(exist_ok=True)
        self.offline = Path(offline_dir) if offline_dir else None     
        self.state = {"status": "starting", "updated_at": None, "vehicles": [], "alerts": [], "error": None}
        self._thread = threading.Thread(target=self._loop, name="transit", daemon=True)

    def start(self):
        self._thread.start()

    def _get(self, name):
        if self.offline:
            return (self.offline / f"{name}.pb").read_bytes(), "offline"
        try:
            req = urllib.request.Request(BASE + f"{name}.pb", headers={"User-Agent": "krakow-live-demo/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                body = r.read()
            (self.cache / f"{name}.pb").write_bytes(body)
            return body, "live"
        except Exception:
            p = self.cache / f"{name}.pb"
            if p.exists():
                return p.read_bytes(), "cache"
            raise

    def _line(self, route_id):
        r = self.lines.routes.get(route_id)
        return r["line"] if r else route_id

    def _loop(self):
        while True:
            try:
                vehicles, alerts, sources = [], [], set()
                for name, mode in FEEDS.items():
                    body, src = self._get(name)
                    sources.add(src)
                    feed = gtfs_realtime_pb2.FeedMessage()
                    feed.ParseFromString(body)
                    for e in feed.entity:
                        if e.HasField("vehicle") and e.vehicle.HasField("position"):
                            v = e.vehicle
                            vehicles.append({"id": v.vehicle.id or e.id, "mode": mode, "line": self._line(v.trip.route_id),
                                             "lat": round(v.position.latitude, 6), "lng": round(v.position.longitude, 6),
                                             "bearing": round(v.position.bearing) if v.position.HasField("bearing") else None,
                                             "ts": v.timestamp or None})
                        if e.HasField("alert"):
                            a = e.alert
                            text = lambda ts: ts.translation[0].text if ts.translation else ""
                            alerts.append({"id": e.id, "mode": mode, "header": text(a.header_text),
                                           "description": text(a.description_text),
                                           "lines": sorted({self._line(i.route_id) for i in a.informed_entity if i.route_id}),
                                           "stops": sorted({self.lines.stops[i.stop_id]["name"] for i in a.informed_entity
                                                            if i.stop_id in self.lines.stops})})
                status = "live" if sources == {"live"} else ("offline" if "offline" in sources else "cache")
                self.state = {"status": status, "updated_at": time.time(), "vehicles": vehicles, "alerts": alerts, "error": None}
            except Exception as ex:                              
                self.state = {**self.state, "status": "error", "error": str(ex)}
                if os.environ.get("TRANSIT_DEBUG"):
                    traceback.print_exc()
            time.sleep(self.every_s)

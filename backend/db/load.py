import csv
import json
import re
import unicodedata

import click
import h3
from flask import current_app
from sqlalchemy import delete, insert

from .models import Address, Facility
from .session import SessionLocal


def fold(s):
    s = unicodedata.normalize("NFKD", (s or "").replace("ł", "l").replace("Ł", "L"))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    s = re.sub(r"\b(ul|al|os|pl)\.\s*", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def load_all(root):
    addresses = []
    with open(f"{root}/addresses.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            lat, lng = float(r["lat"]), float(r["lon"])
            addresses.append({"street": r["street"], "place": r["place"], "housenumber": r["housenumber"],
                              "key": fold(f"{r['street'] or r['place']} {r['housenumber']}"),
                              "lat": lat, "lng": lng, "cell10": h3.latlng_to_cell(lat, lng, 10)})
    facilities = []
    with open(f"{root}/facilities.geojson", encoding="utf-8") as f:
        for feat in json.load(f)["features"]:
            p, (lng, lat) = feat["properties"], feat["geometry"]["coordinates"]
            facilities.append({"name": p["name"], "type": p["type"], "address": p.get("address") or "",
                               "district_id": p.get("district_id"), "cell8": p["h3_8"], "cell11": p["h3_11"],
                               "lat": lat, "lng": lng})
    with SessionLocal() as s, s.begin():
        s.execute(delete(Address))
        s.execute(delete(Facility))
        s.execute(insert(Address), addresses)
        s.execute(insert(Facility), facilities)
    return len(addresses), len(facilities)


def register_cli(app):
    @app.cli.command("load-data")
    def load_data():
        a, f = load_all(current_app.config["DATA_DIR"])
        click.echo(f"loaded {a} addresses, {f} facilities")

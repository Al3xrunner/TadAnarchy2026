from flask import Blueprint, jsonify, request
from sqlalchemy import select

from db.load import fold
from db.models import Address
from db.session import SessionLocal

bp = Blueprint("geo", __name__)


@bp.get("/api/geocode")
def geocode():
    q = fold(request.args.get("q", ""))
    if len(q) < 3:
        return jsonify([])
    words = q.split()
    stmt = select(Address)
    for w in words:
        stmt = stmt.where(Address.key.like(f"%{w}%"))
    with SessionLocal() as s:
        rows = s.scalars(stmt.limit(40)).all()
    number = next((w for w in words if w[0].isdigit()), None)
    rows.sort(key=lambda a: (fold(a.housenumber) != number, len(a.key)))
    return jsonify([{"label": f"{a.street or a.place} {a.housenumber}", "lat": a.lat, "lng": a.lng,
                     "cell10": a.cell10} for a in rows[:8]])

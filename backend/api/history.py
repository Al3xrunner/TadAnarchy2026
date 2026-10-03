from flask import Blueprint, jsonify, request
from sqlalchemy import func, select

from db.models import IncidentRow, ReportRow, Run
from db.session import SessionLocal

bp = Blueprint("history", __name__)


@bp.get("/api/history/runs")
def runs():
    with SessionLocal() as s:
        rows = s.scalars(select(Run).order_by(Run.started_at.desc()).limit(20)).all()
        counts = dict(s.execute(select(ReportRow.run_id, func.count()).group_by(ReportRow.run_id)).all())
    return jsonify([{"id": r.id, "scenario": r.scenario, "title": r.title, "users": r.users, "seed": r.seed,
                     "started_at": r.started_at.isoformat(), "reports": counts.get(r.id, 0)} for r in rows])


@bp.get("/api/history/incidents")
def incidents():
    run_id = int(request.args["run_id"])
    with SessionLocal() as s:
        rows = s.scalars(select(IncidentRow).where(IncidentRow.run_id == run_id)
                         .order_by(IncidentRow.max_level.desc(), IncidentRow.devices.desc())).all()
        by_cat = dict(s.execute(select(ReportRow.category, func.count()).where(ReportRow.run_id == run_id)
                                .group_by(ReportRow.category)).all())
    return jsonify({"incidents": [{"id": r.id, "category": r.category, "max_level": r.max_level, "status": r.status,
                                   "confidence": r.confidence, "district": r.district, "devices": r.devices,
                                   "first_t": r.first_t} for r in rows],
                    "reports_by_category": by_cat})

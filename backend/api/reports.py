from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("reports", __name__)
CATEGORIES = {"heating", "water", "power", "flood", "transit", "danger", "other"}
STATUS = {"rate_limited": 429, "duplicate": 409, "outside_city": 422}


@bp.post("/api/reports")
def post_report():
    d = request.get_json(silent=True) or {}
    try:
        r = {"device_id": str(d["device_id"])[:64], "category": d["category"], "kind": d.get("kind", "problem"),
             "lat": float(d["lat"]), "lng": float(d["lng"]), "text": (d.get("text") or "")[:280] or None}
    except (KeyError, TypeError, ValueError):
        return jsonify(accepted=False, reason="bad_request"), 400
    if r["category"] not in CATEGORIES or r["kind"] not in ("problem", "fine"):
        return jsonify(accepted=False, reason="bad_category"), 400
    try:
        result = current_app.extensions["runner"].call("report", r)
    except TimeoutError:
        return jsonify(accepted=False, reason="engine_busy"), 503
    return jsonify(result), (202 if result["accepted"] else STATUS.get(result["reason"], 400))

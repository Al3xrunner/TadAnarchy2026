from functools import wraps

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("director", __name__)


def require_token(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get("X-Director-Token") != current_app.config["DIRECTOR_TOKEN"]:
            return jsonify(error="forbidden"), 403
        return f(*args, **kwargs)
    return wrapper


@bp.get("/api/director/scenarios")
def scenarios():
    return jsonify(current_app.extensions["runner"].call("scenarios", {}))


@bp.post("/api/director/load")
@require_token
def load():
    return jsonify(current_app.extensions["runner"].call("load", request.get_json(force=True), timeout=60))


@bp.post("/api/director/speed")
@require_token
def speed():
    return jsonify(current_app.extensions["runner"].call("speed", request.get_json(force=True)))

from flask import Blueprint, current_app, jsonify

bp = Blueprint("transit", __name__)


@bp.get("/api/transit/live")
def live():
    feed = current_app.extensions.get("transit_feed")
    if feed is None:
        return jsonify(status="disabled", vehicles=[], alerts=[], updated_at=None, error="TRANSIT_LIVE=0")
    return jsonify(feed.state)

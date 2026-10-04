from datetime import datetime
import json
from threading import Lock

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("comments", __name__)
MAX_COMMENTS = 200
MAX_TEXT_LENGTH = 500
MAX_USER_LENGTH = 60


class CommentStore:
    def __init__(self):
        self._comments = []
        self._next_id = 1
        self._lock = Lock()

    def add(self, incident_id, district, user, text):
        with self._lock:
            comment = {
                "id": self._next_id,
                "incident_id": incident_id,
                "district": district,
                "user": user,
                "text": text,
                "timestamp": datetime.now().strftime("%H:%M"),
            }
            self._next_id += 1
            self._comments.append(comment)
            del self._comments[:-MAX_COMMENTS]
            return dict(comment)

    def recent(self):
        with self._lock:
            return [dict(comment) for comment in self._comments]


@bp.post("/api/comments")
def post_comment():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Expected a JSON object."), 400

    incident_id = data.get("incident_id")
    text = data.get("text")
    user = data.get("user")
    if not isinstance(incident_id, str) or not incident_id.strip():
        return jsonify(error="incident_id is required."), 400
    if not isinstance(text, str) or not text.strip():
        return jsonify(error="text is required."), 400
    text = text.strip()
    if len(text) > MAX_TEXT_LENGTH:
        return jsonify(error=f"text must be at most {MAX_TEXT_LENGTH} characters."), 400
    if not isinstance(user, str) or not user.strip():
        return jsonify(error="user is required."), 400
    user = user.strip()
    if len(user) > MAX_USER_LENGTH:
        return jsonify(error=f"user must be at most {MAX_USER_LENGTH} characters."), 400

    runner = current_app.extensions["runner"]
    _, payload = runner.wait_for_snapshot(-1, timeout=0)
    incidents = json.loads(payload).get("incidents", [])
    incident = next((item for item in incidents if item.get("id") == incident_id), None)
    if incident is None:
        return jsonify(error="Incident not found."), 404

    comment = current_app.extensions["comment_store"].add(
        incident_id, incident.get("district", ""), user, text
    )
    return jsonify(comment), 201

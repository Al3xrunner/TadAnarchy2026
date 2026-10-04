from datetime import datetime
import json
import os
from pathlib import Path
from threading import Lock

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("comments", __name__)
MAX_TEXT_LENGTH = 500
MAX_USER_LENGTH = 60


class CommentStore:
    def __init__(self, path):
        self._path = Path(path)
        self._lock = Lock()
        self._comments = self._load()
        self._next_id = max((comment["id"] for comment in self._comments), default=0) + 1

    def _load(self):
        if not self._path.exists():
            return []
        with self._path.open(encoding="utf-8") as comments_file:
            comments = json.load(comments_file)
        if not isinstance(comments, list) or any(
            not isinstance(comment, dict)
            or not isinstance(comment.get("id"), int)
            or not isinstance(comment.get("incident_id"), str)
            for comment in comments
        ):
            raise ValueError(f"Invalid comment data in {self._path}")
        return comments

    def _save(self, comments):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self._path.with_name(f"{self._path.name}.tmp")
        try:
            with temporary_path.open("w", encoding="utf-8") as comments_file:
                json.dump(comments, comments_file, ensure_ascii=False, indent=2)
                comments_file.write("\n")
            os.replace(temporary_path, self._path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

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
            comments = [*self._comments, comment]
            self._save(comments)
            self._comments = comments
            self._next_id += 1
            return dict(comment)

    def keep_active_incidents(self, incidents):
        active_ids = {
            incident["id"]
            for incident in incidents
            if incident.get("status") == "active" and incident.get("level", 0) > 0
        }
        with self._lock:
            comments = [
                comment for comment in self._comments
                if comment["incident_id"] in active_ids
            ]
            if len(comments) != len(self._comments):
                self._save(comments)
                self._comments = comments

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
    store = current_app.extensions["comment_store"]
    store.keep_active_incidents(incidents)
    incident = next((item for item in incidents if item.get("id") == incident_id), None)
    if incident is None or incident.get("status") != "active" or incident.get("level", 0) == 0:
        return jsonify(error="Incident is no longer active."), 404

    comment = store.add(incident_id, incident.get("district", ""), user, text)
    return jsonify(comment), 201

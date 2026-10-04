import json

from flask import Blueprint, Response, current_app

bp = Blueprint("stream", __name__)


@bp.get("/api/stream")
def stream():
    runner = current_app.extensions["runner"]   
    comment_store = current_app.extensions["comment_store"]

    def events():
        yield "retry: 2000\n\n"
        last = -1
        while True:
            version, payload = runner.wait_for_snapshot(last, timeout=15)
            if version == last:
                yield ": keep-alive\n\n"
                continue
            last = version
            snapshot = json.loads(payload)
            snapshot["recent_comments"] = comment_store.recent()
            payload = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
            yield f"data: {payload}\n\n" 
                   

    return Response(events(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@bp.get("/api/snapshot")
def snapshot():
    _, payload = current_app.extensions["runner"].wait_for_snapshot(-1, timeout=0)
    snapshot = json.loads(payload)
    snapshot["recent_comments"] = current_app.extensions["comment_store"].recent()
    return Response(json.dumps(snapshot, ensure_ascii=False), mimetype="application/json")

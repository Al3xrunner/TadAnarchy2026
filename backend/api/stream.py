from flask import Blueprint, Response, current_app

bp = Blueprint("stream", __name__)


@bp.get("/api/stream")
def stream():
    runner = current_app.extensions["runner"]   

    def events():
        yield "retry: 2000\n\n"
        last = -1
        while True:
            version, payload = runner.wait_for_snapshot(last, timeout=15)
            if version == last:
                yield ": keep-alive\n\n"
                continue
            last = version
            yield f"data: {payload}\n\n" 
                   

    return Response(events(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@bp.get("/api/snapshot")
def snapshot():
    _, payload = current_app.extensions["runner"].wait_for_snapshot(-1, timeout=0)
    return Response(payload, mimetype="application/json")

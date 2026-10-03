import os

from flask import Flask, send_from_directory

from config import Config


def create_app(start_engine=True):
    app = Flask(__name__)
    app.config.from_object(Config)

    from db.session import init_db
    from db.writer import DBWriter
    init_db(app.config["DB_URL"])
    writer = DBWriter()
    app.extensions["db_writer"] = writer

    if start_engine:
        writer.start()
        if app.config["MOCK"]:
            from engine.mock import MockRunner
            runner = MockRunner(os.path.join(os.path.dirname(__file__), "mock_snapshot.json"))
        else:
            from engine.engine import Engine
            from engine.runner import EngineRunner
            engine = Engine(app.config["DATA_DIR"], app.config["EXTRA_SCENARIOS"])
            engine.clock.speed = app.config["DEFAULT_SPEED"]
            engine.handle("load", {"scenario": app.config["DEFAULT_SCENARIO"], "users": app.config["DEFAULT_USERS"],
                                   "seed": 67})
            runner = EngineRunner(engine, db_queue=writer.queue)
        runner.start()
        app.extensions["runner"] = runner

    from api import director, geo, history, reports, stream
    for module in (reports, stream, director, geo, history):
        app.register_blueprint(module.bp)

    from db.load import register_cli
    register_cli(app)

    dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

    @app.get("/")
    @app.get("/app")
    @app.get("/dashboard")
    @app.get("/director")
    def spa():
        return send_from_directory(dist, "index.html")

    @app.get("/assets/<path:p>")
    def assets(p):
        return send_from_directory(os.path.join(dist, "assets"), p)

    @app.get("/data/<path:p>")
    def data(p):
        return send_from_directory(app.config["DATA_DIR"], p)

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), threaded=True,
                     debug=True, use_reloader=False)

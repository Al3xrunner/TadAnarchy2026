from app import create_app
from db.load import load_all

app = create_app(start_engine=False)
print("loaded %d addresses, %d facilities" % load_all(app.config["DATA_DIR"]))

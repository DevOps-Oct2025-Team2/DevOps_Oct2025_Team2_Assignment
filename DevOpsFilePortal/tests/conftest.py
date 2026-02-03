#Garence Wong Kar Kang 
import os
import sys
import importlib
import pathlib
import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1] 
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    db_dir = tmp_path / "db"
    upload_dir = tmp_path / "uploads"
    db_dir.mkdir()
    upload_dir.mkdir()

    monkeypatch.setenv("SQLITE_PATH", str(db_dir / "test.db"))
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")
    monkeypatch.setenv("SHOW_STARTUP_BANNER", "0")

    import app as app_module
    importlib.reload(app_module)

    app_module.app.config.update(TESTING=True)

    with app_module.app.test_client() as c:
        yield c


def login(client, username, password):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )

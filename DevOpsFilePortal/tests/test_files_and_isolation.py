import io
import os
from conftest import login

def create_user_as_admin(client, username, password):
    login(client, "admin", "admin123")
    client.post("/admin/create_user", data={"username": username, "password": password})
    client.get("/logout")

def upload_file(client, filename, content: bytes):
    data = {"file": (io.BytesIO(content), filename)}
    return client.post("/dashboard/upload", data=data, content_type="multipart/form-data")

def test_data_isolation_download_404(client):
    # Arrange: create user1 and user2
    create_user_as_admin(client, "user1", "pass1")
    create_user_as_admin(client, "user2", "pass2")

    # user1 uploads a file
    login(client, "user1", "pass1")
    upload_file(client, "secret.txt", b"TOP-SECRET")
    dash = client.get("/dashboard")
    assert b"secret.txt" in dash.data

    # Extract file_id from HTML (simple parse)
    # The table renders Download links like /dashboard/download/<id>
    html = dash.data.decode("utf-8")
    import re
    m = re.search(r"/dashboard/download/(\d+)", html)
    assert m, "Expected a download link in dashboard HTML"
    file_id = int(m.group(1))

    # user2 cannot download user1's file
    client.get("/logout")
    login(client, "user2", "pass2")
    res = client.get(f"/dashboard/download/{file_id}")
    assert res.status_code == 404

def test_data_isolation_delete_no_effect(client):
    create_user_as_admin(client, "user1", "pass1")
    create_user_as_admin(client, "user2", "pass2")

    login(client, "user1", "pass1")
    upload_file(client, "a.txt", b"aaa")
    dash = client.get("/dashboard")
    html = dash.data.decode("utf-8")

    import re
    m = re.search(r"/dashboard/delete/(\d+)", html)
    assert m
    file_id = int(m.group(1))

    client.get("/logout")
    login(client, "user2", "pass2")
    res = client.post(f"/dashboard/delete/{file_id}", follow_redirects=True)
    # Should not delete, and user2 should still see "No files uploaded yet."
    assert b"No files uploaded yet." in res.data

def test_upload_too_large_returns_413(client, monkeypatch):
    # Set small limit for test
    monkeypatch.setenv("MAX_CONTENT_LENGTH", "10")  # 10 bytes
    import importlib
    import app as app_module
    importlib.reload(app_module)
    app_module.app.config.update(TESTING=True)

    with app_module.app.test_client() as c:
        # Need a logged-in user
        app_module.init_db()
        app_module.ensure_seed_admin()
        c.post("/login", data={"username": "admin", "password": "admin123"})
        # Admin cannot upload; create normal user
        c.post("/admin/create_user", data={"username": "u", "password": "p"})
        c.get("/logout")
        c.post("/login", data={"username": "u", "password": "p"})

        data = {"file": (io.BytesIO(b"01234567890"), "big.txt")}  # 11 bytes
        res = c.post("/dashboard/upload", data=data, content_type="multipart/form-data")
        assert res.status_code == 413

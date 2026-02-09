from io import BytesIO
from conftest import login

def create_user_as_admin(client, username, password):
    login(client, "admin", "admin123")
    client.post("/admin/create_user", data={"username": username, "password": password}, follow_redirects=False)
    client.get("/logout", follow_redirects=False)

def upload_file(client, filename="a.txt", content=b"hello"):
    data = {"file": (BytesIO(content), filename)}
    return client.post("/dashboard/upload", data=data, content_type="multipart/form-data", follow_redirects=False)

def test_admin_cannot_use_user_dashboard(client):
    login(client, "admin", "admin123")
    res = client.get("/dashboard", follow_redirects=False)
    assert res.status_code in (302, 303)
    assert "/admin" in res.headers.get("Location", "")

def test_user_cannot_access_admin_dashboard(client):
    create_user_as_admin(client, "user1", "pass1")
    login(client, "user1", "pass1")
    res = client.get("/admin", follow_redirects=False)
    assert res.status_code in (302, 303)

def test_user_cannot_download_other_users_file(client):
    # Create 2 users
    create_user_as_admin(client, "user1", "pass1")
    create_user_as_admin(client, "user2", "pass2")

    # user1 uploads a file
    login(client, "user1", "pass1")
    up = upload_file(client, "secret.txt", b"topsecret")
    assert up.status_code in (302, 303)
    client.get("/logout", follow_redirects=False)

    # user2 tries to download user1's file (file_id will be 1 in fresh test DB)
    login(client, "user2", "pass2")
    res = client.get("/dashboard/download/1", follow_redirects=False)
    assert res.status_code == 404  # must not leak existence

def test_user_cannot_delete_other_users_file(client):
    create_user_as_admin(client, "user1", "pass1")
    create_user_as_admin(client, "user2", "pass2")

    login(client, "user1", "pass1")
    upload_file(client, "secret.txt", b"topsecret")
    client.get("/logout", follow_redirects=False)

    login(client, "user2", "pass2")
    res = client.post("/dashboard/delete/1", follow_redirects=False)
    # app redirects back to dashboard with "File not found."
    assert res.status_code in (302, 303)

def test_download_invalid_file_id(client):
    create_user_as_admin(client, "edgeuser", "edgepass")
    login(client, "edgeuser", "edgepass")

    res = client.get("/dashboard/download/9999", follow_redirects=False)

    assert res.status_code == 404 or res.status_code in (302, 303)
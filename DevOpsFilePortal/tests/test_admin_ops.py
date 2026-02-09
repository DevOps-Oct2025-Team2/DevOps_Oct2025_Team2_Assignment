from conftest import login
def test_admin_can_create_and_delete_user(client):
    from user_repo import get_user_by_username
    # 1. Login as Admin
    login(client, "admin", "admin123")

    # 2. Create a new user "testuser"
    res = client.post(
        "/admin/create_user",
        data={"username": "testuser", "password": "password"},
        follow_redirects=True
    )
    assert res.status_code == 200
    # The message might be HTML escaped (e.g. &#39;testuser&#39;)
    # Let's check for the key parts
    assert b"testuser" in res.data
    assert b"created." in res.data

    # 3. Verify user exists in DB and can login
    user = get_user_by_username("testuser")
    assert user is not None

    client.get("/logout", follow_redirects=True)
    res_login = login(client, "testuser", "password")
    assert res_login.status_code in (302, 303)
    assert "/dashboard" in res_login.headers.get("Location", "")
    
    # Logout "testuser"
    client.get("/logout", follow_redirects=True)

    # 4. Login as Admin again to delete
    login(client, "admin", "admin123")
    
    # 5. Delete "testuser"
    res_delete = client.post(f"/admin/delete_user/{user['id']}", follow_redirects=True)
    assert res_delete.status_code == 200
    assert b"User deleted." in res_delete.data

    # 6. Verify user is gone
    user_deleted = get_user_by_username("testuser")
    assert user_deleted is None

def test_admin_delete_nonexistent_user(client):
    login(client, "admin", "admin123")

    res = client.post("/admin/delete_user/9999", follow_redirects=True)

    # App should handle safely without crashing
    assert res.status_code == 200

def test_admin_cannot_create_duplicate_user(client):
    login(client, "admin", "admin123")

    client.post(
        "/admin/create_user",
        data={"username": "dupuser", "password": "pass"},
        follow_redirects=True
    )

    res = client.post(
        "/admin/create_user",
        data={"username": "dupuser", "password": "pass"},
        follow_redirects=True
    )

    assert b"exists" in res.data.lower() or b"error" in res.data.lower()

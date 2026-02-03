from conftest import login


def test_login_wrong_password_shows_error(client):
    # admin is seeded by ensure_seed_admin()
    res = login(client, "admin", "wrongpassword")
    assert res.status_code == 200
    assert b"Invalid username or password" in res.data


def test_login_admin_redirects_to_admin_dashboard(client):
    res = login(client, "admin", "admin123")
    assert res.status_code in (302, 303)
    assert "/admin" in res.headers.get("Location", "")


def test_logout_clears_session(client):
    # login first
    res = login(client, "admin", "admin123")
    assert res.status_code in (302, 303)

    # access admin should work
    res2 = client.get("/admin", follow_redirects=False)
    assert res2.status_code == 200

    # logout
    res3 = client.get("/logout", follow_redirects=False)
    assert res3.status_code in (302, 303)
    assert "/login" in res3.headers.get("Location", "")

    # after logout, admin should redirect to login
    res4 = client.get("/admin", follow_redirects=False)
    assert res4.status_code in (302, 303)
    assert "/login" in res4.headers.get("Location", "")


def test_admin_page_requires_admin(client):
    # Create a normal user via admin UI quickly, then login as user
    login(client, "admin", "admin123")
    client.post("/admin/create_user", data={"username": "user1", "password": "pass1"}, follow_redirects=False)
    client.get("/logout", follow_redirects=False)

    # login as normal user
    res = login(client, "user1", "pass1")
    assert res.status_code in (302, 303)
    assert "/dashboard" in res.headers.get("Location", "")

    # user trying to access /admin should be blocked (redirect)
    res2 = client.get("/admin", follow_redirects=False)
    assert res2.status_code in (302, 303)

from conftest import login
import importlib

def test_session_invalidated_on_restart(client, monkeypatch):
    import app as app_module

    # Login as admin
    from conftest import login
    res = login(client, "admin", "admin123")
    assert res.status_code in (302, 303)
    assert client.get("/admin").status_code == 200

    # Simulate restart by changing RUN_ID in the same app instance
    monkeypatch.setattr(app_module, "RUN_ID", "NEW_RUN_ID")

    res2 = client.get("/admin", follow_redirects=False)
    assert res2.status_code in (302, 303)
    assert "/login" in res2.headers.get("Location", "")


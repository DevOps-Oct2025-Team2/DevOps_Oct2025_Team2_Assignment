import io
from conftest import login
from file_repo import list_files_for_user

def test_user_can_upload_and_delete_file(client):
    # 1. Create a user via Admin (or just assume one if we had a helper, but let's use the admin route first)
    login(client, "admin", "admin123")
    client.post(
        "/admin/create_user",
        data={"username": "fileuser", "password": "password"},
        follow_redirects=True
    )
    client.get("/logout", follow_redirects=True)

    # 2. Login as the new user
    login(client, "fileuser", "password")

    # 3. Upload a file
    file_content = b"This is a test file content."
    data = {
        "file": (io.BytesIO(file_content), "test_file.txt")
    }
    res_upload = client.post(
        "/dashboard/upload",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True
    )
    assert res_upload.status_code == 200
    assert b"File uploaded successfully." in res_upload.data
    assert b"test_file.txt" in res_upload.data

    # 4. Verify file in DB
    # We need the user_id suitable for file_repo, or we can just parse it from the list
    # Let's get the user ID from the user repo to be safe, or just trust the UI
    # For robust testing, let's use the repo.
    from user_repo import get_user_by_username
    user = get_user_by_username("fileuser")
    files = list_files_for_user(user["id"])
    assert len(files) == 1
    file_id = files[0]["id"]
    assert files[0]["original_filename"] == "test_file.txt"

    # 5. Delete the file
    res_delete = client.post(f"/dashboard/delete/{file_id}", follow_redirects=True)
    assert res_delete.status_code == 200
    assert b"File deleted." in res_delete.data

    # 6. Verify file is gone
    files_after = list_files_for_user(user["id"])
    assert len(files_after) == 0

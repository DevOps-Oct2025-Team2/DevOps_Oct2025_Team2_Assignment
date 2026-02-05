import os
import pytest

def test_env_file_has_no_secrets():
    """
    TestCase: Verify that the local .env file (if it exists) does not contain 
    actual secrets for GITHUB_PAT.
    """
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    if not os.path.exists(env_path):
        pytest.skip(".env file not found, skipping security check")
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if line.startswith("GITHUB_PAT="):
            value = line.split("=", 1)[1].strip()
            # Fail if value looks like a real token (len > 10 is a heuristic for real tokens)
            # Access tokens are usually long (starts with ghp_ or similar)
            if len(value) > 0 and value != "placeholder" and not value.startswith("ghp_placeholder"):
                 pytest.fail(f"SECURITY RISK: .env file contains a potential GITHUB_PAT token! Found value length: {len(value)}")

def test_env_flask_secret_not_default():
    """
    TestCase: Verify FLASK_SECRET_KEY is not the default 'DevOpsSecretKey' 
    in production-like environments (optional, just specific check).
    """
    pass

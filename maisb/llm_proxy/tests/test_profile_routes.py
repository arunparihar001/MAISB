import importlib
import re
import sys

from fastapi.testclient import TestClient


def load_scan_app(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "usage.db"))
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_FROM", raising=False)
    monkeypatch.delenv("RESEND_FROM_EMAIL", raising=False)
    for module_name in ("api.scan_api", "api.profile_routes", "api.public_routes"):
        sys.modules.pop(module_name, None)
    scan_api = importlib.import_module("api.scan_api")
    return scan_api


def test_production_routes_are_mounted(monkeypatch, tmp_path):
    scan_api = load_scan_app(monkeypatch, tmp_path)
    paths = set(scan_api.app.openapi()["paths"].keys())

    expected = {
        "/health",
        "/v1/plans",
        "/v1/profile/signup",
        "/v1/profile/verify-email",
        "/v1/profile/login",
        "/v1/profile/me",
        "/v1/profile/status",
        "/v1/plans/select",
        "/v1/api-keys",
        "/v1/api-keys/{key_id}/rotate",
        "/v1/api-keys/{key_id}/revoke",
        "/v1/scan",
    }

    assert expected.issubset(paths)


def test_signup_verification_flow_uses_pending_profile_and_link(monkeypatch, tmp_path):
    scan_api = load_scan_app(monkeypatch, tmp_path)
    from api import profile_routes

    captured = {}

    def fake_send_resend_email(to, subject, html_body):
        captured["to"] = to
        captured["subject"] = subject
        captured["body"] = html_body
        return True

    monkeypatch.setattr(profile_routes, "send_resend_email", fake_send_resend_email)

    client = TestClient(scan_api.app)
    signup_payload = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "company": "Analytical Engines",
        "use_case": "Verify auth flow",
        "password": "s3cret-pass",
    }

    signup_response = client.post("/v1/profile/signup", json=signup_payload)
    assert signup_response.status_code == 200
    signup_data = signup_response.json()
    assert signup_data["status"] == "pending_verification"
    assert signup_data["email_sent"] is True
    assert captured["subject"] == "Verify your MAISB account"
    assert "/verify-email?token=" in captured["body"]

    token_match = re.search(r"<pre>([^<]+)</pre>", captured["body"])
    assert token_match is not None
    raw_token = token_match.group(1)

    verify_response = client.post("/v1/profile/verify-email", json={"token": raw_token})
    assert verify_response.status_code == 200
    assert verify_response.json() == {"verified": True, "email": "ada@example.com"}

    verify_again = client.post("/v1/profile/verify-email", json={"token": raw_token})
    assert verify_again.status_code == 400

    conn = profile_routes.get_conn()
    profile_row = conn.execute("SELECT verified FROM profiles WHERE email=?", ("ada@example.com",)).fetchone()
    token_row = conn.execute("SELECT token_hash FROM email_verifications ORDER BY created_at DESC LIMIT 1").fetchone()
    conn.close()

    assert profile_row["verified"] == 1
    assert token_row["token_hash"] != raw_token
    assert len(token_row["token_hash"]) == 64

import re
import sys
from contextlib import closing

from fastapi.testclient import TestClient

MODULES_TO_CLEAR = ("api.scan_api", "api.profile_routes", "api.public_routes")


def setup_test_scan_app(monkeypatch, tmp_path, extra_env=None):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "usage.db"))
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_FROM", raising=False)
    monkeypatch.delenv("RESEND_FROM_EMAIL", raising=False)
    for key, value in (extra_env or {}).items():
        monkeypatch.setenv(key, value)
    for module_name in MODULES_TO_CLEAR:
        sys.modules.pop(module_name, None)
    from api import scan_api

    return scan_api


def test_production_routes_are_mounted(monkeypatch, tmp_path):
    scan_api = setup_test_scan_app(monkeypatch, tmp_path)
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


def test_signup_and_email_verification_flow(monkeypatch, tmp_path):
    scan_api = setup_test_scan_app(monkeypatch, tmp_path)
    from api import profile_routes

    email = "ada@example.com"
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
        "email": email,
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
    assert "https://app.maisb.app/verify-email" in captured["body"]

    token_match = re.search(r"<pre>([^<]+)</pre>", captured["body"])
    assert token_match is not None
    raw_token = token_match.group(1)

    verify_response = client.post("/v1/profile/verify-email", json={"token": raw_token})
    assert verify_response.status_code == 200
    assert verify_response.json() == {"verified": True, "email": email}

    verify_again = client.post("/v1/profile/verify-email", json={"token": raw_token})
    assert verify_again.status_code == 400

    with closing(profile_routes.get_conn()) as conn:
        profile_row = conn.execute("SELECT verified FROM profiles WHERE email=?", (email,)).fetchone()
        token_row = conn.execute("SELECT token_hash FROM email_verifications ORDER BY created_at DESC LIMIT 1").fetchone()

    assert profile_row["verified"] == 1
    assert token_row["token_hash"] != raw_token
    assert len(token_row["token_hash"]) == 64


def test_cors_preflight_allows_production_signup_origin(monkeypatch, tmp_path):
    scan_api = setup_test_scan_app(monkeypatch, tmp_path)
    client = TestClient(scan_api.app)

    for path in (
        "/v1/profile/signup",
        "/v1/profile/verify-email",
        "/v1/profile/login",
        "/v1/api-keys",
    ):
        response = client.options(
            path,
            headers={
                "Origin": "https://app.maisb.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        assert response.status_code in {200, 204}
        assert response.headers["access-control-allow-origin"] == "https://app.maisb.app"
        assert "POST" in response.headers["access-control-allow-methods"]
        assert "content-type" in response.headers["access-control-allow-headers"].lower()


def test_signup_returns_json_error_when_email_delivery_fails(monkeypatch, tmp_path):
    scan_api = setup_test_scan_app(
        monkeypatch,
        tmp_path,
        extra_env={
            "APP_ENV": "production",
            "RESEND_API_KEY": "test-key",
            "RESEND_FROM_EMAIL": "MAISB <hello@updates.maisb.app>",
        },
    )
    signup_route = next(route for route in scan_api.app.routes if getattr(route, "path", None) == "/v1/profile/signup")
    monkeypatch.setitem(signup_route.endpoint.__globals__, "resend_enabled", lambda: True)
    monkeypatch.setitem(signup_route.endpoint.__globals__, "send_resend_email", lambda *args, **kwargs: False)

    client = TestClient(scan_api.app)
    response = client.post(
        "/v1/profile/signup",
        json={
            "name": "Grace Hopper",
            "email": "grace@example.com",
            "company": "US Navy",
            "use_case": "Verify error handling",
            "password": "s3cret-pass",
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"]["error"] == "verification_email_failed"

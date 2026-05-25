import re
import sys
from contextlib import closing

import httpx
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

    signup_response = client.post(
        "/v1/profile/signup",
        json=signup_payload,
        headers={"Origin": "https://app.maisb.app"},
    )
    assert signup_response.status_code == 200
    assert signup_response.headers["access-control-allow-origin"] == "https://app.maisb.app"
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


def test_send_resend_email_posts_to_resend_api(monkeypatch, tmp_path):
    setup_test_scan_app(monkeypatch, tmp_path)
    from api import profile_routes

    captured = {}

    class FakeResponse:
        status_code = 200
        headers = {}

        def raise_for_status(self):
            return None

    def fake_post(url, *, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(profile_routes, "RESEND_API_KEY", "test-key")
    monkeypatch.setattr(profile_routes, "RESEND_FROM", "MAISB <hello@updates.maisb.app>")
    monkeypatch.setattr(profile_routes, "RESEND_REPLY_TO", "sales@maisb.app")

    assert profile_routes.send_resend_email("ada@example.com", "Verify", "<p>Body</p>") is True
    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["headers"] == {
        "Authorization": "Bearer test-key",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "MAISB/1.0",
    }
    assert captured["json"] == {
        "from": "hello@updates.maisb.app",
        "to": ["ada@example.com"],
        "subject": "Verify",
        "html": "<p>Body</p>",
        "reply_to": "sales@maisb.app",
    }
    assert isinstance(captured["timeout"], httpx.Timeout)
    assert captured["timeout"].read == 8.0
    assert captured["timeout"].connect == 5.0


def test_send_resend_email_uses_bare_sender_when_already_canonical(monkeypatch, tmp_path):
    setup_test_scan_app(monkeypatch, tmp_path)
    from api import profile_routes

    captured = {}

    class FakeResponse:
        status_code = 200
        headers = {}

        def raise_for_status(self):
            return None

    def fake_post(url, *, json=None, headers=None, timeout=None):
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(profile_routes, "RESEND_API_KEY", "test-key")
    monkeypatch.setattr(profile_routes, "RESEND_FROM", "hello@updates.maisb.app")

    assert profile_routes.send_resend_email("ada@example.com", "Verify", "<p>Body</p>") is True
    assert captured["json"]["from"] == "hello@updates.maisb.app"


def test_send_resend_email_records_provider_error_diagnostics(monkeypatch, tmp_path):
    setup_test_scan_app(monkeypatch, tmp_path)
    from api import profile_routes

    request = httpx.Request("POST", "https://api.resend.com/emails")
    provider_error = {
        "error": "forbidden",
        "message": "Sender domain is not verified for this workspace.",
    }
    response = httpx.Response(
        403,
        request=request,
        json=provider_error,
    )

    def fake_post(*args, **kwargs):
        raise httpx.HTTPStatusError("Forbidden", request=request, response=response)

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(profile_routes, "RESEND_API_KEY", "test-key")
    monkeypatch.setattr(profile_routes, "RESEND_FROM", "hello@updates.maisb.app")

    assert profile_routes.send_resend_email("ada@example.com", "Verify", "<p>Body</p>") is False
    assert profile_routes.get_last_resend_diagnostics() == {
        "provider": "resend",
        "status_code": 403,
        "provider_error": provider_error,
        "error": "forbidden",
        "message": "Sender domain is not verified for this workspace.",
    }


def test_duplicate_unverified_signup_resends_verification(monkeypatch, tmp_path):
    scan_api = setup_test_scan_app(monkeypatch, tmp_path)
    from api import profile_routes

    sent_messages = []

    def fake_send_resend_email(to, subject, html_body):
        sent_messages.append((to, subject, html_body))
        return True

    monkeypatch.setattr(profile_routes, "send_resend_email", fake_send_resend_email)

    client = TestClient(scan_api.app)
    payload = {
        "name": "Grace Hopper",
        "email": "grace@example.com",
        "company": "US Navy",
        "use_case": "First signup",
        "password": "s3cret-pass",
    }

    first = client.post("/v1/profile/signup", json=payload)
    assert first.status_code == 200
    assert first.json()["created"] is True

    with closing(profile_routes.get_conn()) as conn:
        initial_hash = conn.execute(
            "SELECT password_hash FROM profiles WHERE email=?",
            (payload["email"],),
        ).fetchone()["password_hash"]

    second = client.post(
        "/v1/profile/signup",
        json={**payload, "name": "Grace M. Hopper", "use_case": "Resend signup", "password": "new-pass-123"},
    )
    assert second.status_code == 200
    data = second.json()
    assert data["created"] is False
    assert data["status"] == "pending_verification"
    assert data["email_sent"] is True
    assert data["message"] == "Verification email resent."
    assert len(sent_messages) == 2

    with closing(profile_routes.get_conn()) as conn:
        current_hash = conn.execute(
            "SELECT password_hash FROM profiles WHERE email=?",
            (payload["email"],),
        ).fetchone()["password_hash"]

    assert current_hash != initial_hash
    token_match = re.search(r"<pre>([^<]+)</pre>", sent_messages[-1][2])
    assert token_match is not None
    verify = client.post("/v1/profile/verify-email", json={"token": token_match.group(1)})
    assert verify.status_code == 200

    login = client.post(
        "/v1/profile/login",
        json={"email": payload["email"], "password": "new-pass-123"},
    )
    assert login.status_code == 200
    assert login.json()["profile"]["email"] == payload["email"]


def test_duplicate_verified_signup_returns_conflict(monkeypatch, tmp_path):
    scan_api = setup_test_scan_app(monkeypatch, tmp_path)
    from api import profile_routes

    sent_messages = []

    def fake_send_resend_email(to, subject, html_body):
        sent_messages.append((to, subject, html_body))
        return True

    monkeypatch.setattr(profile_routes, "send_resend_email", fake_send_resend_email)

    client = TestClient(scan_api.app)
    email = "maya@example.com"
    signup = client.post(
        "/v1/profile/signup",
        json={
            "name": "Maya Angelou",
            "email": email,
            "company": "Writer",
            "use_case": "Verification",
            "password": "s3cret-pass",
        },
    )
    token_match = re.search(r"<pre>([^<]+)</pre>", sent_messages[0][2])
    assert signup.status_code == 200
    assert token_match is not None

    verify = client.post("/v1/profile/verify-email", json={"token": token_match.group(1)})
    assert verify.status_code == 200

    duplicate = client.post(
        "/v1/profile/signup",
        json={
            "name": "Maya Angelou",
            "email": email,
            "company": "Writer",
            "use_case": "Verification",
            "password": "s3cret-pass",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "An account with this email already exists. Please log in."
    assert len(sent_messages) == 1


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


def test_cors_test_endpoint_reports_origin(monkeypatch, tmp_path):
    scan_api = setup_test_scan_app(monkeypatch, tmp_path)
    client = TestClient(scan_api.app)

    response = client.get("/v1/cors-test", headers={"Origin": "https://app.maisb.app"})

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "service": "maisb-api",
        "origin": "https://app.maisb.app",
        "cors": "enabled",
    }


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
    provider_error = {
        "error": "forbidden",
        "message": "Sender domain is not verified for this workspace.",
    }
    signup_route = next(route for route in scan_api.app.routes if getattr(route, "path", None) == "/v1/profile/signup")
    monkeypatch.setitem(signup_route.endpoint.__globals__, "resend_enabled", lambda: True)
    monkeypatch.setitem(signup_route.endpoint.__globals__, "send_resend_email", lambda *args, **kwargs: False)
    monkeypatch.setitem(
        signup_route.endpoint.__globals__,
        "get_last_resend_diagnostics",
        lambda: {
            "provider": "resend",
            "status_code": 403,
            "error": "forbidden",
            "provider_error": provider_error,
            "message": "Sender domain is not verified for this workspace.",
        },
    )

    client = TestClient(scan_api.app)
    response = client.post(
        "/v1/profile/signup",
        json={
            "name": "Grace Hopper",
            "email": "grace-failure@example.com",
            "company": "US Navy",
            "use_case": "Verify error handling",
            "password": "s3cret-pass",
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"]["error"] == "verification_email_failed"
    assert response.json()["detail"]["diagnostics"] == {
        "provider": "resend",
        "status_code": 403,
        "error": "forbidden",
        "provider_error": provider_error,
        "message": "Sender domain is not verified for this workspace.",
    }

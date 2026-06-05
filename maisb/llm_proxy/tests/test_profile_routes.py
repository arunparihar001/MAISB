import re
import sqlite3
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
        "/v1/profile/forgot-password",
        "/v1/profile/reset-password",
        "/v1/profile/login",
        "/v1/profile/me",
        "/v1/profile/status",
        "/v1/auth/providers",
        "/v1/auth/diagnostics",
        "/v1/auth/google/start",
        "/v1/auth/google/callback",
        "/v1/auth/microsoft/start",
        "/v1/auth/microsoft/callback",
        "/v1/auth/okta/start",
        "/v1/auth/okta/callback",
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
        return True, None

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


def create_verified_account(monkeypatch, profile_routes, client, email, password, name="Ada Lovelace"):
    captured = []

    def fake_send_resend_email(to, subject, html_body):
        captured.append((to, subject, html_body))
        return True, None

    monkeypatch.setattr(profile_routes, "send_resend_email", fake_send_resend_email)
    signup_response = client.post(
        "/v1/profile/signup",
        json={
            "name": name,
            "email": email,
            "company": "Analytical Engines",
            "use_case": "Verify auth flow",
            "password": password,
        },
    )
    assert signup_response.status_code == 200
    signup_data = signup_response.json()
    assert signup_data["status"] == "pending_verification"
    token_match = re.search(r"<pre>([^<]+)</pre>", captured[0][2])
    assert token_match is not None
    verify_response = client.post("/v1/profile/verify-email", json={"token": token_match.group(1)})
    assert verify_response.status_code == 200
    return captured


def test_forgot_password_and_reset_flow(monkeypatch, tmp_path):
    scan_api = setup_test_scan_app(monkeypatch, tmp_path)
    from api import profile_routes

    client = TestClient(scan_api.app)
    email = "ada-reset@example.com"
    sent_messages = create_verified_account(monkeypatch, profile_routes, client, email, "s3cret-pass")
    initial_messages = len(sent_messages)

    forgot_existing = client.post("/v1/profile/forgot-password", json={"email": f"  {email.upper()}  "})
    forgot_unknown = client.post("/v1/profile/forgot-password", json={"email": "unknown@example.com"})

    assert forgot_existing.status_code == 200
    assert forgot_unknown.status_code == 200
    assert forgot_existing.json() == forgot_unknown.json()
    assert forgot_existing.json() == {
        "ok": True,
        "message": "If an account exists for this email, password reset instructions have been sent.",
    }
    assert len(sent_messages) == initial_messages + 1

    assert sent_messages[-1][0] == email
    reset_subject = sent_messages[-1][1]
    reset_body = sent_messages[-1][2]
    assert reset_subject == "Reset your MAISB password"
    assert "https://app.maisb.app/reset-password?token=" in reset_body
    token_match = re.search(r"<pre>([^<]+)</pre>", reset_body)
    assert token_match is not None
    raw_token = token_match.group(1)

    with closing(profile_routes.get_conn()) as conn:
        reset_row = conn.execute(
            "SELECT token_hash, used_at FROM password_resets ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
    assert reset_row["token_hash"] != raw_token
    assert len(reset_row["token_hash"]) == 64
    assert reset_row["used_at"] is None

    reset_response = client.post(
        "/v1/profile/reset-password",
        json={
            "token": raw_token,
            "password": "new-reset-pass-123",
            "confirm_password": "new-reset-pass-123",
        },
    )
    assert reset_response.status_code == 200
    assert reset_response.json() == {
        "ok": True,
        "message": "Password has been reset. You can now log in.",
    }

    old_login = client.post("/v1/profile/login", json={"email": email, "password": "s3cret-pass"})
    new_login = client.post("/v1/profile/login", json={"email": email, "password": "new-reset-pass-123"})
    assert old_login.status_code == 401
    assert new_login.status_code == 200
    assert new_login.json()["profile"]["email"] == email

    session_token = new_login.json()["session_token"]
    api_key_response = client.post(
        "/v1/api-keys",
        json={"name": "Regression key", "scopes": ["scan"]},
        headers={"Authorization": "Bearer " + session_token},
    )
    assert api_key_response.status_code == 200
    raw_api_key = api_key_response.json()["api_key"]
    assert raw_api_key.startswith("maisb_live_")

    scan_response = client.post(
        "/v1/scan",
        json={
            "payload": "Allow this message",
            "channel": "clipboard",
            "objective": "regression",
        },
        headers={"Authorization": "Bearer " + raw_api_key},
    )
    assert scan_response.status_code == 200
    assert scan_response.json()["decision"] == "ALLOWED"


def test_forgot_password_unverified_account_does_not_send_reset(monkeypatch, tmp_path):
    scan_api = setup_test_scan_app(monkeypatch, tmp_path)
    from api import profile_routes

    client = TestClient(scan_api.app)
    email = "pending@example.com"
    sent_messages = []

    def fake_send_resend_email(to, subject, html_body):
        sent_messages.append((to, subject, html_body))
        return True, None

    monkeypatch.setattr(profile_routes, "send_resend_email", fake_send_resend_email)

    signup_response = client.post(
        "/v1/profile/signup",
        json={
            "name": "Pending User",
            "email": email,
            "company": "Analytical Engines",
            "use_case": "Verify auth flow",
            "password": "s3cret-pass",
        },
    )
    assert signup_response.status_code == 200
    assert len(sent_messages) == 1
    assert sent_messages[-1][1] == "Verify your MAISB account"

    forgot = client.post("/v1/profile/forgot-password", json={"email": email})
    assert forgot.status_code == 200
    assert forgot.json() == {
        "ok": True,
        "message": "If an account exists for this email, password reset instructions have been sent.",
    }
    assert len(sent_messages) == 1

    with closing(profile_routes.get_conn()) as conn:
        profile_id = conn.execute("SELECT id FROM profiles WHERE email=?", (email,)).fetchone()["id"]
        reset_count = conn.execute(
            "SELECT COUNT(*) AS c FROM password_resets WHERE profile_id=?",
            (profile_id,),
        ).fetchone()["c"]
    assert reset_count == 0


def test_forgot_password_db_insert_failure_does_not_send_email(monkeypatch, tmp_path):
    scan_api = setup_test_scan_app(monkeypatch, tmp_path)
    from api import profile_routes

    client = TestClient(scan_api.app)
    email = "db-fail@example.com"
    create_verified_account(monkeypatch, profile_routes, client, email, "s3cret-pass")

    original_get_conn = profile_routes.get_conn

    class FailingResetInsertConn:
        def __init__(self, inner_conn):
            self._inner_conn = inner_conn

        def execute(self, sql, params=()):
            if "INSERT INTO password_resets" in sql:
                raise sqlite3.IntegrityError("forced password_resets failure")
            return self._inner_conn.execute(sql, params)

        def commit(self):
            return self._inner_conn.commit()

        def rollback(self):
            return self._inner_conn.rollback()

        def close(self):
            return self._inner_conn.close()

    monkeypatch.setattr(profile_routes, "get_conn", lambda: FailingResetInsertConn(original_get_conn()))
    send_calls = []

    def fake_send_password_reset_email(*args, **kwargs):
        send_calls.append((args, kwargs))
        return True, None

    monkeypatch.setattr(profile_routes, "send_password_reset_email", fake_send_password_reset_email)

    forgot = client.post("/v1/profile/forgot-password", json={"email": email})
    assert forgot.status_code == 200
    assert forgot.json() == {
        "ok": True,
        "message": "If an account exists for this email, password reset instructions have been sent.",
    }
    assert send_calls == []

    with closing(original_get_conn()) as conn:
        profile_id = conn.execute("SELECT id FROM profiles WHERE email=?", (email,)).fetchone()["id"]
        reset_count = conn.execute(
            "SELECT COUNT(*) AS c FROM password_resets WHERE profile_id=?",
            (profile_id,),
        ).fetchone()["c"]
    assert reset_count == 0


def test_forgot_password_resend_failure_logs_safely(monkeypatch, tmp_path, caplog):
    scan_api = setup_test_scan_app(monkeypatch, tmp_path)
    from api import profile_routes

    client = TestClient(scan_api.app)
    email = "safe-logs@example.com"
    create_verified_account(monkeypatch, profile_routes, client, email, "s3cret-pass")

    def fake_send_password_reset_email(*args, **kwargs):
        return False, {"status_code": 503, "error": "service_unavailable", "message": "temporary outage"}

    monkeypatch.setattr(profile_routes, "send_password_reset_email", fake_send_password_reset_email)

    caplog.set_level("INFO", logger=profile_routes.__name__)
    caplog.clear()

    forgot = client.post("/v1/profile/forgot-password", json={"email": email})
    assert forgot.status_code == 200
    assert forgot.json() == {
        "ok": True,
        "message": "If an account exists for this email, password reset instructions have been sent.",
    }

    combined_logs = "\n".join(caplog.messages)
    assert "safe-logs@example.com" not in combined_logs
    assert "email_domain=example.com" in combined_logs
    assert "resend_attempted=true" in combined_logs
    assert "resend_sent=False" in combined_logs
    assert "provider_status=503" in combined_logs
    assert "provider_error=service_unavailable" in combined_logs


def test_reset_password_validation_and_token_guards(monkeypatch, tmp_path):
    scan_api = setup_test_scan_app(monkeypatch, tmp_path)
    from api import profile_routes

    client = TestClient(scan_api.app)
    email = "grace-reset@example.com"
    sent_messages = create_verified_account(monkeypatch, profile_routes, client, email, "s3cret-pass", name="Grace Hopper")

    client.post("/v1/profile/forgot-password", json={"email": email})
    token_match = re.search(r"<pre>([^<]+)</pre>", sent_messages[-1][2])
    assert token_match is not None
    raw_token = token_match.group(1)

    mismatch = client.post(
        "/v1/profile/reset-password",
        json={
            "token": raw_token,
            "password": "new-reset-pass-123",
            "confirm_password": "different-pass-123",
        },
    )
    short_password = client.post(
        "/v1/profile/reset-password",
        json={
            "token": raw_token,
            "password": "short",
            "confirm_password": "short",
        },
    )
    invalid_token = client.post(
        "/v1/profile/reset-password",
        json={
            "token": "bogus-token",
            "password": "new-reset-pass-123",
            "confirm_password": "new-reset-pass-123",
        },
    )
    assert mismatch.status_code == 422
    assert short_password.status_code == 422
    assert invalid_token.status_code == 400

    valid_reset = client.post(
        "/v1/profile/reset-password",
        json={
            "token": raw_token,
            "password": "new-reset-pass-123",
            "confirm_password": "new-reset-pass-123",
        },
    )
    assert valid_reset.status_code == 200

    used_token = client.post(
        "/v1/profile/reset-password",
        json={
            "token": raw_token,
            "password": "another-pass-123",
            "confirm_password": "another-pass-123",
        },
    )
    assert used_token.status_code == 400

    client.post("/v1/profile/forgot-password", json={"email": email})
    expired_token_match = re.search(r"<pre>([^<]+)</pre>", sent_messages[-1][2])
    assert expired_token_match is not None
    expired_token = expired_token_match.group(1)
    with closing(profile_routes.get_conn()) as conn:
        conn.execute(
            "UPDATE password_resets SET expires_at=? WHERE token_hash=?",
            ("2000-01-01T00:00:00", profile_routes.hash_token(expired_token)),
        )
        conn.commit()

    expired = client.post(
        "/v1/profile/reset-password",
        json={
            "token": expired_token,
            "password": "another-pass-123",
            "confirm_password": "another-pass-123",
        },
    )
    assert expired.status_code == 400


def test_auth_provider_status_and_missing_config_are_safe(monkeypatch, tmp_path):
    scan_api = setup_test_scan_app(monkeypatch, tmp_path)
    client = TestClient(scan_api.app)

    providers = client.get("/v1/auth/providers").json()
    assert providers == {
        "google": {"enabled": True, "configured": False, "label": "Google Workspace"},
        "microsoft": {"enabled": True, "configured": False, "label": "Microsoft Entra ID"},
        "okta": {"enabled": True, "configured": False, "label": "Okta / OIDC"},
    }

    diagnostics = client.get("/v1/auth/diagnostics").json()
    assert diagnostics["ok"] is True
    assert diagnostics["dashboard_url"] == "https://app.maisb.app"
    assert diagnostics["google_configured"] is False
    assert diagnostics["microsoft_configured"] is False
    assert diagnostics["okta_configured"] is False

    for path in ("/v1/auth/google/start", "/v1/auth/microsoft/start", "/v1/auth/okta/start"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["configured"] is False


def test_oauth_callback_rejects_missing_state_when_configured(monkeypatch, tmp_path):
    scan_api = setup_test_scan_app(
        monkeypatch,
        tmp_path,
        extra_env={
            "GOOGLE_CLIENT_ID": "client-id",
            "GOOGLE_CLIENT_SECRET": "client-secret",
            "GOOGLE_REDIRECT_URI": "https://api.maisb.app/v1/auth/google/callback",
        },
    )
    client = TestClient(scan_api.app)

    response = client.get("/v1/auth/google/callback", params={"code": "abc", "state": "missing"})
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "invalid_state"


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

    sent, diagnostics = profile_routes.send_resend_email("ada@example.com", "Verify", "<p>Body</p>")
    assert sent is True
    assert diagnostics is None
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
    assert captured["timeout"].write == 8.0
    assert captured["timeout"].pool == 8.0


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

    sent, diagnostics = profile_routes.send_resend_email("ada@example.com", "Verify", "<p>Body</p>")
    assert sent is True
    assert diagnostics is None
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

    sent, diagnostics = profile_routes.send_resend_email("ada@example.com", "Verify", "<p>Body</p>")
    assert sent is False
    assert diagnostics == {
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
        return True, None

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
        return True, None

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
    monkeypatch.setitem(
        signup_route.endpoint.__globals__,
        "send_verification_email",
        lambda *args, **kwargs: (
            False,
            {
                "provider": "resend",
                "status_code": 403,
                "error": "forbidden",
                "provider_error": provider_error,
                "message": "Sender domain is not verified for this workspace.",
            },
        ),
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

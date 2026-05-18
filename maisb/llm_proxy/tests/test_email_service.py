from services import email_service


def test_email_service_fails_safe_without_resend_key(monkeypatch):
    monkeypatch.setattr(email_service, 'RESEND_API_KEY', '')
    assert email_service.send_admin_notification('subject', 'message') is False

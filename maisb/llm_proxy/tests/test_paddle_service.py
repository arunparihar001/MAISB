import hashlib
import hmac

from services import paddle_service


def test_verify_webhook_signature_accepts_valid_signature(monkeypatch):
    raw = b'{"event_id":"evt_1"}'
    ts = '1710000000'
    secret = 'test_secret'
    monkeypatch.setattr(paddle_service, 'PADDLE_WEBHOOK_SECRET', secret)
    digest = hmac.new(secret.encode('utf-8'), f'{ts}:{raw.decode("utf-8")}'.encode('utf-8'), hashlib.sha256).hexdigest()

    assert paddle_service.verify_webhook_signature(raw, f'ts={ts};h1={digest}')
    assert not paddle_service.verify_webhook_signature(raw, f'ts={ts};h1=bad')


def test_event_identity_and_plan_for_price(monkeypatch):
    monkeypatch.setattr(paddle_service, 'PADDLE_CERTIFY_PRICE_ID', 'pri_certify')
    assert paddle_service.event_identity({'event_id': 'evt_2', 'event_type': 'transaction.completed'}) == {
        'event_id': 'evt_2',
        'event_type': 'transaction.completed',
    }
    assert paddle_service.plan_for_price('pri_certify') == 'certify'
    assert paddle_service.plan_for_price('pri_other') == 'pro'

from services import billing_store


def test_store_webhook_event_is_idempotent(tmp_path, monkeypatch):
    db_path = str(tmp_path / 'billing.db')
    monkeypatch.setattr(billing_store, 'DB_PATH', db_path)
    billing_store.init_billing_store()
    first = billing_store.store_webhook_event('evt_1', 'transaction.completed', {'ok': True})
    second = billing_store.store_webhook_event('evt_1', 'transaction.completed', {'ok': True})
    assert first is True
    assert second is False

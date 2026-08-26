from datetime import datetime, timezone

from cleanup_service import stale_order


def test_only_old_open_orders_are_stale():
    now = datetime(2026, 8, 19, tzinfo=timezone.utc)
    old = {"status": "checkout", "updated_at": "2026-07-01T00:00:00Z"}
    recent = {"status": "checkout", "updated_at": "2026-08-10T00:00:00Z"}
    shipped = {"status": "shipped", "updated_at": "2026-07-01T00:00:00Z"}
    assert stale_order(old, now) is True
    assert stale_order(recent, now) is False
    assert stale_order(shipped, now) is False

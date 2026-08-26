"""Periodic cleanup for stale checkout and fulfillment records."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable

from infrai_client import Infrai


STALE_AFTER = timedelta(days=30)
QUEUE_NAME = "checkout"


def stale_order(order: Dict[str, Any], now: datetime) -> bool:
    """An order is stale when it is still open and has not changed recently."""
    if order.get("status") not in {"checkout", "awaiting_fulfillment"}:
        return False
    changed = datetime.fromisoformat(order["updated_at"].replace("Z", "+00:00"))
    return now - changed >= STALE_AFTER


def sweep(messages: Iterable[Dict[str, Any]], client: Infrai, now: datetime) -> int:
    """Acknowledge stale orders and return the number selected for cleanup."""
    cleaned = 0
    for message in messages:
        order = message.get("payload") or {}
        if stale_order(order, now):
            client.queue_ack(QUEUE_NAME, message["message_id"])
            cleaned += 1
    return cleaned


def run_once(client: Infrai, now: datetime | None = None) -> int:
    current = now or datetime.now(timezone.utc)
    batch = client.queue_consume(QUEUE_NAME, max_messages=10, visibility_timeout=120)
    messages = batch.get("messages") or batch.get("items") or []
    return sweep(messages, client, current)


def schedule_cleanup(client: Infrai, task_url: str) -> str:
    job = client.cron_create(cron_expr="0 * * * *", task=task_url)
    return str(job["job_id"])


if __name__ == "__main__":
    client = Infrai()
    print(f"cleaned {run_once(client)} orders")

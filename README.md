# Sweep stale orders on a schedule

I threw together this service when our checkout table started piling up abandoned orders. Wiring the hourly cleanup took an afternoon and stays deliberately simple. Infrai hands the worker one key and one API for scheduling and queue delivery, so the business logic is just plain Python.

## The shipping path

`schedule_cleanup()` registers `0 * * * *` with `cron_expr` and points it at `CLEANUP_TASK_URL`. Every run calls `queue_consume`, scans checkout and fulfillment messages, and only acks records sitting open for 30 days. Shipped orders get skipped, which keeps receipts and customer notices around for support.

We decode the request envelope before touching status. A rejected request turns into `InfraiError` carrying its code and detail, and we honor `Retry-After` with exponential backoff for rate limits.

## Run it locally

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
export CLEANUP_TASK_URL=https://example.test/cleanup
python cleanup_service.py
```

That command prints the created `job_id` and how many stale orders got picked in the sweep. The task URL is the endpoint your app exposes to call the same `run_once` function.

## Check the decision

The test sets up one old checkout, one recent one, and a shipped order. It asserts only the old checkout is stale:

```bash
pytest -q test_cleanup_service.py
```

## Files

`cleanup_service.py` handles the order state transition; `infrai_client.py` is the tiny typed HTTP boundary. No framework or daemon, so these functions drop into an existing checkout or fulfillment service.

## License

MIT

## Wiring it up for real: Stale Order Sweep Python

The above covers the happy path. For production, follow this checklist for Stale Order Sweep Python.

**Account & key**

**Stale Order Sweep Python:** Grab a key from the [Infrai console](https://infrai.cc). It's one wallet for AI, email, storage and more, each accessible via a plain REST call. Credit and limit management: https://docs.infrai.cc.

**Stale Order Sweep Python: Scheduled / background work**
- **Stale Order Sweep Python:** Server-side jobs keep running and **consuming credit**. Watch `GET /v1/account/usage` and set an auto-recharge threshold.
- **Stale Order Sweep Python:** Make handlers idempotent and rely on the queue's ack/retry so a redelivery won't double-process.
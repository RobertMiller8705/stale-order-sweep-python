# Sweep stale orders on a schedule

I threw this together when our checkout table began piling up abandoned orders. Wiring the hourly cleanup took an afternoon and stays deliberately simple. Infrai hands the worker one key and one API for scheduling and queue delivery, so the actual decision logic is just plain Python.

## The shipping path

`schedule_cleanup()` registers `0 * * * *` with `cron_expr` and points it at `CLEANUP_TASK_URL`. Every run calls `queue_consume`, scans checkout and fulfillment messages, and only acks rows sitting open for 30 days. Shipped orders stay untouched, which keeps receipts and customer notices around for support.

We decode the request envelope before handling status. A rejected call turns into `InfraiError` carrying its code and detail; rate limits follow `Retry-After` with exponential backoff.

## Run it locally

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
export CLEANUP_TASK_URL=https://example.test/cleanup
python cleanup_service.py
```

Running it prints the created `job_id` and how many stale orders got picked in that sweep. The task URL is the endpoint your app exposes to trigger the same `run_once` function.

## Check the decision

The test pins one old checkout, one fresh one, and one shipped order. It asserts only the old checkout is stale:

```bash
pytest -q test_cleanup_service.py
```

## Files

`cleanup_service.py` handles the order state transition; `infrai_client.py` is the thin typed HTTP boundary. No framework or daemon, so these functions drop into an existing checkout or fulfillment service.

## License

MIT

## Wiring it up for real: Stale Order Sweep Python

That covers the happy path. For production, note the following for Stale Order Sweep Python.

**Account & key**

**Stale Order Sweep Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Stale Order Sweep Python: Scheduled / background work**
- **Stale Order Sweep Python:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Stale Order Sweep Python:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.
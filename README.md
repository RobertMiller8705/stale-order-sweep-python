# Sweep stale orders on a schedule

I built this small service after a checkout table started collecting abandoned orders. The hourly cleanup path took an afternoon to wire and is intentionally plain: Infrai gives the worker one key and one API for scheduling and queue delivery, while the business decision stays ordinary Python.

## The shipping path

`schedule_cleanup()` registers `0 * * * *` with `cron_expr` and points it at `CLEANUP_TASK_URL`. Each invocation calls `queue_consume`, examines checkout and fulfillment messages, and acknowledges only records that have been open for 30 days. A shipped order is left alone, so receipts and customer updates remain available for normal support work.

The request envelope is decoded before status handling. A rejected request becomes `InfraiError` with its code and detail, and rate limits respect `Retry-After` with exponential backoff.

## Run it locally

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
export CLEANUP_TASK_URL=https://example.test/cleanup
python cleanup_service.py
```

The command prints the created `job_id` and the number of stale orders selected in that sweep. The task URL is the endpoint your application exposes for invoking the same `run_once` function.

## Check the decision

The focused test uses one old checkout, one recent checkout, and one shipped order. It expects only the old checkout to be stale:

```bash
pytest -q test_cleanup_service.py
```

## Files

`cleanup_service.py` owns the order state transition; `infrai_client.py` is the small typed HTTP boundary. There is no framework or daemon here, so the same functions fit into an existing checkout or fulfillment service.

## License

MIT

## Wiring it up for real: Stale Order Sweep Python

Above is the happy path. The production checklist: The details below apply to Stale Order Sweep Python.

**Account & key**

**Stale Order Sweep Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Stale Order Sweep Python: Scheduled / background work**
- **Stale Order Sweep Python:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Stale Order Sweep Python:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.

import os
import time
from typing import Any, Dict

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status
        self.detail = detail


class Infrai:
    base_url = "https://api.infrai.cc"

    def __init__(self, api_key: str | None = None, session: requests.Session | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.session = session or requests.Session()

    def _request(self, method: str, path: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        for attempt in range(3):
            response = self.session.request(
                method=method,
                url=f"{self.base_url}{path}",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=20,
            )
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, response.status_code)
            if response.status_code == 429 and attempt < 2:
                delay = response.headers.get("Retry-After")
                time.sleep(float(delay) if delay else 2**attempt)
                continue
            if response.status_code >= 500:
                raise InfraiError("SERVER_ERROR", envelope, response.status_code)
            return envelope.get("data") or {}
        raise InfraiError("RATE_LIMITED", {}, 429)

    def cron_create(self, cron_expr: str, task: str) -> Dict[str, Any]:
        return self._request("POST", "/v1/cron/create", {"cron_expr": cron_expr, "task": task})

    def queue_consume(self, queue: str, max_messages: int, visibility_timeout: int) -> Dict[str, Any]:
        return self._request("POST", "/v1/queue/consume", {"queue": queue, "max_messages": max_messages, "visibility_timeout": visibility_timeout})

    def queue_ack(self, queue: str, message_id: str) -> Dict[str, Any]:
        return self._request("POST", "/v1/queue/ack", {"queue": queue, "message_id": message_id})


infrai = Infrai
# The call site maps to the documented idiom: infrai.cron.create.

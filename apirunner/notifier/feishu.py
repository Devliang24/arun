from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import Optional

import httpx

from .base import Notifier, NotifyContext
from .format import build_summary_text
from apirunner.models.report import RunReport


class FeishuNotifier(Notifier):
    def __init__(self, *, webhook: str, secret: Optional[str] = None, mentions: Optional[str] = None, timeout: float = 6.0) -> None:
        self.webhook = webhook
        self.secret = secret
        self.mentions = mentions or ""
        self.timeout = timeout

    def _sign(self, ts: str) -> str:
        # sign = base64(hmac_sha256(ts + '\n' + secret, secret))
        msg = (ts + "\n" + (self.secret or "")).encode()
        dig = hmac.new((self.secret or "").encode(), msg, digestmod=hashlib.sha256).digest()
        return base64.b64encode(dig).decode()

    def send(self, report: RunReport, ctx: NotifyContext) -> None:  # pragma: no cover - integration
        if not self.webhook:
            return
        text = build_summary_text(report, html_path=ctx.html_path, log_path=ctx.log_path, topn=ctx.topn)
        if self.mentions:
            text = f"提醒: {self.mentions}\n" + text
        payload: dict = {
            "msg_type": "text",
            "content": {"text": text},
        }
        headers = {"Content-Type": "application/json"}
        url = self.webhook
        if self.secret:
            ts = str(int(time.time()))
            payload.update({"timestamp": ts, "sign": self._sign(ts)})
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=payload, headers=headers)
                # Feishu returns 200 even for errors; ignore body parsing here
                _ = resp.text
        except Exception:
            # best-effort, ignore failures
            return


"""带同主机限流与有界重试的 HTTP 客户端（学术注册库友好）。

设计要点：
- 同主机最小间隔节流（export.arxiv.org 等对突发请求返回 429）
- 429/503 按 Retry-After 有界重试，预算耗尽即失败（fail-closed，不无限等）
- 统一 UA 带联系邮箱（Crossref/OpenAlex polite pool 要求）
"""
from __future__ import annotations

import os
import time
import threading
from typing import Any, Optional

import httpx

CONTACT = os.environ.get("GOAI_EMAIL", "goai-research@example.com")
UA = f"goai-research/0.1 (mailto:{CONTACT})"

MIN_INTERVAL = float(os.environ.get("GOAI_HTTP_MIN_INTERVAL", "1.0"))  # 秒/同主机
MAX_RETRIES = int(os.environ.get("GOAI_HTTP_MAX_RETRIES", "2"))
RETRY_BUDGET = float(os.environ.get("GOAI_HTTP_RETRY_BUDGET", "45"))  # 单次请求总等待上限

_last_hit: dict[str, float] = {}
_lock = threading.Lock()


def _throttle(host: str) -> None:
    with _lock:
        prev = _last_hit.get(host, 0.0)
        wait = prev + MIN_INTERVAL - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_hit[host] = time.monotonic()


def get(url: str, params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None, timeout: float = 30.0) -> httpx.Response:
    """节流 GET；429/503 按 Retry-After 有界重试，失败抛 httpx.HTTPStatusError。"""
    merged = {"User-Agent": UA}
    if headers:
        merged.update(headers)
    waited = 0.0
    attempt = 0
    while True:
        host = httpx.URL(url).host or "unknown"
        _throttle(host)
        resp = httpx.get(url, params=params, headers=merged,
                         timeout=timeout, follow_redirects=True)
        if resp.status_code in (429, 503) and attempt < MAX_RETRIES:
            retry_after = resp.headers.get("Retry-After")
            try:
                delay = min(float(retry_after), RETRY_BUDGET - waited) if retry_after else 5.0
            except ValueError:
                delay = 5.0
            if delay <= 0 or waited + delay > RETRY_BUDGET:
                resp.raise_for_status()
            time.sleep(delay)
            waited += delay
            attempt += 1
            continue
        resp.raise_for_status()
        return resp


def get_json(url: str, params: Optional[dict[str, Any]] = None,
             headers: Optional[dict[str, str]] = None) -> Any:
    return get(url, params=params, headers=headers).json()


def download(url: str, dest_path: str, timeout: float = 120.0) -> dict[str, Any]:
    """下载文件到 dest_path，返回 {path,bytes,content_type}。非 2xx 抛异常。"""
    host = httpx.URL(url).host or "unknown"
    _throttle(host)
    with httpx.stream("GET", url, headers={"User-Agent": UA},
                      timeout=timeout, follow_redirects=True) as resp:
        resp.raise_for_status()
        ctype = resp.headers.get("content-type", "")
        n = 0
        os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_bytes():
                f.write(chunk)
                n += len(chunk)
    return {"path": dest_path, "bytes": n, "content_type": ctype}

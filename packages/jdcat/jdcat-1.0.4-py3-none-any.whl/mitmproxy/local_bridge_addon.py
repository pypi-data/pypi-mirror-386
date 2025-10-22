# -*- coding: utf-8 -*-
"""
Mitmproxy local bridge addon (minimal, non-blocking local notify + optional upload)

Features (Phase B.2 + C.1 minimal loop):
- On each captured flow (response event), immediately POST a lightweight local notify to LOCAL_NOTIFY_URL (/notify).
  Payload: { flowId, method, url, status, sessionId?, ts }
- After upload to remote ingest finishes (single or batch-like with array of one), POST a local notify with type=upload
  Payload: { flowId, uploaded: true/false, error?: string }

Notes:
- This file intentionally keeps event body small to reduce overhead.
- All local notify errors are ignored (debug print only); they must not block capture or remote ingest.
- Non-blocking by ThreadPoolExecutor to avoid mitmproxy main loop blocking.

Environment variables:
- LOCAL_NOTIFY_URL: e.g., http://127.0.0.1:17866/notify
- INGEST_URL: remote ingest endpoint (e.g., http://localhost:8008/api/traffic/ingest/batch)
- INGEST_KEY: API key for remote ingest (X-INGEST-KEY)
- SESSION_ID: optional current capture session id for tagging

Usage:
  mitmdump -s sensitive-check-local/mitmproxy/local_bridge_addon.py --ssl-insecure -p 8080
"""

import os
import json
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional
from collections import OrderedDict
import hashlib
import base64
from urllib.parse import urlsplit, parse_qsl, urlencode

# Avoid heavy deps: use standard library HTTP client
import urllib.request
import urllib.error

try:
    from mitmproxy import http  # type: ignore
except Exception:  # pragma: no cover
    http = None  # allow basic import check outside mitmproxy runtime

# optional toml reader for config toggle (py3.11+)
try:
    import tomllib as _tomli  # type: ignore
except Exception:  # pragma: no cover
    _tomli = None  # fallback to env only


# ---- Dedup configuration ----
TTL_SECONDS = int(os.getenv("DEDUP_TTL_SECONDS", "60"))
MAX_ENTRIES = int(os.getenv("DEDUP_MAX_ENTRIES", "10000"))


class DedupStore:
    """
    Per-session LRU + TTL store.
    Key: signature string (hash)
    Value: last-seen timestamp (seconds)
    """
    def __init__(self, max_entries: int = MAX_ENTRIES, ttl_seconds: int = TTL_SECONDS) -> None:
        self.max_entries = int(max_entries)
        self.ttl_seconds = int(ttl_seconds)
        self._data: "OrderedDict[str, float]" = OrderedDict()
        self._lock = threading.Lock()

    def _evict_expired_unlocked(self, now: float) -> None:
        ttl = float(self.ttl_seconds)
        # Fast path: pop from oldest while expired
        keys_to_delete = []
        for k, ts in list(self._data.items()):
            if now - ts > ttl:
                keys_to_delete.append(k)
            else:
                # OrderedDict: once we hit a fresh one, break to keep O(k) where k=expired prefix
                break
        for k in keys_to_delete:
            self._data.pop(k, None)

    def seen_or_add(self, key: str) -> bool:
        """
        Atomically check-then-record.
        Returns True if this key was seen within TTL (skip), else False and record it.
        """
        now = time.time()
        with self._lock:
            # prune expired
            self._evict_expired_unlocked(now)
            # hit?
            if key in self._data:
                ts = self._data.get(key, 0.0)
                if now - ts <= self.ttl_seconds:
                    # hit within TTL -> move to end as MRU and return hit
                    try:
                        self._data.move_to_end(key)
                    except Exception:
                        pass
                    self._data[key] = now
                    return True
                else:
                    # expired -> treat as miss, overwrite timestamp
                    try:
                        self._data.pop(key, None)
                    except Exception:
                        pass
            # capacity guard
            while len(self._data) >= self.max_entries:
                try:
                    self._data.popitem(last=False)
                except Exception:
                    break
            self._data[key] = now
            return False


def _http_post_json(url: str, data: Dict[str, Any], timeout: float = 2.0, headers: Optional[Dict[str, str]] = None) -> tuple[int, str]:
    req = urllib.request.Request(url, method="POST")
    body = json.dumps(data).encode("utf-8")
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, body, timeout=timeout) as resp:
            b = resp.read()
            body_txt = b.decode("utf-8", errors="ignore") if isinstance(b, (bytes, bytearray)) else str(b)
            return getattr(resp, "status", 200), body_txt
    except urllib.error.HTTPError as e:
        try:
            eb = e.read()
            err_txt = eb.decode("utf-8", errors="ignore") if isinstance(eb, (bytes, bytearray)) else str(eb)
        except Exception:
            err_txt = str(e)
        # propagate with status and body for observability
        raise RuntimeError(f"http {getattr(e, 'code', 500)} {err_txt}")


class LocalNotifier:
    def __init__(self) -> None:
        self.url = os.getenv("LOCAL_NOTIFY_URL", "").strip()
        self.enabled = bool(self.url)
        # small pool; minimize thread overhead
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="local-notify")

    def notify(self, event_type: str, payload: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        event = {
            "type": event_type,
            "payload": payload,
        }
        # fire-and-forget
        self.executor.submit(self._send_safe, event)

    def _send_safe(self, event: Dict[str, Any]) -> None:
        try:
            _http_post_json(self.url, event, timeout=1.5)
        except Exception as e:
            # debug only; never raise
            print(f"[local_bridge] debug: local notify failed: {e}")


class RemoteIngestUploader:
    def __init__(self) -> None:
        self.url = os.getenv("INGEST_URL", "").strip()
        self.key = os.getenv("INGEST_KEY", "").strip()
        # identity for isolation & auditing
        self.user_id = os.getenv("USER_ID", "").strip()
        self.project_id = os.getenv("PROJECT_ID", "").strip()
        self.task_id = os.getenv("TASK_ID", "").strip()
        self.enabled = bool(self.url)
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="remote-ingest")
        
        # DEBUG: Enhanced logging for configuration debugging
        try:
            masked = "yes" if self.key else "no"
            print(f"[local_bridge] ingest config url={self.url} key_set={masked} user_id={self.user_id} project_id={self.project_id} task_id={self.task_id}")
        except Exception as e:
            print(f"[DEBUG] RemoteIngestUploader.__init__: logging failed: {e}")

    def upload_async(self, dto: Dict[str, Any], flow_id: str, on_done):
        if not self.enabled:
            # simulate success=false without blocking
            def _cb():
                try:
                    on_done(flow_id, False, "INGEST_URL not set")
                except Exception as e:
                    print(f"[local_bridge] debug: on_done callback error: {e}")
            self.executor.submit(_cb)
            return
        # batch if /batch in url, else single
        is_batch = "/batch" in self.url

        def _send():
            try:
                headers = {}
                if self.key:
                    headers["X-INGEST-KEY"] = self.key
                # inject identity headers if provided
                if self.user_id:
                    headers["X-USER-ID"] = self.user_id
                if self.project_id:
                    headers["X-PROJECT-ID"] = self.project_id
                if self.task_id:
                    headers["X-TASK-ID"] = self.task_id
                payload = [dto] if is_batch else dto
                status, resp_txt = _http_post_json(self.url, payload, timeout=5.0, headers=headers)
                ok = 200 <= status < 300
                err = None if ok else f"http {status} {resp_txt[:256]}"
                on_done(flow_id, ok, err)
            except Exception as e:
                on_done(flow_id, False, str(e))

        self.executor.submit(_send)


class LocalBridgeAddon:
    def __init__(self) -> None:
        self.notifier = LocalNotifier()
        self.uploader = RemoteIngestUploader()
        self.session_id = os.getenv("SESSION_ID") or None
        self.filter_xhr_only = self._load_filter_toggle()
        # dedup toggle from env (canonicalized in API/process)
        self.dedup_enabled = str(os.getenv("DEDUP", "false")).strip().lower() in ("1", "true", "yes", "on")
        # dedup mode: how to compose signature key. options:
        # - url_no_query (default): 按URL(不含query)去重 -> host+path
        # - method_host_path: 方法+主机+路径（忽略query/body）
        # - method_host_path_query: 包含规范化后的query
        # - method_host_path_body: 包含请求体hash
        # - all: 同时包含query与body
        self.dedup_mode = (os.getenv("DEDUP_MODE", "url_no_query") or "url_no_query").strip().lower()
        # domain allowlist (comma or newline separated)
        raw_targets = os.getenv("TARGET_DOMAINS", "") or ""
        self.target_domains = self._parse_targets(raw_targets)
        # optional url regex filter
        self.filter_regex = None
        try:
            import re as _re
            regex = os.getenv("FILTER_REGEX", "")
            if regex and regex.strip():
                self.filter_regex = _re.compile(regex.strip())
        except Exception:
            self.filter_regex = None
        # per-session stores
        self._dedup_stores: Dict[str, DedupStore] = {}

        # stats for observability
        self._stat_lock = threading.Lock()
        self._stat_total = 0
        self._stat_kept_api = 0
        self._stat_filtered_static = 0

        # startup log for dedup
        try:
            print(f"[local_bridge] dedup-enabled:{str(self.dedup_enabled).lower()}, mode={getattr(self, 'dedup_mode', 'url_no_query')}, sessionId={self.session_id}")
        except Exception:
            pass

        try:
            if self.target_domains:
                print(f"[local_bridge] target_domains={self.target_domains}")
            if self.filter_regex:
                print(f"[local_bridge] filter_regex set")
        except Exception:
            pass

        self._start_stat_reporter()

    # config loader: env CAPTURE_FILTER_XHR_ONLY has priority, fallback pyproject.toml, default True
    def _load_filter_toggle(self) -> bool:
        v = os.getenv("CAPTURE_FILTER_XHR_ONLY")
        if v is not None:
            return str(v).strip().lower() not in ("0", "false", "no", "off")
        # try pyproject.toml
        try:
            if _tomli is None:
                return True
            base = os.getcwd()
            pyp = os.path.join(base, "pyproject.toml")
            if not os.path.isfile(pyp):
                # try project root one level up when running under tools dir
                parent = os.path.dirname(base)
                cand = os.path.join(parent, "pyproject.toml")
                pyp = cand if os.path.isfile(cand) else pyp
            if os.path.isfile(pyp):
                with open(pyp, "rb") as f:
                    data = _tomli.load(f)
                tool = data.get("tool", {}) if isinstance(data, dict) else {}
                sec = tool.get("sensitive_check_local", {}) if isinstance(tool, dict) else {}
                val = sec.get("capture.filter_xhr_only", True)
                return bool(val)
        except Exception:
            pass
        return True

    def _get_req_header(self, flow: "http.HTTPFlow", name: str) -> Optional[str]:  # type: ignore
        try:
            return flow.request.headers.get(name) if (flow and flow.request) else None
        except Exception:
            return None

    def _get_resp_header(self, flow: "http.HTTPFlow", name: str) -> Optional[str]:  # type: ignore
        try:
            return flow.response.headers.get(name) if (flow and flow.response) else None
        except Exception:
            return None

    def _is_api_like(self, flow: "http.HTTPFlow", method: str, url: str) -> bool:  # type: ignore
        xr = (self._get_req_header(flow, "x-requested-with") or "").lower() == "xmlhttprequest"
        sfm = (self._get_req_header(flow, "sec-fetch-mode") or "").lower()
        sfd = (self._get_req_header(flow, "sec-fetch-dest") or "").lower()
        accept = (self._get_req_header(flow, "accept") or "").lower()
        req_ct = (self._get_req_header(flow, "content-type") or "").lower()
        resp_ct = (self._get_resp_header(flow, "content-type") or "").lower()
        cond_fetch = (sfm in ("cors", "same-origin") and sfd == "empty")
        cond_accept_json = "application/json" in accept
        cond_req_json_method = (method.upper() in ("POST", "PUT", "PATCH")) and ("application/json" in req_ct)
        cond_resp_json = "application/json" in resp_ct
        # 任一命中则认为是API
        return xr or cond_fetch or cond_accept_json or cond_req_json_method or cond_resp_json

    def _is_static_by_url(self, url: str) -> bool:
        lower = (url or "").split("?")[0].lower()
        exts = (
            ".js", ".mjs", ".css", ".map",
            ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
            ".woff", ".woff2", ".ttf", ".eot", ".otf",
            ".mp4", ".webm", ".avi", ".mov",
            ".mp3", ".wav", ".flac",
            ".pdf", ".zip", ".rar", ".7z"
        )
        return any(lower.endswith(x) for x in exts)

    def _is_static_by_ct(self, ct: Optional[str]) -> bool:
        if not ct:
            return False
        ct = ct.lower()
        if ct.startswith("image/"):
            return True
        if ct.startswith("text/css"):
            return True
        if ct.startswith("application/javascript") or ct.startswith("text/javascript"):
            return True
        if ct.startswith("font/"):
            return True
        if ct.startswith("video/") or ct.startswith("audio/"):
            return True
        if ct.startswith("application/octet-stream"):
            return True
        return False

    def _should_keep(self, flow: "http.HTTPFlow", method: str, url: str) -> bool:  # type: ignore
        # 先按“过滤判定”剔除静态，再按“保留判定”兜底保留 API；若两者均不命中则丢弃
        ct = self._get_resp_header(flow, "content-type")
        is_static = self._is_static_by_url(url) or self._is_static_by_ct(ct)
        if is_static:
            return False
        keep = self._is_api_like(flow, method, url)
        return bool(keep)

    # helpers: target domains parsing and match
    def _parse_targets(self, s: str) -> list[str]:
        try:
            items = []
            for line in s.replace(",", "\n").splitlines():
                v = (line or "").strip().lower()
                if v:
                    items.append(v)
            return items
        except Exception:
            return []

    def _host_in_targets(self, host: str) -> bool:
        if not self.target_domains:
            return True
        try:
            h = (host or "").strip().lower()
            if not h:
                return False
            for pat in self.target_domains:
                # suffix match (allow subdomains)
                if h == pat or h.endswith("." + pat):
                    return True
            return False
        except Exception:
            return False

    # helpers: dedup session store + signature normalization
    def _get_store(self) -> DedupStore:
        sid = self.session_id or "default"
        s = self._dedup_stores.get(sid)
        if not s:
            s = DedupStore(MAX_ENTRIES, TTL_SECONDS)
            self._dedup_stores[sid] = s
        return s

    def _norm_query(self, query: str) -> str:
        try:
            pairs = parse_qsl(query or "", keep_blank_values=True)
            pairs.sort(key=lambda kv: (kv[0], kv[1]))
            return urlencode(pairs, doseq=True)
        except Exception:
            return ""

    def _hash_bytes(self, b: bytes) -> str:
        try:
            return hashlib.sha256(b).hexdigest()
        except Exception:
            try:
                return f"len={len(b or b'')}"
            except Exception:
                return "len=?"

    def _stable_json_dumps(self, obj: Any) -> str:
        try:
            return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        except Exception:
            return ""

    def _norm_body_hash(self, flow: "http.HTTPFlow") -> str:  # type: ignore
        try:
            req = flow.request if (flow and flow.request) else None
            if not req:
                return self._hash_bytes(b"")
            raw = getattr(req, "raw_content", None)
            if raw is None:
                try:
                    txt = req.get_text(strict=False) or ""
                    raw = txt.encode("utf-8", errors="ignore")
                except Exception:
                    raw = b""
            ct = (req.headers.get("content-type") or "").lower()
            if "application/json" in ct:
                try:
                    js = json.loads(raw.decode("utf-8", errors="ignore"))
                    s = self._stable_json_dumps(js)
                    return self._hash_bytes(s.encode("utf-8"))
                except Exception:
                    pass
            return self._hash_bytes(raw)
        except Exception:
            return self._hash_bytes(b"")

    def _make_signature_key(self, flow: "http.HTTPFlow", method: str, url: str) -> tuple[str, str, str]:  # key, METHOD, path
        try:
            parts = urlsplit(url or "")
            host = parts.netloc.lower()
            path = parts.path or "/"
            qn = self._norm_query(parts.query or "")
            m = (method or "").upper()
            bh = self._norm_body_hash(flow)
            mode = getattr(self, "dedup_mode", "url_no_query")
            if mode == "url_no_query":
                # 简化为“按URL(不含query)去重”，不考虑方法与请求体
                core = [host, path]
            elif mode == "method_host_path":
                core = [m, host, path]
            elif mode == "method_host_path_query":
                core = [m, host, path, qn]
            elif mode == "method_host_path_body":
                core = [m, host, path, bh]
            else:  # "all" 或未知 -> 最保守（包含query与body）
                core = [m, host, path, qn, bh]
            sig = "|".join(core)
            return hashlib.sha256(sig.encode("utf-8")).hexdigest(), m, path
        except Exception:
            base = f"{method}|{url}"
            return hashlib.sha256(base.encode("utf-8")).hexdigest(), (method or "").upper(), "/"

    # mitmproxy hook: called when a server response has been received
    def response(self, flow: "http.HTTPFlow") -> None:  # type: ignore
        try:
            flow_id = str(getattr(flow, "id", "")) or self._gen_flow_id()
            method = (flow.request.method if flow and flow.request else None) or ""
            url = (flow.request.pretty_url if flow and flow.request else None) or ""
            status = flow.response.status_code if (flow and flow.response) else None
            # Extract host
            try:
                host = url.split('/')[2] if '://' in url else ''
            except Exception:
                host = ''

            # 0) Apply user target domain allowlist first
            if host and not self._host_in_targets(host):
                return

            # 0.1) optional url regex filter
            if self.filter_regex is not None:
                try:
                    if not self.filter_regex.search(url or ""):
                        return
                except Exception:
                    pass

            # Ignore noisy system domains to reduce log interference (only when not in target allowlist)
            ignore_cfg = os.getenv("IGNORE_HOST_SUFFIXES", "icloud.com,apple.com,google.com,clients.google.com,gstatic.com,googleapis.com,googleusercontent.com,cdn.apple.com,itunes.apple.com").split(',')
            if host:
                h = host.strip().lower()
                # Only consider ignoring noise when current host is NOT in user target allowlist
                if not self._host_in_targets(h):
                    for suf in [s.strip().lower() for s in ignore_cfg if s.strip()]:
                        if suf and (h.endswith(suf)):
                            return
                # also skip backend ingest self-traffic
                if (h in ("aqapi.jdtest.local:8008","localhost:8008", "127.0.0.1:8008")) and ("/api/traffic/ingest" in (url or "")):
                    return
            ts_ms = int(time.time() * 1000)

            # Stats & filtering
            ct = self._get_resp_header(flow, "content-type")
            is_static = self._is_static_by_url(url) or self._is_static_by_ct(ct)
            is_api = self._is_api_like(flow, method, url)

            with self._stat_lock:
                self._stat_total += 1

            if self.filter_xhr_only:
                if is_static:
                    with self._stat_lock:
                        self._stat_filtered_static += 1
                    return  # drop static
                if not is_api:
                    # neither matched - drop
                    return
                # kept api
                with self._stat_lock:
                    self._stat_kept_api += 1
            else:
                # no-filter mode: do not drop anything, but record counters for observability
                if is_static:
                    with self._stat_lock:
                        self._stat_filtered_static += 1
                if is_api:
                    with self._stat_lock:
                        self._stat_kept_api += 1

            # Dedup check right before notify/upload
            if self.dedup_enabled:
                try:
                    sig_key, mU, pth = self._make_signature_key(flow, method, url)
                    hit = self._get_store().seen_or_add(sig_key)
                    if hit:
                        # hit -> skip further processing
                        print(f"[local_bridge] dedup-skipped key={sig_key} method={mU} path={pth}")
                        return
                    else:
                        print(f"[local_bridge] dedup-store key={sig_key} method={mU} path={pth}")
                except Exception as _e:
                    # on any error, continue without skipping
                    print(f"[local_bridge] debug: dedup error: {_e}")

            # 1) local notify: flow (non-blocking)
            self.notifier.notify(
                "flow",
                {
                    "flowId": flow_id,
                    "method": method,
                    "url": url,
                    "status": status if status is not None else -1,
                    "sessionId": self.session_id,
                    "ts": ts_ms,
                },
            )

            # 2) optional remote upload (extended dto for headers/bodies/query etc.)
            # startedAt
            started_at = None
            try:
                t0 = getattr(flow.request, "timestamp_start", None)
                if t0:
                    started_at = datetime.fromtimestamp(float(t0)).isoformat(timespec="seconds")
            except Exception:
                started_at = None

            # finishedAt for duration
            duration_ms = None
            try:
                t0 = getattr(flow.request, "timestamp_start", None)
                t1 = getattr(flow.response, "timestamp_end", None)
                if t0 and t1:
                    duration_ms = int(max(0.0, (float(t1) - float(t0)) * 1000.0))
            except Exception:
                duration_ms = None

            # URL parts
            try:
                parts = urlsplit(url or "")
                scheme = parts.scheme or None
                host = parts.hostname or (parts.netloc or None)
                port = parts.port
                path = parts.path or "/"
                query = parts.query or ""
            except Exception:
                scheme = None
                host = None
                port = None
                path = "/"
                query = ""

            # request/response headers
            def _headers_to_dict(hdrs) -> Dict[str, str]:
                try:
                    d: Dict[str, str] = {}
                    for k, v in (hdrs.items(multi=True) if hdrs is not None else []):
                        if k in d:
                            d[k] = f"{d[k]}, {v}"
                        else:
                            d[k] = v
                    return d
                except Exception:
                    try:
                        return dict(hdrs or {})
                    except Exception:
                        return {}

            req_headers: Dict[str, str] = {}
            resp_headers: Dict[str, str] = {}
            try:
                req_headers = _headers_to_dict(flow.request.headers if (flow and flow.request) else None)
            except Exception:
                req_headers = {}
            try:
                resp_headers = _headers_to_dict(flow.response.headers if (flow and flow.response) else None)
            except Exception:
                resp_headers = {}

            # request/response bodies (base64)
            def _get_raw_req() -> bytes:
                try:
                    if not (flow and flow.request):
                        return b""
                    raw = getattr(flow.request, "raw_content", None)
                    if raw is None:
                        try:
                            txt = flow.request.get_text(strict=False) or ""
                            raw = txt.encode("utf-8", errors="ignore")
                        except Exception:
                            raw = b""
                    return raw or b""
                except Exception:
                    return b""

            def _get_raw_resp() -> bytes:
                try:
                    if not (flow and flow.response):
                        return b""
                    raw = getattr(flow.response, "raw_content", None)
                    if raw is None:
                        try:
                            txt = flow.response.get_text(strict=False) or ""
                            raw = txt.encode("utf-8", errors="ignore")
                        except Exception:
                            raw = b""
                    return raw or b""
                except Exception:
                    return b""

            req_b64 = ""
            resp_b64 = ""
            try:
                rb = _get_raw_req()
                if rb:
                    req_b64 = base64.b64encode(rb).decode("ascii")
            except Exception:
                req_b64 = ""
            try:
                sb = _get_raw_resp()
                if sb:
                    resp_b64 = base64.b64encode(sb).decode("ascii")
            except Exception:
                resp_b64 = ""

            # meta (add identity hints if available)
            meta_obj: Dict[str, Any] = {
                "addon": "local_bridge_addon",
                "pid": os.getpid(),
                "session_id": self.session_id,
            }
            try:
                if getattr(self.uploader, "user_id", None):
                    meta_obj["user_id"] = self.uploader.user_id
                if getattr(self.uploader, "project_id", None):
                    meta_obj["project_id"] = self.uploader.project_id
                if getattr(self.uploader, "task_id", None):
                    meta_obj["task_id"] = self.uploader.task_id
            except Exception:
                pass

            # identity must come explicitly from environment; do not infer from captured headers to avoid silent mismatches

            # do not derive project_id from URL query; require explicit environment or /start body

            # Convert query string to JSON format if it exists
            query_json = ""
            if query:
                try:
                    # Parse query string into dict and convert to JSON
                    query_dict = dict(parse_qsl(query, keep_blank_values=True))
                    query_json = json.dumps(query_dict, ensure_ascii=False, separators=(",", ":"))
                except Exception:
                    query_json = ""

            dto: Dict[str, Any] = {
                "flowId": flow_id,
                "startedAt": started_at or datetime.now().isoformat(timespec="seconds"),
                "method": method,
                "url": url,
                "scheme": scheme,
                "host": host,
                "port": port,
                "path": path,
                "query": query_json,  # send as JSON string
                # legacy + current
                "status": status,
                "responseStatus": status,
                "durationMs": duration_ms,
                # headers/bodies
                "requestHeaders": req_headers,
                "requestBody": req_b64,          # send base64 with key expected by DTO
                "responseHeaders": resp_headers,
                "responseBody": resp_b64,        # send base64 with key expected by DTO
                # misc
                "tags": ["mitmproxy", "local"],
                "meta": meta_obj,
            }

            def _on_done(fid: str, uploaded: bool, error: Optional[str]):
                # local notify: upload result
                self.notifier.notify(
                    "upload",
                    {
                        "flowId": fid,
                        "uploaded": bool(uploaded),
                        **({"error": error} if error else {}),
                    },
                )

            # fire-and-forget upload
            self.uploader.upload_async(dto, flow_id, _on_done)

        except Exception as e:
            # never break mitmproxy flow
            print(f"[local_bridge] debug: addon error: {e}")

    @staticmethod
    def _gen_flow_id() -> str:
        # fallback in case mitmproxy flow.id is missing
        return f"f-{int(time.time() * 1000)}-{os.getpid()}"

    def _start_stat_reporter(self) -> None:
        def _loop():
            while True:
                time.sleep(30.0)
                try:
                    with self._stat_lock:
                        total = self._stat_total
                        kept = self._stat_kept_api
                        filtered = self._stat_filtered_static
                        # reset window
                        self._stat_total = 0
                        self._stat_kept_api = 0
                        self._stat_filtered_static = 0
                    # INFO级简要计数日志（非敏感）
                    print(f"[local_bridge][stats] window=30s total_flows={total} kept_api={kept} filtered_static={filtered} xhr_only={self.filter_xhr_only}")
                except Exception as e:
                    print(f"[local_bridge] debug: stat reporter error: {e}")
        t = threading.Thread(target=_loop, name="stats-reporter", daemon=True)
        t.start()


# Register addon
addons = [LocalBridgeAddon()]
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
import asyncio
import shutil
import platform

from . import __version__
from . import process
from . import events
from . import proxy_macos
from .config import load_config
from .backend_client import BackendAPIError, build_backend_api_from_context
from .packaging_utils import find_mitmdump_executable

# added: logging & forwarding deps
import os
import json
import logging
import time
from urllib import request as _urlreq, error as _urlerr

app = FastAPI(title="sensitive-check-local", version=__version__)

# In-memory snapshot for macOS system proxy to allow rollback on /stop or failure during /start
_proxy_snapshot: Dict[str, Any] | None = None
_proxy_services: list[str] | None = None
_proxy_enabled: bool = False

# CORS: allow any origin for Stage A to enable remote frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# added: logger & forwarding config
_logger = logging.getLogger("sensitive_check_local")
if not _logger.handlers:
    _logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setLevel(logging.INFO)
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))
    _logger.addHandler(_h)

_BACKEND_INGEST_URL = os.getenv("BACKEND_INGEST_URL", "http://aqapi.jdtest.local:8008/api/traffic/ingest")
# 默认关闭转发；仅 FORWARD_TO_BACKEND=true 时开启
_FORWARD_TO_BACKEND = os.getenv("FORWARD_TO_BACKEND", "false").lower() in ("1", "true", "yes", "on")
_FORWARD_LOG_BODY_MAX = int(os.getenv("FORWARD_LOG_BODY_MAX", "1024"))
_INGEST_TIMEOUT = float(os.getenv("INGEST_TIMEOUT", "5.0"))

_logger.info("[local-config] forwarding=%s target=%s timeout=%ss", _FORWARD_TO_BACKEND, _BACKEND_INGEST_URL, _INGEST_TIMEOUT)


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"ok": True, "version": __version__}

# 查看当前转发配置，便于排障
@app.get("/forwarding")
async def forwarding() -> Dict[str, Any]:
    return {
        "forwardToBackend": _FORWARD_TO_BACKEND,
        "backendIngestUrl": _BACKEND_INGEST_URL,
        "timeoutSec": _INGEST_TIMEOUT,
        "logBodyMax": _FORWARD_LOG_BODY_MAX,
    }


def _status_payload(state: Dict[str, Any]) -> Dict[str, Any]:
    extra = events.get_status_fields()
    return {
        "running": bool(state.get("running")),
        "port": state.get("port"),
        "sessionId": state.get("sessionId"),
        "lastError": state.get("lastError"),
        "proxyEnabled": bool(state.get("proxyEnabled", False)),
        "pendingCount": int(extra.get("pendingCount", 0)),
        "lastEventTs": extra.get("lastEventTs"),
        # optional but useful for debugging
        "dedupEnabled": bool(state.get("dedupEnabled", False)),
    }


@app.get("/status")
async def status() -> Dict[str, Any]:
    state = process.status()
    return _status_payload(state)


@app.get("/events")
async def events_stream():
    q = await events.subscribe()

    async def gen():
        try:
            while True:
                data = await q.get()
                yield f"data: {data}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            events.unsubscribe(q)

    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)

# added: helpers for forwarding to backend ingest
def _truncate(s: str, n: int) -> str:
    try:
        return s if len(s) <= n else s[:n] + "..."
    except Exception:
        return s

def _post_json_blocking(url: str, payload_str: str, timeout: float, headers: dict | None = None) -> tuple[int, str]:
    # merge default json header with custom headers
    _headers = {"Content-Type": "application/json"}
    try:
        if headers:
            _headers.update({str(k): str(v) for k, v in headers.items() if str(k).strip() and str(v).strip()})
    except Exception:
        pass
    req = _urlreq.Request(url=url, data=payload_str.encode("utf-8"), headers=_headers, method="POST")
    try:
        with _urlreq.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            body = resp.read()
            body_txt = body.decode("utf-8", errors="ignore") if isinstance(body, (bytes, bytearray)) else str(body)
            return status, body_txt
    except _urlerr.HTTPError as e:
        try:
            b = e.read()
            body_txt = b.decode("utf-8", errors="ignore") if isinstance(b, (bytes, bytearray)) else str(b)
        except Exception:
            body_txt = str(e)
        return int(getattr(e, "code", 500) or 500), body_txt
    except Exception as e:
        return 599, str(e)

async def _forward_ingest(body: dict):
    if not _FORWARD_TO_BACKEND:
        return
    try:
        # Only forward when capture is running; otherwise skip to avoid startup noise
        state = process.status()
        if not bool(state.get("running")):
            _logger.info("[local-forward] skipped: capture not running")
            return

        # avoid echo/loop: do not forward backend ingest flows themselves
        try:
            url_raw = str(body.get("url") or body.get("requestUrl") or "")
            if url_raw and url_raw.startswith(_BACKEND_INGEST_URL):
                _logger.info("[local-forward] skipped: backend ingest url")
                return
        except Exception:
            pass

        # best-effort mapping
        dto = {
            "flowId": body.get("flowId") or body.get("id") or f"local-{int(time.time()*1000)}",
            "startedAt": body.get("startedAt") or body.get("ts") or time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "method": body.get("method") or "GET",
            "url": body.get("url") or body.get("requestUrl") or "http://aqapi.jdtest.local/",
            "responseStatus": body.get("responseStatus") or body.get("status") or 200,
            "durationMs": body.get("durationMs") or 0,
            "requestHeaders": body.get("requestHeaders") or {},
            "responseHeaders": body.get("responseHeaders") or {},
            "requestBodyBase64": body.get("requestBodyBase64") or "",
            "responseBodyBase64": body.get("responseBodyBase64") or "",
            "meta": body.get("meta") or {},
        }
        # ensure session_id present if provided as sessionId at top-level
        if "session_id" not in dto["meta"]:
            sid = body.get("session_id") or body.get("sessionId")
            if sid:
                dto["meta"]["session_id"] = sid

        payload_str = json.dumps(dto, ensure_ascii=False)

        # Inject headers for backend auth & isolation (align with addon)
        headers: dict[str, str] = {}
        try:
            ingest_key = os.getenv("INGEST_KEY", "").strip()
            user_id = os.getenv("USER_ID", "").strip()
            project_id = os.getenv("PROJECT_ID", "").strip()
            task_id = os.getenv("TASK_ID", "").strip()
            if ingest_key:
                headers["X-INGEST-KEY"] = ingest_key
            if user_id:
                headers["X-USER-ID"] = user_id
            if project_id:
                headers["X-PROJECT-ID"] = project_id
            if task_id:
                headers["X-TASK-ID"] = task_id
        except Exception:
            pass

        loop = asyncio.get_running_loop()
        status, resp_txt = await loop.run_in_executor(
            None, _post_json_blocking, _BACKEND_INGEST_URL, payload_str, _INGEST_TIMEOUT, headers
        )
        _logger.info("[local-forward] url=%s status=%s resp=%s", _BACKEND_INGEST_URL, status, _truncate(resp_txt, _FORWARD_LOG_BODY_MAX))
    except Exception as e:
        _logger.error("[local-forward] failed: %s", e, exc_info=False)


@app.post("/notify")
async def notify(req: Request) -> Dict[str, Any]:
    try:
        body = await req.json()
        if not isinstance(body, dict):
            body = {}
    except Exception:
        body = {}

    # logging for visibility
    try:
        keys = list(body.keys())
        preview = _truncate(json.dumps(body) if isinstance(body, dict) else str(body), _FORWARD_LOG_BODY_MAX)
        _logger.info("[local-notify] keys=%s size=%s preview=%s", keys, len(preview), preview)
    except Exception:
        pass

    # Broadcast first, then apply event to counters
    await events.broadcast(body)
    events.apply_event(body)

    # forward to backend (best-effort, async)
    try:
        asyncio.create_task(_forward_ingest(body))
    except Exception:
        pass

    return {"ok": True}

@app.post("/start")
async def start(req: Request) -> Dict[str, Any]:
    global _proxy_snapshot, _proxy_services, _proxy_enabled
    try:
        body = await req.json()
        if not isinstance(body, dict):
            body = {}
    except Exception:
        body = {}
    # Normalize dedup toggle from compatible fields; persist as 'deduplicate'
    try:
        dedup_bool = bool(body.get("deduplicate") or body.get("enableDedup") or body.get("dedup"))
        body["deduplicate"] = dedup_bool
    except Exception:
        dedup_bool = False

    # Fail-fast validation: identity and ingest configuration
    try:
        merged_cfg = load_config()
    except Exception:
        merged_cfg = {}

    user_id = body.get("userId")
    if user_id is None:
        user_id = merged_cfg.get("user_id")
    project_id = body.get("projectId")
    if project_id is None:
        project_id = merged_cfg.get("project_id")
    task_id = body.get("taskId")
    if task_id is None:
        task_id = merged_cfg.get("task_id")

    # Required: userId, projectId(允许0=个人空间), taskId（严格要求；缺失即中断并提示）
    missing_fields: list[str] = []
    if not user_id:
        missing_fields.append("userId")
    # projectId 必须提供；允许为0表示“个人空间”，仅禁止负数或缺失/空字符串
    try:
        pid_int = int(project_id) if project_id is not None and str(project_id).strip() != "" else None
    except Exception:
        pid_int = None
    if pid_int is None or pid_int < 0:
        missing_fields.append("projectId")
    # taskId 必须存在（由前端/后端预创建任务后传入）
    if not task_id or str(task_id).strip() == "":
        missing_fields.append("taskId")
    if missing_fields:
        return {
            "ok": False,
            "error": f"missing required fields: {', '.join(missing_fields)}. Provide in /start body or config.yaml",
            "running": False,
            "proxyEnabled": False,
        }

    # export identity to API process env for forwarding header injection
    try:
        os.environ["USER_ID"] = str(user_id)
        os.environ["PROJECT_ID"] = str(project_id)
        os.environ["TASK_ID"] = str(task_id)
    except Exception:
        pass
    ingest_url_present = bool(body.get("ingestUrl") or merged_cfg.get("ingest_url"))
    if (not _FORWARD_TO_BACKEND) and (not ingest_url_present):
        return {
            "ok": False,
            "error": "ingest not configured: provide ingestUrl in body/config or set FORWARD_TO_BACKEND=true with BACKEND_INGEST_URL",
            "running": False,
            "proxyEnabled": False,
        }

    # Step 1: preflight check for mitmdump using enhanced finder
    mitmdump_path = find_mitmdump_executable()
    if not mitmdump_path:
        return {"ok": False, "error": "mitmdump not found. Please install mitmproxy (pip install mitmproxy or brew install mitmproxy)."}

    # Prepare vars
    bypass_domains = body.get("bypassDomains") or []
    if not isinstance(bypass_domains, list):
        bypass_domains = []
    _proxy_snapshot = None
    _proxy_services = None
    _proxy_enabled = False

    # Step 2: take proxy snapshot on macOS (Darwin) before starting
    is_darwin = platform.system() == "Darwin"
    if is_darwin:
        try:
            services = proxy_macos.detect_services()
            snap = proxy_macos.snapshot_proxy_state(services)
            _proxy_services = services
            _proxy_snapshot = snap
        except getattr(proxy_macos, "NoActiveNetworkServices", Exception):
            # No active network services -> fail fast with clear message
            msg = "未检测到可用网络服务，请在系统设置启用 Wi‑Fi 或有线网络后重试"
            process.set_proxy_enabled(False)
            if hasattr(process, "set_last_error"):
                process.set_last_error(msg)
            return {
                "ok": False,
                "error": msg,
                "running": False,
                "proxyEnabled": False,
            }
        except Exception:
            # Snapshot failed for other reasons: continue in no-proxy mode
            _proxy_services = None
            _proxy_snapshot = None

    # Step 3: start mitmdump process
    res = process.start(body)
    # Log dedup-enabled with sessionId for debugging
    try:
        sid = res.get("sessionId") or process.status().get("sessionId") or body.get("sessionId")
        _logger.info("dedup-enabled:%s, sessionId=%s", "true" if dedup_bool else "false", sid)
    except Exception:
        pass
    if not bool(res.get("ok", True)):
        # Failure: rollback proxy if we changed (we haven't yet), nothing to stop here besides state
        # Just ensure proxyEnabled false
        err_msg = res.get("error") or "failed to start mitmdump"
        process.set_proxy_enabled(False)
        if hasattr(process, "set_last_error"):
            process.set_last_error(err_msg)
        return {
            "ok": False,
            "error": err_msg,
            "running": False,
            "proxyEnabled": False,
        }

    # Step 4: enable system proxy on macOS; other platforms degrade gracefully
    port = res.get("port")
    if is_darwin and isinstance(port, int) and port:
        try:
            services = _proxy_services or proxy_macos.detect_services()
            proxy_macos.enable_system_proxy(services, port, bypass_domains)
            _proxy_enabled = True
            process.set_proxy_enabled(True)
            if hasattr(process, "set_last_error"):
                process.set_last_error(None)
        except Exception as e:
            # Enable proxy failed: stop mitmdump and restore snapshot
            _logger.error("[start] 代理启用失败，开始清理: %s", str(e))
            
            try:
                _logger.info("[start] 停止 mitmdump 进程...")
                process.stop()
                _logger.info("[start] mitmdump 进程已停止")
            except Exception as stop_err:
                _logger.error("[start] 停止 mitmdump 失败: %s", stop_err)
                
            # Restore if snapshot exists
            try:
                if _proxy_snapshot:
                    _logger.info("[start] 恢复代理设置快照...")
                    proxy_macos.restore_proxy_state(_proxy_snapshot)
                    _logger.info("[start] 代理设置已恢复")
                else:
                    _logger.info("[start] 无代理快照需要恢复")
            except Exception as restore_err:
                _logger.error("[start] 恢复代理设置失败: %s", restore_err)
                
            _proxy_enabled = False
            process.set_proxy_enabled(False)
            err_text = str(e)
            if hasattr(process, "set_last_error"):
                process.set_last_error(err_text)
            
            _logger.error("[start] 最终状态: running=False, proxyEnabled=False, error=%s", err_text)
            
            # 特殊处理用户取消的情况，提供更友好的错误信息
            user_friendly_error = err_text
            if "用户已取消" in err_text or "User canceled" in err_text:
                user_friendly_error = "用户取消了管理员权限验证，代理未启用。请重新尝试并在弹窗中点击'允许'。"
            
            # Return the aggregated error from enable_system_proxy when available
            return {
                "ok": False,
                "error": user_friendly_error,
                "running": False,
                "proxyEnabled": False,
                "userCanceled": "用户已取消" in err_text or "User canceled" in err_text,
            }
    else:
        # Non-Darwin or invalid port: run without touching system proxy
        _proxy_enabled = False
        process.set_proxy_enabled(False)
        # 成功启动后清空 lastError（即便未改系统代理）
        if hasattr(process, "set_last_error"):
            process.set_last_error(None)

    return {
        "ok": True,
        "sessionId": res.get("sessionId"),
        "running": True,
        "port": res.get("port"),
        "proxyEnabled": _proxy_enabled,
        "lastError": None if _proxy_enabled or not is_darwin else process.status().get("lastError"),
    }


@app.post("/stop")
async def stop() -> Dict[str, Any]:
    global _proxy_snapshot, _proxy_services, _proxy_enabled
    # Always try to stop mitmdump
    res = process.stop()
    # Always attempt to restore proxy snapshot on macOS, even if process already exited (idempotent)
    if platform.system() == "Darwin":
        try:
            if _proxy_snapshot:
                proxy_macos.restore_proxy_state(_proxy_snapshot)
        except Exception:
            # best-effort restore
            pass
    # Reset in-memory flags
    _proxy_snapshot = None
    _proxy_services = None
    _proxy_enabled = False
    process.set_proxy_enabled(False)
    return {"ok": True, "running": False, "proxyEnabled": False}
# ============================================================================
# 越权测试相关接口（新增）
# ============================================================================

# 内存态上下文与任务状态（越权测试专用）
_permission_context_mem: Dict[str, Any] = {}  # 结构：{project_id, user_id, task_id, client_id, started_at, state}
_permission_running_task_id: Optional[str] = None
_permission_completed_tasks: Dict[str, str] = {}  # task_id -> "success"|"failed"
_permission_lock = asyncio.Lock()  # 控制并发：全局仅允许一个执行中的 task

# 路径设定（允许环境变量覆盖）
def _permission_client_id_path() -> str:
    default_path = os.path.expanduser("~/.sensitive-check/client_id")
    return os.environ.get("SENSITIVE_LOCAL_CLIENT_ID_PATH", default_path)

def _permission_context_path() -> str:
    default_path = os.path.expanduser("~/.sensitive-check/context.json")
    return os.environ.get("SENSITIVE_LOCAL_CONTEXT_PATH", default_path)

def _permission_load_or_create_client_id() -> str:
    path = _permission_client_id_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                client_id = f.read().strip()
                if client_id:
                    return client_id
    except Exception:
        pass
    
    # 生成新的 client_id
    import uuid
    client_id = str(uuid.uuid4())
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(client_id)
    except Exception:
        pass
    return client_id

def _permission_load_context() -> Dict[str, Any]:
    path = _permission_context_path()
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.loads(f.read())
    except Exception:
        pass
    return {}

def _permission_save_context(ctx: Dict[str, Any]) -> None:
    path = _permission_context_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ctx, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _permission_extract_headers(request: Request) -> tuple[str, str]:
    """
    从请求头提取 Project-Id、User-Id（严格不做 Body 兜底）
    返回：(project_id, user_id)
    """
    project_id = ""
    user_id = ""
    
    # 支持多种 Header 键名
    for key in ["Project-Id", "Project-ID", "X-Project-Id", "projectId"]:
        if key in request.headers:
            project_id = request.headers[key].strip()
            break
    
    for key in ["User-Id", "User-ID", "X-User-Id", "userId"]:
        if key in request.headers:
            user_id = request.headers[key].strip()
            break
    
    return project_id, user_id

@app.post("/local/context/bind")
async def permission_context_bind(request: Request) -> Dict[str, Any]:
    """
    绑定上下文：POST /local/context/bind
    Headers: Project-Id、User-Id
    Body: { "task_id": "..." }
    """
    global _permission_context_mem
    
    _logger.info("[permission-bind] 开始绑定越权测试上下文")
    
    # 严格从 Headers 读取，不做 Body 兜底
    project_id, user_id = _permission_extract_headers(request)
    _logger.info(f"[permission-bind] 提取Headers: project_id={project_id}, user_id={user_id[:6] if user_id else 'None'}***")
    
    if not project_id or not user_id:
        _logger.error("[permission-bind] 缺少必要的Headers: Project-Id 和 User-Id")
        raise HTTPException(
            status_code=400,
            detail="Missing required headers: Project-Id and User-Id"
        )
    
    try:
        body = await request.json()
        task_id = str(body.get("task_id", "")).strip()
        _logger.info(f"[permission-bind] 解析请求体: task_id={task_id}")
        if not task_id:
            _logger.error("[permission-bind] 请求体中缺少task_id")
            raise HTTPException(status_code=400, detail="Missing task_id in request body")
    except Exception as e:
        _logger.error(f"[permission-bind] 解析请求体失败: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {e}")
    
    # 生成/获取 client_id
    client_id = _permission_load_or_create_client_id()
    _logger.info(f"[permission-bind] 获取客户端ID: client_id={client_id[:8]}***")
    
    # 更新内存上下文
    _permission_context_mem = {
        "project_id": project_id,
        "user_id": user_id,
        "task_id": task_id,
        "client_id": client_id,
        "started_at": int(time.time()),
        "state": "bound"
    }
    
    # 持久化上下文
    _permission_save_context(_permission_context_mem)
    _logger.info("[permission-bind] 上下文已持久化到文件")
    
    _logger.info(f"[permission-bind] ✅ 上下文绑定成功: task_id={task_id} project_id={project_id} user_id={user_id[:6]}*** client_id={client_id[:8]}***")
    
    return {"success": True}

@app.post("/local/tasks/start")
async def permission_task_start(request: Request) -> Dict[str, Any]:
    """
    启动执行：POST /local/tasks/start
    Headers: Project-Id、User-Id
    Body: { "task_id": "..." }
    """
    global _permission_running_task_id, _permission_completed_tasks
    
    _logger.info("[permission-start] 🚀 开始启动越权测试任务")
    
    async with _permission_lock:
        # 验证 Headers
        project_id, user_id = _permission_extract_headers(request)
        _logger.info(f"[permission-start] 验证Headers: project_id={project_id}, user_id={user_id[:6] if user_id else 'None'}***")
        
        if not project_id or not user_id:
            _logger.error("[permission-start] ❌ 缺少必要的Headers")
            raise HTTPException(
                status_code=400,
                detail="Missing required headers: Project-Id and User-Id"
            )
        
        try:
            body = await request.json()
            task_id = str(body.get("task_id", "")).strip()
            _logger.info(f"[permission-start] 解析任务ID: task_id={task_id}")
            if not task_id:
                _logger.error("[permission-start] ❌ 缺少task_id")
                raise HTTPException(status_code=400, detail="Missing task_id in request body")
        except Exception as e:
            _logger.error(f"[permission-start] ❌ 解析请求体失败: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON body: {e}")
        
        # 验证上下文一致性
        _logger.info(f"[permission-start] 验证上下文一致性...")
        _logger.info(f"[permission-start] 内存上下文: project_id={_permission_context_mem.get('project_id')}, user_id={_permission_context_mem.get('user_id')}, task_id={_permission_context_mem.get('task_id')}")
        
        if (_permission_context_mem.get("project_id") != project_id or
            _permission_context_mem.get("user_id") != user_id or
            _permission_context_mem.get("task_id") != task_id):
            _logger.error("[permission-start] ❌ 上下文不匹配，需要先调用/local/context/bind")
            raise HTTPException(
                status_code=400,
                detail="Context mismatch. Please call /local/context/bind first"
            )
        
        _logger.info("[permission-start] ✅ 上下文验证通过")
        
        # 检查是否已完成
        if task_id in _permission_completed_tasks:
            status = _permission_completed_tasks[task_id]
            _logger.info(f"[permission-start] ⚠️ 任务已完成: task_id={task_id}, status={status}")
            return {
                "success": True,
                "started": False,
                "message": f"already completed: status={status}"
            }
        
        # 检查是否正在运行
        if _permission_running_task_id == task_id:
            _logger.info(f"[permission-start] ⚠️ 任务已在运行: task_id={task_id}")
            return {
                "success": True,
                "started": False,
                "message": "already running"
            }
        
        # 检查是否有其他任务在运行
        if _permission_running_task_id is not None:
            _logger.warning(f"[permission-start] ⚠️ 其他任务正在运行: current={_permission_running_task_id}, requested={task_id}")
            return {
                "success": True,
                "started": False,
                "message": f"another task running: {_permission_running_task_id}"
            }
        
        # 标记为运行中
        _permission_running_task_id = task_id
        _logger.info(f"[permission-start] 📝 标记任务为运行中: task_id={task_id}")
        
        # 启动后台执行器
        _logger.info(f"[permission-start] 🔄 启动后台执行器...")
        asyncio.create_task(_permission_execute_task(task_id))
        
        _logger.info(f"[permission-start] ✅ 任务启动成功: task_id={task_id}")
        
        return {
            "success": True,
            "started": True,
            "message": "started"
        }

async def _permission_execute_task(task_id: str) -> None:
    """
    后台执行越权测试任务
    """
    global _permission_running_task_id, _permission_completed_tasks, _permission_context_mem
    
    try:
        _logger.info(f"[permission-execute] 🔥 开始执行越权测试任务: task_id={task_id}")
        _logger.info(f"[permission-execute] 当前上下文: {_permission_context_mem}")
        
        # 从 process 模块调用执行器
        _logger.info(f"[permission-execute] 调用process.run_permission_task...")
        success = await process.run_permission_task(_permission_context_mem.copy())
        
        # 标记完成状态
        status = "success" if success else "failed"
        _permission_completed_tasks[task_id] = status
        _logger.info(f"[permission-execute] ✅ 任务执行完成: task_id={task_id}, success={success}, status={status}")
        
    except Exception as e:
        _logger.error(f"[permission-execute] ❌ 任务执行异常: task_id={task_id}, error={e}", exc_info=True)
        _permission_completed_tasks[task_id] = "failed"
        
    finally:
        _logger.info(f"[permission-execute] 🧹 开始清理任务状态: task_id={task_id}")
        
        # 清理运行状态
        if _permission_running_task_id == task_id:
            _permission_running_task_id = None
            _logger.info(f"[permission-execute] 清除运行中任务ID: {task_id}")
        
        # 基础上下文清理（保留 client_id，清理 task_id）
        if _permission_context_mem.get("task_id") == task_id:
            _permission_context_mem.pop("task_id", None)
            _permission_context_mem["state"] = "completed"
            _permission_save_context(_permission_context_mem)
            _logger.info(f"[permission-execute] 上下文已更新为completed状态")
        
        _logger.info(f"[permission-execute] 🏁 任务执行流程结束: task_id={task_id}")
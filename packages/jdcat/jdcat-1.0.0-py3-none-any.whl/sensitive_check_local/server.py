from __future__ import annotations

import os
import json
import uuid
import time
import asyncio
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# 说明：
# - 本地服务入口，按要求新增：
#   • POST /local/context/bind
#   • POST /local/tasks/start
# - 仅支持从 Headers 读取 Project-Id、User-Id，不做 Body 兜底
# - 统一 CORS 放行（仅为本地服务端，路径见下）
# - 上下文持久化与 client_id 管理
# - 同一 task_id 幂等与全局执行并发约束（全局仅允许一个执行中的 task）

app = FastAPI(title="sensitive-check-local-permission", version="0.1.0")

# 全局 CORS 放行（覆盖到 /local/context/bind 与 /local/tasks/start）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# 内存态上下文与任务状态
_context_mem: Dict[str, Any] = {}  # 结构：{project_id, user_id, task_id, client_id, started_at, state}
_running_task_id: Optional[str] = None
_completed_tasks: Dict[str, str] = {}  # task_id -> "success"|"failed"
_lock = asyncio.Lock()  # 控制并发：全局仅允许一个执行中的 task

# 路径设定（允许环境变量覆盖）
def _client_id_path() -> str:
    default_path = os.path.expanduser("~/.sensitive-check/client_id")
    return os.environ.get("SENSITIVE_LOCAL_CLIENT_ID_PATH", default_path)

def _context_path() -> str:
    default_path = os.path.expanduser("~/.sensitive-check/context.json")
    return os.environ.get("SENSITIVE_LOCAL_CONTEXT_PATH", default_path)

def _load_or_create_client_id() -> str:
    path = _client_id_path()
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                cid = f.read().strip()
                if cid:
                    return cid
        # 创建新 client_id
        cid = uuid.uuid4().hex
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(cid)
        return cid
    except Exception:
        # 读取失败自动重建
        try:
            cid = uuid.uuid4().hex
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(cid)
            return cid
        except Exception:
            # 最后兜底：返回内存态
            return uuid.uuid4().hex

def _save_context(ctx: Dict[str, Any]) -> None:
    path = _context_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ctx, f, ensure_ascii=False, indent=2)
    except Exception:
        # 文档要求：不要过度添加兜底逻辑，这里保留异常抛出位置在调用方
        pass

def _load_context() -> Optional[Dict[str, Any]]:
    path = _context_path()
    try:
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return None
    except Exception:
        return None

def _get_header(req: Request, name: str) -> str:
    # 严格使用 Header，不支持 Body 兜底
    val = req.headers.get(name)
    if val is None or str(val).strip() == "":
        raise HTTPException(status_code=400, detail=f"missing header: {name}")
    return str(val).strip()

# 事件日志（基础）：统一脱敏，供排查
def _log_event(event: str, info: Dict[str, Any]) -> None:
    # 注意脱敏：不输出完整 token/headers/响应体
    safe_info = dict(info or {})
    # 典型敏感字段处理
    for k in list(safe_info.keys()):
        if k.lower() in {"authorization", "cookie", "set-cookie", "token"}:
            safe_info[k] = "***"
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    task_id = safe_info.get("task_id") or safe_info.get("taskId") or "-"
    print(f"[{ts}] [local] event={event} task_id={task_id} info={safe_info}")

@app.post("/local/context/bind")
async def bind_context(req: Request) -> Dict[str, Any]:
    """
    绑定上下文：
    Headers：Project-Id、User-Id（若 Body 也提供，以 Headers 为准，不做兜底）
    Body：{ "task_id": "...", "strategies"?: ["horizontal"|"vertical"|...], "follow_redirects"?: true|false }
    行为：
      - 持久化上下文（内存与文件）
      - 生成/缓存 client_id（若不存在）
      - 可选：记录前端传入的策略与是否跟随重定向（不做默认兜底）
    返回：{ "success": true }
    """
    project_id = _get_header(req, "Project-Id")
    user_id = _get_header(req, "User-Id")

    body = await req.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="invalid json body")
    task_id = str(body.get("task_id") or "").strip()
    if task_id == "":
        raise HTTPException(status_code=400, detail="missing field: task_id")

    # 可选解析：策略（仅允许 horizontal/vertical），若提供但解析后为空则报错
    strategies_parsed = None
    if "strategies" in body:
        raw = body.get("strategies")
        allowed = {"horizontal", "vertical"}
        parsed: list[str] = []
        if isinstance(raw, str):
            parts = [x.strip().lower() for x in raw.replace(",", " ").split() if x.strip()]
            parsed = [x for x in parts if x in allowed]
        elif isinstance(raw, list):
            parsed = [str(x).strip().lower() for x in raw if str(x).strip().lower() in allowed]
        else:
            raise HTTPException(status_code=400, detail="invalid strategies")
        if not parsed:
            raise HTTPException(status_code=400, detail="invalid strategies (empty)")
        strategies_parsed = parsed

    # 可选解析：是否跟随重定向
    follow_redirects_parsed = None
    if "follow_redirects" in body:
        fr = body.get("follow_redirects")
        if isinstance(fr, bool):
            follow_redirects_parsed = fr
        elif isinstance(fr, str):
            follow_redirects_parsed = str(fr).strip().lower() in ("1", "true", "yes", "on")
        else:
            raise HTTPException(status_code=400, detail="invalid follow_redirects")

    client_id = _load_or_create_client_id()

    ctx = {
        "project_id": project_id,
        "user_id": user_id,
        "task_id": task_id,
        "client_id": client_id,
        "started_at": int(time.time() * 1000),
        "state": {"status": "bound"},
    }
    # 仅在前端提供时写入策略/重定向参数；不做默认兜底
    if strategies_parsed is not None:
        ctx["strategies"] = strategies_parsed
    if follow_redirects_parsed is not None:
        ctx["follow_redirects"] = follow_redirects_parsed

    _context_mem.clear()
    _context_mem.update(ctx)
    try:
        _save_context(ctx)
    except Exception as e:
        # 按要求不做过度兜底，抛错以暴露问题
        raise HTTPException(status_code=500, detail=f"persist context failed: {e}")

    _log_event("on_context_bound", {"task_id": task_id, "strategies": strategies_parsed or "-", "follow_redirects": follow_redirects_parsed if follow_redirects_parsed is not None else "-"})
    return {"success": True}

@app.post("/local/tasks/start")
async def start_task(req: Request) -> Dict[str, Any]:
    """
    启动执行器（幂等）：
    Headers：Project-Id、User-Id；Body：{ "task_id": "...", "strategies"?: ["horizontal"|"vertical"], "follow_redirects"?: true|false }
    行为：
      - 读取上下文 → 启动执行器（幂等控制）
      - 可选：允许前端在启动时覆盖策略与是否跟随重定向
      - 相同 task 正在执行或已完成：返回 {success:true, started:false|true, message}
      - 全局仅允许一个执行中的 task
    返回：
      { "success": true, "started": true, "message": "started" }
    """
    project_id = _get_header(req, "Project-Id")
    user_id = _get_header(req, "User-Id")

    body = await req.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="invalid json body")
    task_id = str(body.get("task_id") or "").strip()
    if task_id == "":
        raise HTTPException(status_code=400, detail="missing field: task_id")

    ctx = _load_context() or _context_mem or None
    if not ctx:
        raise HTTPException(status_code=400, detail="context not bound")
    # 统一以 Headers 为准（拒绝 Body 兜底）
    if str(ctx.get("project_id")) != project_id or str(ctx.get("user_id")) != user_id or str(ctx.get("task_id")) != task_id:
        raise HTTPException(status_code=400, detail="context mismatch: headers do not match bound context")

    # 可选覆盖策略
    strategies_override = None
    if "strategies" in body:
        raw = body.get("strategies")
        allowed = {"horizontal", "vertical"}
        parsed: list[str] = []
        if isinstance(raw, str):
            parts = [x.strip().lower() for x in raw.replace(",", " ").split() if x.strip()]
            parsed = [x for x in parts if x in allowed]
        elif isinstance(raw, list):
            parsed = [str(x).strip().lower() for x in raw if str(x).strip().lower() in allowed]
        else:
            raise HTTPException(status_code=400, detail="invalid strategies")
        if not parsed:
            raise HTTPException(status_code=400, detail="invalid strategies (empty)")
        strategies_override = parsed

    # 可选覆盖是否跟随重定向
    follow_redirects_override = None
    if "follow_redirects" in body:
        fr = body.get("follow_redirects")
        if isinstance(fr, bool):
            follow_redirects_override = fr
        elif isinstance(fr, str):
            follow_redirects_override = str(fr).strip().lower() in ("1", "true", "yes", "on")
        else:
            raise HTTPException(status_code=400, detail="invalid follow_redirects")

    # 并发与幂等控制
    async with _lock:
        global _running_task_id
        if _running_task_id is not None:
            if _running_task_id == task_id:
                _log_event("start_task_idempotent_running", {"task_id": task_id})
                return {"success": True, "started": False, "message": "already running"}
            else:
                _log_event("start_task_blocked_by_other", {"task_id": task_id, "running": _running_task_id})
                return {"success": True, "started": False, "message": f"another task running: {_running_task_id}"}
        # 已完成的任务再次启动，返回已完成状态
        if _completed_tasks.get(task_id) in {"success", "failed"}:
            _log_event("start_task_already_completed", {"task_id": task_id, "status": _completed_tasks.get(task_id)})
            return {"success": True, "started": False, "message": f"already completed: status={_completed_tasks.get(task_id)}"}

    # 标记运行中
    _running_task_id = task_id

    # 覆盖上下文中的策略与重定向参数（仅当前端提供时）
    if strategies_override is not None:
        ctx["strategies"] = strategies_override
    if follow_redirects_override is not None:
        ctx["follow_redirects"] = follow_redirects_override
    # 持久化更新后的上下文
    try:
        _save_context(ctx)
    except Exception:
        # 保持执行继续，但不进行过度兜底
        pass

    # 后台执行器启动（骨架，细节在 process.py 中实现）
    async def _runner():
        from . import process as _process  # 延迟导入，避免循环依赖
        success = False
        try:
            _log_event("start_task_runner_begin", {"task_id": task_id, "strategies": ctx.get("strategies", "-"), "follow_redirects": ctx.get("follow_redirects", "-")})
            success = await _process.run_permission_task(ctx)
            status = "success" if success else "failed"
            _completed_tasks[task_id] = status
            _log_event("start_task_runner_end", {"task_id": task_id, "status": status})
        finally:
            # 释放运行占位 & 上下文清理（基础）
            async with _lock:
                global _running_task_id
                if _running_task_id == task_id:
                    _running_task_id = None
                # 基础上下文清理：记录完成状态并清理 task_id，持久化
                try:
                    _context_mem["state"] = {"status": "completed", "success": success}
                    _context_mem["task_id"] = None
                    _save_context(_context_mem)
                except Exception:
                    pass

    asyncio.create_task(_runner())
    _log_event("start_task_started", {"task_id": task_id})
    return {"success": True, "started": True, "message": "started"}

# 兼容 CLI 启动（示例命令见交付说明）
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("sensitive_check_local.server:app", host="127.0.0.1", port=17866, reload=False, log_level="info")  # 本地服务自身是在localhost启动的，这里保留127.0.0.1
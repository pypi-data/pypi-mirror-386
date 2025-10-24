"""
Backend API client for permission testing.
Handles HTTP communication with the Java backend service.
"""
from __future__ import annotations

import os
import json
import asyncio
from typing import Any, Dict, List, Optional
import httpx


class BackendAPIError(Exception):
    """Backend API communication error"""
    def __init__(self, message: str, status_code: Optional[int] = None, payload: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}


class BackendAPI:
    """
    HTTP 客户端封装，统一向后端 Java 发起请求并注入必要头与参数
    
    统一注入 Headers：Project-Id、User-Id、X-Client-Id；Content-Type: application/json
    采用指数退避重试策略：对网络错误/超时/5xx 进行重试；4xx 不重试直接上抛
    """
    
    def __init__(self, project_id: str, user_id: str, client_id: str, base_url: Optional[str] = None, timeout_sec: float = 10.0):
        self.project_id = project_id
        self.user_id = user_id
        self.client_id = client_id
        self.base_url = base_url or os.getenv("BACKEND_BASE_URL", "http://aqapi.jdtest.local:8008")
        self.timeout_sec = timeout_sec
        self.session: Optional[httpx.AsyncClient] = None
        
    async def _get_session(self) -> httpx.AsyncClient:
        if self.session is None:
            self.session = httpx.AsyncClient(timeout=self.timeout_sec)
        return self.session
        
    async def close(self) -> None:
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def _request(
        self,
        method: str,
        path: str,
        json_body: Optional[Dict[str, Any]] = None,
        max_retries: int = 5,
        initial_delay: float = 0.5,
        backoff_factor: float = 2.0,
        max_delay: float = 30.0
    ) -> Dict[str, Any]:
        """
        发起 HTTP 请求，带指数退避重试策略
        对网络错误/超时/5xx 进行重试；4xx 不重试直接上抛
        """
        import logging
        logger = logging.getLogger("sensitive_check_local")
        
        url = f"{self.base_url.rstrip('/')}{path}"
        headers = {
            "Content-Type": "application/json",
            "Project-ID": self.project_id,
            "User-ID": self.user_id,
            "X-Client-Id": self.client_id,
        }
        
        # 安全的请求体预览
        body_preview = "None"
        if json_body:
            try:
                import json
                body_str = json.dumps(json_body, ensure_ascii=False)
                body_preview = body_str[:200] + "..." if len(body_str) > 200 else body_str
            except Exception:
                body_preview = str(json_body)[:200]
        
        logger.info(f"[HTTP-REQUEST] 🌐 发起请求:")
        logger.info(f"[HTTP-REQUEST]   - Method: {method.upper()}")
        logger.info(f"[HTTP-REQUEST]   - URL: {url}")
        logger.info(f"[HTTP-REQUEST]   - Headers: Project-Id={self.project_id}, User-Id={self.user_id[:6]}***, Client-Id={self.client_id[:8]}***")
        logger.info(f"[HTTP-REQUEST]   - Body: {body_preview}")
        
        session = await self._get_session()
        delay = initial_delay
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"[HTTP-REQUEST] 尝试 {attempt + 1}/{max_retries + 1}...")
                
                if method.upper() == "GET":
                    response = await session.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await session.post(url, headers=headers, json=json_body)
                else:
                    raise BackendAPIError(f"Unsupported HTTP method: {method}")
                
                logger.info(f"[HTTP-RESPONSE] 收到响应: status={response.status_code}")
                
                # 4xx 错误不重试，直接抛出
                if 400 <= response.status_code < 500:
                    try:
                        error_data = response.json()
                        message = error_data.get("message", f"HTTP {response.status_code}")
                        logger.error(f"[HTTP-RESPONSE] ❌ 客户端错误: {message}")
                    except Exception:
                        message = f"HTTP {response.status_code}: {response.text}"
                        logger.error(f"[HTTP-RESPONSE] ❌ 客户端错误: {message}")
                    raise BackendAPIError(message, response.status_code, error_data if 'error_data' in locals() else {})
                
                # 5xx 错误进行重试
                if response.status_code >= 500:
                    logger.warning(f"[HTTP-RESPONSE] ⚠️ 服务器错误: {response.status_code}, 将重试...")
                    if attempt < max_retries:
                        logger.info(f"[HTTP-REQUEST] 等待 {delay}s 后重试...")
                        await asyncio.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                        continue
                    else:
                        logger.error(f"[HTTP-RESPONSE] ❌ 重试次数耗尽: HTTP {response.status_code}")
                        raise BackendAPIError(f"HTTP {response.status_code} after {max_retries} retries", response.status_code)
                
                # 成功响应
                response.raise_for_status()
                response_data = response.json()
                
                # 安全的响应预览
                try:
                    import json
                    resp_str = json.dumps(response_data, ensure_ascii=False)
                    resp_preview = resp_str[:300] + "..." if len(resp_str) > 300 else resp_str
                except Exception:
                    resp_preview = str(response_data)[:300]
                
                logger.info(f"[HTTP-RESPONSE] ✅ 请求成功: {resp_preview}")
                return response_data
                
            except httpx.TimeoutException:
                logger.warning(f"[HTTP-REQUEST] ⏰ 请求超时 (尝试 {attempt + 1})")
                if attempt < max_retries:
                    logger.info(f"[HTTP-REQUEST] 等待 {delay}s 后重试...")
                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
                    continue
                else:
                    logger.error(f"[HTTP-REQUEST] ❌ 超时重试次数耗尽")
                    raise BackendAPIError(f"Request timeout after {max_retries} retries")
                    
            except httpx.NetworkError as e:
                logger.warning(f"[HTTP-REQUEST] 🌐 网络错误: {e} (尝试 {attempt + 1})")
                if attempt < max_retries:
                    logger.info(f"[HTTP-REQUEST] 等待 {delay}s 后重试...")
                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
                    continue
                else:
                    logger.error(f"[HTTP-REQUEST] ❌ 网络错误重试次数耗尽: {e}")
                    raise BackendAPIError(f"Network error after {max_retries} retries: {e}")
                    
            except BackendAPIError:
                # 重新抛出我们自己的异常
                raise
                
            except Exception as e:
                logger.error(f"[HTTP-REQUEST] ❌ 未知错误: {e}", exc_info=True)
                raise BackendAPIError(f"Unexpected error: {e}")
    
    # 原子认领：POST /api/permission/tasks/claim
    async def claim(self, task_id: str, client_id: Optional[str] = None) -> Dict[str, Any]:
        if not task_id:
            raise BackendAPIError("missing task_id for claim")
        payload = {
            "task_id": task_id,
            "client_id": client_id or self.client_id
        }
        return await self._request("POST", "/api/permission/tasks/claim", json_body=payload)
    
    # 详情拉取：GET /api/permission/tasks/detail
    async def detail(self, task_id: str) -> Dict[str, Any]:
        if not task_id:
            raise BackendAPIError("missing task_id for detail")
        return await self._request("GET", f"/api/permission/tasks/detail?taskId={task_id}")
    
    # 进度上报：POST /api/permission/tasks/progress
    async def progress(self, task_id: str, current: int, total: int, message: str) -> Dict[str, Any]:
        if not task_id:
            raise BackendAPIError("missing task_id for progress")
        payload = {
            "task_id": task_id,
            "current": int(current),
            "total": int(total),
            "message": str(message)
        }
        return await self._request("POST", "/api/permission/tasks/progress", json_body=payload)
    
    # 结果上报：POST /api/permission/tasks/results
    async def results(self, task_id: str, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not task_id:
            raise BackendAPIError("missing task_id for results")
        if not isinstance(test_results, list):
            raise BackendAPIError("test_results must be a list")
        payload = {"task_id": task_id, "test_results": test_results}
        return await self._request("POST", "/api/permission/tasks/results", json_body=payload)

    # 完成状态：POST /api/permission/tasks/complete
    async def complete(self, task_id: str, success: bool) -> Dict[str, Any]:
        if not task_id:
            raise BackendAPIError("missing task_id for complete")
        payload = {"task_id": task_id, "success": bool(success)}
        return await self._request("POST", "/api/permission/tasks/complete", json_body=payload)


def build_backend_api_from_context(ctx: Dict[str, Any]) -> BackendAPI:
    """
    从本地上下文构建 BackendAPI 客户端（严格从 Headers 注入的上下文字段）
    ctx 结构：{project_id, user_id, task_id, client_id, ...}
    """
    if not isinstance(ctx, dict):
        raise BackendAPIError("invalid context")
    project_id = str(ctx.get("project_id") or "").strip()
    user_id = str(ctx.get("user_id") or "").strip()
    client_id = str(ctx.get("client_id") or "").strip()
    if not project_id or not user_id or not client_id:
        raise BackendAPIError("context missing fields: project_id/user_id/client_id")
    return BackendAPI(project_id=project_id, user_id=user_id, client_id=client_id)
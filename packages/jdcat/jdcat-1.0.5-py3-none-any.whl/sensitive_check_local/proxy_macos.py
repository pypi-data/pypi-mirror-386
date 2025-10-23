"""
macOS system proxy control for sensitive-check-local.

Implements:
- detect_services(): enumerate active network services (exclude lines starting with '*')
- snapshot_proxy_state(services): capture HTTP/HTTPS proxy and bypass list per service
- enable_system_proxy(services, port, bypass_domains): set proxies to 127.0.0.1:port and merge/set bypass list
- restore_proxy_state(snapshot): restore previous state

Non-Darwin platforms: raise RuntimeError to signal upper layer for graceful degrade.
"""
from __future__ import annotations

import platform
import subprocess
from typing import Any, Dict, List, Tuple

from . import config as _config


def _ensure_darwin() -> None:
    if platform.system() != "Darwin":
        raise RuntimeError("System proxy operations are only supported on macOS (Darwin).")


def _run(args: List[str]) -> Tuple[int, str, str]:
    p = subprocess.run(args, capture_output=True, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    return p.returncode, out, err

def run_cmd(args: List[str]) -> Tuple[int, str, str]:
    """
    Unified command runner. Returns (code, stdout, stderr).
    """
    return _run(args)

# added: logger and admin-run helper for macOS privileged operations
import os
import shlex
import logging
import time
from urllib import request as _urlreq, error as _urlerr
_logger = logging.getLogger("sensitive_check_local.proxy")
if not _logger.handlers:
    _logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setLevel(logging.INFO)
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))
    _logger.addHandler(_h)

# 全局标记，用于跟踪是否已经申请过本地网络权限
_network_permission_requested = False

# 单轮 /start 防抖：仅允许一次 Helper 安装尝试
_helper_install_attempted_once = False

# 本轮是否已实际启用过系统代理（仅在 enable 成功后置 True）
_proxy_applied_this_round = False

def _run_admin(args: List[str]) -> Tuple[int, str, str]:
    """
    Execute command with admin privileges via AppleScript to trigger macOS auth prompt.
    Only use for commands that change system proxy settings.
    """
    # Build a properly quoted shell command
    cmd = " ".join(shlex.quote(a) for a in args)
    script = f'do shell script "{cmd}" with administrator privileges'
    p = subprocess.run(["/usr/bin/osascript", "-e", script], capture_output=True, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    code = int(p.returncode or 0)
    _logger.info("[proxy-admin] cmd=%s code=%s out=%s err=%s", cmd, code, out[:200], err[:200])
    return code, out, err

def _run_admin_batch(commands: List[List[str]]) -> List[Tuple[int, str, str]]:
    """
    Execute multiple commands in a single admin privileges request to reduce popup frequency.
    """
    if not commands:
        return []
    
    # Combine all commands into a single shell script
    cmd_strings = []
    for args in commands:
        cmd = " ".join(shlex.quote(a) for a in args)
        cmd_strings.append(cmd)
    
    # Join commands with && to stop on first failure
    combined_cmd = " && ".join(cmd_strings)
    script = f'do shell script "{combined_cmd}" with administrator privileges'
    
    _logger.info("[proxy-admin-batch] Executing %d commands in single admin request", len(commands))
    _logger.debug("[proxy-admin-batch] Script: %s", script[:500])
    
    try:
        p = subprocess.run(["/usr/bin/osascript", "-e", script], capture_output=True, text=True)
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()
        code = int(p.returncode or 0)
        
        if code == 0:
            _logger.info("[proxy-admin-batch] 成功执行，返回码: %s", code)
        else:
            _logger.warning("[proxy-admin-batch] 执行失败，返回码: %s", code)
            if "User canceled" in err or "cancelled" in err.lower():
                _logger.info("[proxy-admin-batch] 用户取消了管理员权限验证")
            elif "Authentication failed" in err:
                _logger.info("[proxy-admin-batch] 管理员权限验证失败")
            else:
                _logger.warning("[proxy-admin-batch] 其他错误: %s", err[:200])
        
        _logger.info("[proxy-admin-batch] Combined result: code=%s out=%s err=%s", code, out[:200], err[:200])
        
        # Return the same result for all commands (simplified)
        return [(code, out, err)] * len(commands)
        
    except Exception as e:
        _logger.error("[proxy-admin-batch] 执行异常: %s", e)
        # Return error for all commands
        return [(1, "", str(e))] * len(commands)


def _helper_plist_path() -> str:
    return "/Library/LaunchDaemons/com.jdcat.proxy.helper.plist"

def _helper_healthcheck(timeout: float = 1.0) -> bool:
    try:
        req = _urlreq.Request(url="http://127.0.0.1:17901/health", method="GET")
        with _urlreq.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            if status != 200:
                return False
            body = resp.read()
            txt = body.decode("utf-8", errors="ignore") if isinstance(body, (bytes, bytearray)) else str(body)
            import json as _json  # local import to minimize global deps
            try:
                obj = _json.loads(txt)
                return bool(obj.get("ok", False))
            except Exception:
                return False
    except Exception:
        return False

def install_if_needed() -> None:
    """
    首次安装 Root Helper（仅在缺失或不可用时触发一次管理员弹窗）：
      1) 创建目录 /Library/PrivilegedHelperTools
      2) 复制打包内 jdcat/root_helper/jdcat_proxy_helper.py -> /Library/PrivilegedHelperTools/jdcat_proxy_helper.py（chmod 0755, chown root:wheel）
      3) 复制打包内 jdcat/resources/com.jdcat.proxy.helper.plist -> /Library/LaunchDaemons/com.jdcat.proxy.helper.plist（chmod 0644, chown root:wheel）
      4) launchctl bootstrap/enable/kickstart
    安装后不做二次安装尝试；仅在本函数内进行一次管理员弹窗。
    """
    global _helper_install_attempted_once
    _ensure_darwin()

    # 若已存在且健康，直接返回（不弹窗）
    try:
        if os.path.exists(_helper_plist_path()) and _helper_healthcheck(timeout=0.6):
            _logger.info("[helper-install] 已存在且健康，跳过安装")
            return
    except Exception:
        pass

    # 防抖：本进程本轮仅允许一次安装尝试
    if _helper_install_attempted_once:
        _logger.info("[helper-install] 本轮已尝试安装，跳过重复安装与弹窗")
        return
    _helper_install_attempted_once = True
    # 计算打包内源文件路径（基于当前模块 __file__）
    here = os.path.abspath(os.path.dirname(__file__))
    pkg_root = os.path.abspath(os.path.join(here, ".."))  # jdcat/
    src_helper = os.path.abspath(os.path.join(pkg_root, "root_helper", "jdcat_proxy_helper.py"))
    src_plist = os.path.abspath(os.path.join(pkg_root, "resources", "com.jdcat.proxy.helper.plist"))

    # 目标路径
    dst_helper = "/Library/PrivilegedHelperTools/jdcat_proxy_helper.py"
    dst_plist = _helper_plist_path()

    # 校验源文件存在
    if not os.path.exists(src_helper):
        raise RuntimeError(f"缺少打包内 Helper 脚本: {src_helper}")
    if not os.path.exists(src_plist):
        raise RuntimeError(f"缺少打包内 LaunchDaemon 模板: {src_plist}")

    commands: list[list[str]] = [
        ["/bin/mkdir", "-p", "/Library/PrivilegedHelperTools"],
        ["/bin/cp", src_helper, dst_helper],
        ["/bin/chmod", "0755", dst_helper],
        ["/usr/sbin/chown", "root:wheel", dst_helper],
        ["/bin/cp", src_plist, dst_plist],
        ["/bin/chmod", "0644", dst_plist],
        ["/usr/sbin/chown", "root:wheel", dst_plist],
        ["/bin/launchctl", "bootstrap", "system", dst_plist],
        ["/bin/launchctl", "enable", "system/com.jdcat.proxy.helper"],
        ["/bin/launchctl", "kickstart", "-k", "system/com.jdcat.proxy.helper"],
    ]

    _logger.info("[helper-install] 以管理员权限执行安装流程（一次性弹窗）")
    results = _run_admin_batch(commands)
    code0 = results[0][0] if results else 1
    if code0 != 0:
        err = results[0][2] or results[0][1] if results else "unknown"
        raise RuntimeError(f"Root Helper 安装失败: {err}")

    # 安装完成后：等待 Helper 启动并健康就绪（重试窗口 8-10s）
    try:
        from . import root_helper_client as _rhc
    except Exception:
        _rhc = None

    wait_ok = False
    if _rhc and hasattr(_rhc, "wait_for_helper"):
        wait_ok = bool(_rhc.wait_for_helper(timeout=8.0, interval=0.5))
    else:
        # 兼容：本地简单轮询
        for _ in range(16):
            if _helper_healthcheck(timeout=0.6):
                wait_ok = True
                break
            time.sleep(0.5)

    if not wait_ok:
        raise RuntimeError("Root Helper 安装后健康检查失败（/health 不可达）")

    _logger.info("[helper-install] 健康检查通过，Helper 就绪")

class NoActiveNetworkServices(Exception):
    """Raised when no active macOS network services are detected."""
    pass


def detect_services() -> List[str]:
    """
    Use /usr/sbin/networksetup -listallnetworkservices and filter:
    - skip lines starting with 'An asterisk (*) denotes'
    - skip lines starting with '*' (disabled services)
    - skip empty lines
    Return active service names. If none, raise NoActiveNetworkServices with guidance.
    """
    _ensure_darwin()
    code, out, err = _run(["/usr/sbin/networksetup", "-listallnetworkservices"])
    if code != 0:
        raise RuntimeError(f"Failed to list network services: {err or out}")
    services: List[str] = []
    for raw in (out or "").splitlines():
        line = (raw or "").strip()
        if not line:
            continue
        low = line.lower()
        # Robustly skip header/notice lines from networksetup output
        if low.startswith("an asterisk") or "asterisk (*) denotes" in low:
            continue
        if line.lstrip().startswith("*"):  # disabled service line
            continue
        # Heuristic: skip localized header lines mentioning disabled services
        if ("带星号" in line or "已禁用" in line) and ("网络服务" in line or "network service" in low):
            continue
        services.append(line)
    # Validate services with -getinfo to avoid header/noise being treated as names
    valid: List[str] = []
    for svc in services:
        c, o, e = _run(["/usr/sbin/networksetup", "-getinfo", svc])
        if c == 0:
            valid.append(svc)
    services = valid
    if not services:
        raise NoActiveNetworkServices("no_active_network_services: 请在系统设置启用某个网络服务（如 Wi‑Fi）后重试")
    return services


def _parse_proxy_get(output: str) -> Dict[str, Any]:
    """
    Parse output of `networksetup -getwebproxy` or `-getsecurewebproxy`.
    Example:
      Enabled: Yes
      Server: 127.0.0.1
      Port: 8080
      Authenticated Proxy Enabled: 0
    """
    enabled = False
    host: str | None = None
    port: int | None = None
    for line in (output or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("enabled:"):
            val = line.split(":", 1)[1].strip().lower()
            enabled = val in ("yes", "1", "true")
        elif line.lower().startswith("server:"):
            v = line.split(":", 1)[1].strip()
            host = v if v else None
        elif line.lower().startswith("port:"):
            v = line.split(":", 1)[1].strip()
            try:
                port = int(v)
            except Exception:
                port = None
    return {"enabled": enabled, "host": host, "port": port}


def _get_webproxy(service: str) -> Dict[str, Any]:
    code, out, err = _run(["/usr/sbin/networksetup", "-getwebproxy", service])
    if code != 0:
        # Some services may not support; treat as disabled
        return {"enabled": False, "host": None, "port": None}
    return _parse_proxy_get(out)


def _get_securewebproxy(service: str) -> Dict[str, Any]:
    code, out, err = _run(["/usr/sbin/networksetup", "-getsecurewebproxy", service])
    if code != 0:
        return {"enabled": False, "host": None, "port": None}
    return _parse_proxy_get(out)


def _get_bypass(service: str) -> list[str]:
    code, out, err = _run(["/usr/sbin/networksetup", "-getproxybypassdomains", service])
    if code != 0:
        # If not supported, return empty
        return []
    # When none configured, it prints: "There aren't any configured for this service!"
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    if lines and "there aren't any configured" in lines[0].lower():
        return []
    return lines


def snapshot_proxy_state(services: List[str]) -> Dict[str, Any]:
    """
    Snapshot proxy settings for given services.
    Returns a dict that can be passed to restore_proxy_state.
    """
    _ensure_darwin()
    items: Dict[str, Any] = {}
    for svc in services:
        http = _get_webproxy(svc)
        https = _get_securewebproxy(svc)
        bypass = _get_bypass(svc)
        items[svc] = {"http": http, "https": https, "bypass": bypass}
    return {"services": list(services), "items": items}


def _set_webproxy(service: str, host: str, port: int, enabled: bool) -> None:
    # Use batch execution to reduce admin prompts
    args1 = ["/usr/sbin/networksetup", "-setwebproxy", service, host, str(port)]
    args2 = ["/usr/sbin/networksetup", "-setwebproxystate", service, "on" if enabled else "off"]
    
    results = _run_admin_batch([args1, args2])
    c1, o1, e1 = results[0]
    c2, o2, e2 = results[1]
    
    _logger.info("[proxy-set] HTTP setwebproxy service=%s host=%s port=%s code=%s", service, host, port, c1)
    if c1 != 0:
        raise RuntimeError(f"Failed to set HTTP proxy for {service}: {e1 or o1}")
    
    _logger.info("[proxy-set] HTTP setwebproxystate service=%s enabled=%s code=%s", service, enabled, c2)
    if c2 != 0:
        raise RuntimeError(f"Failed to toggle HTTP proxy for {service}: {e2 or o2}")


def _set_securewebproxy(service: str, host: str, port: int, enabled: bool) -> None:
    # Use batch execution to reduce admin prompts
    args1 = ["/usr/sbin/networksetup", "-setsecurewebproxy", service, host, str(port)]
    args2 = ["/usr/sbin/networksetup", "-setsecurewebproxystate", service, "on" if enabled else "off"]
    
    results = _run_admin_batch([args1, args2])
    c1, o1, e1 = results[0]
    c2, o2, e2 = results[1]
    
    _logger.info("[proxy-set] HTTPS setsecurewebproxy service=%s host=%s port=%s code=%s", service, host, port, c1)
    if c1 != 0:
        raise RuntimeError(f"Failed to set HTTPS proxy for {service}: {e1 or o1}")
    
    _logger.info("[proxy-set] HTTPS setsecurewebproxystate service=%s enabled=%s code=%s", service, enabled, c2)
    if c2 != 0:
        raise RuntimeError(f"Failed to toggle HTTPS proxy for {service}: {e2 or o2}")


def _set_bypass(service: str, domains: list[str]) -> None:
    # If empty, explicitly clear list using the special 'Empty' token
    if not domains:
        args = ["/usr/sbin/networksetup", "-setproxybypassdomains", service, "Empty"]
    else:
        args = ["/usr/sbin/networksetup", "-setproxybypassdomains", service] + domains
    
    # Use single admin call for bypass domains
    results = _run_admin_batch([args])
    c, o, e = results[0]
    
    if not domains:
        _logger.info("[proxy-set] bypass clear service=%s code=%s", service, c)
        if c != 0:
            raise RuntimeError(f"Failed to clear bypass domains for {service}: {e or o}")
    else:
        _logger.info("[proxy-set] bypass set service=%s domains=%s code=%s", service, domains, c)
        if c != 0:
            raise RuntimeError(f"Failed to set bypass domains for {service}: {e or o}")


def enable_system_proxy(services: List[str], port: int, bypass_domains: list[str] | None = None) -> Dict[str, Any]:
    """
    启用系统代理到 127.0.0.1:port（HTTP/HTTPS），最小可行：优先通过 Root Helper 执行。
    流程：
      1) 若 Helper 可用（GET /health 成功），直接调用 root_helper_client.enable(...)
      2) 若不可用，执行"首次安装流程"，然后再次尝试 Helper
    注意：不再直接用 AppleScript 调用 networksetup；AppleScript 仅用于安装 Helper 的提权复制与 launchctl。
    """
    global _proxy_applied_this_round, _network_permission_requested
    _ensure_darwin()

    # 首次启用时尝试申请本地网络权限（保留现有逻辑）
    if not _network_permission_requested:
        try:
            from .network_permission import request_local_network_permission
            _logger.info("首次启用代理，申请本地网络权限...")
            request_local_network_permission()
            _network_permission_requested = True
            _logger.info("本地网络权限申请完成")
        except Exception as e:
            _logger.warning(f"本地网络权限申请失败，但继续执行代理设置: {e}")
            _network_permission_requested = True
    else:
        _logger.debug("本地网络权限已申请过，跳过")

    # 组装 host/port/bypass
    host = "127.0.0.1"
    defaults = list(_config.DEFAULT_BYPASS) if hasattr(_config, "DEFAULT_BYPASS") else ["aq.jdtest.net", "aqapi.jdtest.local", "0.0.0.0", "::1"]
    merged = defaults + (bypass_domains or [])
    seen: set[str] = set()
    final_domains: list[str] = []
    for d in merged:
        key = str(d).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        final_domains.append(str(d).strip())

    # 调用 Root Helper
    try:
        from . import root_helper_client as _rhc
    except Exception as e:
        raise RuntimeError(f"缺少 Root Helper 客户端模块: {e}")

    # 1) 尝试直连 Helper
    if _rhc.health(timeout=1.0):
        _logger.info("[helper] 健康检查通过，直接调用 /enable")
        _rhc.enable(host, int(port), list(services), final_domains, timeout=5.0)
        _proxy_applied_this_round = True
        return {"enabled": True, "host": host, "port": int(port), "bypass": final_domains, "services": list(services)}

    # 2) 不可用则执行安装流程并重试
    _logger.info("[helper] 不可用，开始安装 Helper...")
    install_if_needed()
    if not _rhc.health(timeout=1.0):
        raise RuntimeError("Root Helper 安装后仍不可用（/health 检测失败）")
    _logger.info("[helper] 安装完成，调用 /enable")
    _rhc.enable(host, int(port), list(services), final_domains, timeout=5.0)
    _proxy_applied_this_round = True
    return {"enabled": True, "host": host, "port": int(port), "bypass": final_domains, "services": list(services)}


def restore_proxy_state(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    恢复系统代理（最小实现）：根据快照中的服务列表将 HTTP/HTTPS 代理状态关闭。
    逻辑：
      - 仅当本轮确实启用过系统代理（_proxy_applied_this_round 为 True）时才执行恢复
      - 优先通过 Root Helper 的 /restore 接口关闭所有服务上的代理
      - Helper 不可用则直接跳过（不触发安装或任何新弹窗），记录警告
    """
    global _proxy_applied_this_round
    _ensure_darwin()
    if not isinstance(snapshot, dict):
        raise RuntimeError("Invalid snapshot")

    services = snapshot.get("services") or []
    if not services:
        return {"restored": True, "services": []}

    # 若本轮未启用过系统代理，则不做恢复（避免“启用失败却恢复”的路径）
    if not _proxy_applied_this_round:
        _logger.info("[restore] 本轮未启用系统代理，跳过恢复")
        return {"restored": False, "services": list(services), "skipped": True}

    try:
        from . import root_helper_client as _rhc
    except Exception as e:
        raise RuntimeError(f"缺少 Root Helper 客户端模块: {e}")

    if _rhc.health(timeout=1.0):
        _logger.info("[helper] 健康检查通过，调用 /restore")
        _rhc.restore(list(services), timeout=5.0)
        return {"restored": True, "services": list(services)}

    # 不做过度兜底：不安装、不弹窗，直接跳过
    _logger.warning("[helper] 不可用，跳过 /restore（不触发安装或弹窗）")
    return {"restored": False, "services": list(services), "skipped": True}


# Backward-compat wrappers (no-op if not used)
def enable_system_proxy_legacy(port: int) -> Dict[str, Any]:
    _ensure_darwin()
    svcs = detect_services()
    enable_system_proxy(svcs, port, None)
    return {"enabled": True, "services": svcs, "port": port}


def disable_system_proxy_legacy() -> Dict[str, Any]:
    _ensure_darwin()
    svcs = detect_services()
    snap = snapshot_proxy_state(svcs)
    # Turn off directly
    for svc in svcs:
        _set_webproxy(svc, "127.0.0.1", 8888, False)
        _set_securewebproxy(svc, "127.0.0.1", 8888, False)
    return {"disabled": True, "services": svcs, "snapshot": snap}
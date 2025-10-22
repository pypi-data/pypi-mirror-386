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
_logger = logging.getLogger("sensitive_check_local.proxy")
if not _logger.handlers:
    _logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setLevel(logging.INFO)
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))
    _logger.addHandler(_h)

# 全局标记，用于跟踪是否已经申请过本地网络权限
_network_permission_requested = False

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
    Enable system proxy to 127.0.0.1:port for HTTP/HTTPS on all given services.
    - Merge default bypass with provided bypass_domains (dedup, preserve order)
    - Use batch admin execution to minimize permission prompts
    - If at least one service succeeds, return enabled=True; otherwise raise with aggregated reasons
    """
    _ensure_darwin()
    
    # 在首次启用代理时申请本地网络权限
    global _network_permission_requested
    if not _network_permission_requested:
        try:
            from .network_permission import request_local_network_permission
            _logger.info("首次启用代理，申请本地网络权限...")
            request_local_network_permission()
            _network_permission_requested = True
            _logger.info("本地网络权限申请完成")
        except Exception as e:
            _logger.warning(f"本地网络权限申请失败，但继续执行代理设置: {e}")
            # 即使失败也标记为已请求，避免重复尝试
            _network_permission_requested = True
    else:
        _logger.debug("本地网络权限已申请过，跳过")
    
    host = "127.0.0.1"
    defaults = list(_config.DEFAULT_BYPASS) if hasattr(_config, "DEFAULT_BYPASS") else ["aq.jdtest.net", "aqapi.jdtest.local", "0.0.0.0", "::1"]
    merged = defaults + (bypass_domains or [])
    # Deduplicate while preserving order (case-insensitive)
    seen: set[str] = set()
    final_domains: list[str] = []
    for d in merged:
        key = str(d).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        final_domains.append(str(d).strip())

    # Build all commands for batch execution
    all_commands = []
    for svc in services:
        # HTTP proxy commands
        all_commands.append(["/usr/sbin/networksetup", "-setwebproxy", svc, host, str(port)])
        all_commands.append(["/usr/sbin/networksetup", "-setwebproxystate", svc, "on"])
        # HTTPS proxy commands
        all_commands.append(["/usr/sbin/networksetup", "-setsecurewebproxy", svc, host, str(port)])
        all_commands.append(["/usr/sbin/networksetup", "-setsecurewebproxystate", svc, "on"])
        # Bypass domains command
        if final_domains:
            all_commands.append(["/usr/sbin/networksetup", "-setproxybypassdomains", svc] + final_domains)
        else:
            all_commands.append(["/usr/sbin/networksetup", "-setproxybypassdomains", svc, "Empty"])

    _logger.info("[proxy-enable] Executing %d commands for %d services in single admin request", len(all_commands), len(services))
    
    try:
        # Execute all commands in a single admin request
        results = _run_admin_batch(all_commands)
        
        # Check results - if any command failed, the entire batch would fail
        success_count = len(services)  # Assume all succeeded if batch didn't raise exception
        errors = []
        
        # Check if the first result indicates failure
        if results and results[0][0] != 0:
            success_count = 0
            errors.append(f"Batch execution failed: {results[0][2] or results[0][1]}")
        
        if success_count >= 1:
            _logger.info("[proxy-enable] Successfully configured proxy for %d services", success_count)
            return {
                "enabled": True,
                "host": host,
                "port": port,
                "bypass": final_domains,
                "services": list(services),
                "successCount": success_count,
                "failureCount": max(0, len(services) - success_count),
                "errors": errors,
            }
        else:
            detail = "\n".join(errors) if errors else "Batch execution failed"
            raise RuntimeError("未能在任何活动网络服务上启用代理\n" + detail)
            
    except Exception as e:
        _logger.error("[proxy-enable] Failed to configure proxy: %s", e)
        raise RuntimeError(f"代理配置失败: {e}")


def restore_proxy_state(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Restore proxy settings from snapshot captured by snapshot_proxy_state().
    Also restore (or clear) bypass domains. When restoring an empty list, we clear the bypass list
    using: networksetup -setproxybypassdomains service Empty
    
    Uses batch execution to minimize admin password prompts.
    """
    _ensure_darwin()
    if not isinstance(snapshot, dict):
        raise RuntimeError("Invalid snapshot")
    services = snapshot.get("services") or []
    items = snapshot.get("items") or {}
    
    if not services:
        return {"restored": True, "services": []}
    
    # Build all commands for batch execution
    all_commands = []
    
    for svc in services:
        it = items.get(svc) or {}
        http = it.get("http") or {}
        https = it.get("https") or {}
        bypass = it.get("bypass")  # may be list or None

        # HTTP proxy commands
        if http.get("enabled"):
            host = http.get("host") or ""
            port = int(http.get("port") or 0)
            if host and port:
                all_commands.append(["/usr/sbin/networksetup", "-setwebproxy", svc, host, str(port)])
                all_commands.append(["/usr/sbin/networksetup", "-setwebproxystate", svc, "on"])
            else:
                # If missing details, turn it off
                all_commands.append(["/usr/sbin/networksetup", "-setwebproxystate", svc, "off"])
        else:
            all_commands.append(["/usr/sbin/networksetup", "-setwebproxystate", svc, "off"])

        # HTTPS proxy commands
        if https.get("enabled"):
            host = https.get("host") or ""
            port = int(https.get("port") or 0)
            if host and port:
                all_commands.append(["/usr/sbin/networksetup", "-setsecurewebproxy", svc, host, str(port)])
                all_commands.append(["/usr/sbin/networksetup", "-setsecurewebproxystate", svc, "on"])
            else:
                all_commands.append(["/usr/sbin/networksetup", "-setsecurewebproxystate", svc, "off"])
        else:
            all_commands.append(["/usr/sbin/networksetup", "-setsecurewebproxystate", svc, "off"])

        # Bypass domains commands
        if isinstance(bypass, list) and bypass:
            # Filter out empty strings and ensure domains are valid
            final_domains = [d.strip() for d in bypass if d and d.strip()]
            if final_domains:
                all_commands.append(["/usr/sbin/networksetup", "-setproxybypassdomains", svc] + final_domains)
            else:
                all_commands.append(["/usr/sbin/networksetup", "-setproxybypassdomains", svc, "Empty"])
        else:
            all_commands.append(["/usr/sbin/networksetup", "-setproxybypassdomains", svc, "Empty"])
    
    _logger.info("[proxy-restore] Executing %d commands for %d services in single admin request", len(all_commands), len(services))
    
    try:
        # Execute all commands in a single admin request
        results = _run_admin_batch(all_commands)
        
        # Check results - if any command failed, the entire batch would fail
        success_count = len(services)  # Assume all succeeded if batch didn't raise exception
        errors = []
        
        # Check if the first result indicates failure
        if results and results[0][0] != 0:
            success_count = 0
            errors.append(f"Batch execution failed: {results[0][2] or results[0][1]}")
        
        if success_count >= 1:
            _logger.info("[proxy-restore] Successfully restored proxy settings for %d services", success_count)
            return {
                "restored": True,
                "services": list(services),
                "successCount": success_count,
                "failureCount": max(0, len(services) - success_count),
                "errors": errors,
            }
        else:
            detail = "\n".join(errors) if errors else "Batch execution failed"
            raise RuntimeError("未能恢复任何网络服务的代理设置\n" + detail)
            
    except Exception as e:
        _logger.error("[proxy-restore] Failed to restore proxy settings: %s", e)
        raise RuntimeError(f"代理设置恢复失败: {e}")


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
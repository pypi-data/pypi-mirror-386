from __future__ import annotations

"""
analysis_local
- 对齐老工具文档描述的响应细粒度比对器、权限检测器、Excel 风险等级映射
- 提供统一入口：
  • compare_responses(original_response, modified_response) -> dict
  • detect_privilege_escalation(original_identity_role, target_identity_role, original_user_id, target_user_id) -> dict
  • map_excel_risk_level(original_status, modified_status, similarity) -> str
  • build_evidence(original_response, modified_response, compare_dict, detector_dict) -> dict
"""

import re
import difflib
from typing import Any, Dict, Optional, Tuple


def _safe_text(x: Any, max_len: int = 4096) -> str:
    try:
        s = str(x) if x is not None else ""
    except Exception:
        s = ""
    return s[:max_len]


def _normalize_text(s: str) -> str:
    """
    标准化文本以进行内容相似度计算：
    - 去除空白差异（多空格/换行）
    - 小写化
    - 移除常见无意义 header 噪声（若传入的是字符串化后的响应）
    """
    if not isinstance(s, str):
        try:
            s = str(s)
        except Exception:
            s = ""
    s = s.strip().lower()
    # 简易去噪：去除多余空白
    s = re.sub(r"\s+", " ", s)
    return s


def compute_similarity(a: Any, b: Any) -> float:
    """
    内容相似度计算（简化对齐版）：
    - 使用 difflib.SequenceMatcher 计算两段标准化文本的相似度
    - 返回 [0.0, 1.0] 浮点
    """
    a_norm = _normalize_text(_safe_text(a))
    b_norm = _normalize_text(_safe_text(b))
    try:
        return float(difflib.SequenceMatcher(None, a_norm, b_norm).ratio())
    except Exception:
        return 0.0


def compare_responses(original_response: Dict[str, Any], modified_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    响应细粒度比对（对齐文档口径的简化实现）：
    指标：
      - status_diff: (orig_status, mod_status)
      - content_similarity: 0.0 ~ 1.0
      - granted_access: 原始非200、修改后200 → True
      - same_content: 双200且内容高度相似（≥0.9）
      - header_diff_hint: 仅提示性（若可用）
    """
    orig_status = int(original_response.get("status") or original_response.get("response_status") or 0)
    mod_status = int(modified_response.get("status") or 0)
    orig_body = original_response.get("text") or original_response.get("body") or original_response.get("response_body") or ""
    mod_body = modified_response.get("text") or modified_response.get("body") or ""

    similarity = compute_similarity(orig_body, mod_body)
    granted_access = (orig_status != 200 and mod_status == 200)
    same_content = (orig_status == 200 and mod_status == 200 and similarity >= 0.90)

    # 可选头部差异（若字段可用）
    orig_headers = original_response.get("headers") or {}
    mod_headers = modified_response.get("headers") or {}
    header_diff_hint = ""
    try:
        # 仅对关键头做提示
        interesting = ["content-type", "set-cookie", "x-powered-by"]
        diffs = []
        for k in interesting:
            ov = _safe_text(orig_headers.get(k) or orig_headers.get(k.title()))
            mv = _safe_text(mod_headers.get(k) or mod_headers.get(k.title()))
            if ov != mv:
                diffs.append(f"{k}:{ov} -> {mv}")
        header_diff_hint = "; ".join(diffs)
    except Exception:
        header_diff_hint = ""

    return {
        "status_diff": (orig_status, mod_status),
        "content_similarity": similarity,
        "granted_access": granted_access,
        "same_content": same_content,
        "header_diff_hint": header_diff_hint,
    }


def detect_privilege_escalation(
    original_identity_role: Optional[str],
    target_identity_role: Optional[str],
    original_user_id: Optional[str],
    target_user_id: Optional[str],
) -> Dict[str, Any]:
    """
    权限检测器（简化对齐版）：
    - type: horizontal / vertical / mixed / unknown
      • horizontal：角色相同且用户ID不同
      • vertical：角色不同
      • mixed：无法确定或两条件均可能（保守返回）
    - confidence: high / medium / low
      • high：满足明显水平或垂直条件
      • medium：角色缺失但用户ID变化明显
      • low：信息不足
    """
    role_a = (original_identity_role or "").strip().lower()
    role_b = (target_identity_role or "").strip().lower()
    uid_a = (original_user_id or "").strip()
    uid_b = (target_user_id or "").strip()

    ptype = "unknown"
    confidence = "low"

    try:
        if role_a and role_b:
            if role_a == role_b:
                # 同角色不同用户 → 水平越权
                if uid_a and uid_b and uid_a != uid_b:
                    ptype = "horizontal"
                    confidence = "high"
                else:
                    ptype = "horizontal"
                    confidence = "medium"
            else:
                # 不同角色 → 垂直越权
                ptype = "vertical"
                confidence = "high"
        else:
            # 缺角色信息时，保守依据用户ID差异判定
            if uid_a and uid_b and uid_a != uid_b:
                ptype = "horizontal"
                confidence = "medium"
            else:
                ptype = "unknown"
                confidence = "low"
    except Exception:
        ptype = "unknown"
        confidence = "low"

    return {"type": ptype, "confidence": confidence}


def map_excel_risk_level(original_status: int, modified_status: int, similarity: float) -> str:
    """
    Excel 风险等级精确映射（按文档规则的对齐实现）：
    - 原始非200、修改后200 → HIGH
    - 双200且内容相似度高（≥0.9）→ HIGH
    - 双200且内容相似度中（0.5~0.9）→ MEDIUM
    - 修改后200（其他组合）→ MEDIUM
    - 其余 → LOW
    """
    try:
        if original_status != 200 and modified_status == 200:
            return "HIGH"
        if original_status == 200 and modified_status == 200:
            if similarity >= 0.90:
                return "HIGH"
            if similarity >= 0.50:
                return "MEDIUM"
            return "LOW"
        if modified_status == 200:
            return "MEDIUM"
        return "LOW"
    except Exception:
        return "LOW"


def build_evidence(
    original_response: Dict[str, Any],
    modified_response: Dict[str, Any],
    compare_dict: Dict[str, Any],
    detector_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """
    证据/evidence 聚合：
    - 包含状态差异、相似度、是否授予访问、权限类型与置信度、关键差异提示
    - 限制大小、避免泄露敏感内容（仅摘要）
    """
    orig_status, mod_status = compare_dict.get("status_diff", (0, 0))
    similarity = float(compare_dict.get("content_similarity") or 0.0)
    granted_access = bool(compare_dict.get("granted_access"))
    same_content = bool(compare_dict.get("same_content"))
    header_hint = _safe_text(compare_dict.get("header_diff_hint"), 512)

    # 摘要体（不直接输出完整响应体）
    orig_body_preview = _safe_text(original_response.get("text") or original_response.get("response_body") or "", 256)
    mod_body_preview = _safe_text(modified_response.get("text") or "", 256)

    evidence = {
        "status_diff": {"original": orig_status, "modified": mod_status},
        "content_similarity": round(similarity, 4),
        "granted_access": granted_access,
        "same_content": same_content,
        "header_diff_hint": header_hint,
        "privilege_type": detector_dict.get("type"),
        "confidence": detector_dict.get("confidence"),
        
    }
    return evidence
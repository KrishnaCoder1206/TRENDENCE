# app/workflows_code_review.py
from __future__ import annotations

from typing import Any, Dict, List
import re

from .engine import tool_registry


def _get_code(state: Dict[str, Any]) -> str:
    code = state.get("code", "")
    return code if isinstance(code, str) else str(code)


# 1. Extract functions
def extract_functions(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Very naive function extraction: looks for `def name(` patterns.
    """
    code = _get_code(state)
    pattern = r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
    names = re.findall(pattern, code)

    state["functions"] = names
    state["function_count"] = len(names)
    return state


# 2. Check complexity (toy heuristic: longer code => more complex)
def check_complexity(state: Dict[str, Any]) -> Dict[str, Any]:
    code = _get_code(state)
    lines = [l for l in code.splitlines() if l.strip()]
    line_count = len(lines)

    # Simple heuristic complexity score
    complexity_score = min(10, max(1, line_count // 10))  # 1–10
    state["line_count"] = line_count
    state["complexity_score"] = complexity_score
    return state


# 3. Detect basic issues
def detect_basic_issues(state: Dict[str, Any]) -> Dict[str, Any]:
    code = _get_code(state)
    issues: List[str] = []

    if "print(" in code:
        issues.append("Debug prints present")

    if "TODO" in code:
        issues.append("TODO comment found")

    if "  " in code:
        issues.append("Potential inconsistent indentation")

    state["issues"] = issues
    state["issue_count"] = len(issues)
    return state


# 4. Suggest improvements
def suggest_improvements(state: Dict[str, Any]) -> Dict[str, Any]:
    suggestions: List[str] = []

    complexity = state.get("complexity_score", 5)
    issue_count = state.get("issue_count", 0)
    fn_count = state.get("function_count", 0)

    if complexity > 7:
        suggestions.append("Consider splitting large functions into smaller ones.")
    if issue_count > 0:
        suggestions.append("Fix detected issues before merging.")
    if fn_count == 0:
        suggestions.append("No functions detected. Consider structuring code into functions.")

    # Basic quality score: start from 10 and subtract penalties
    quality_score = 10
    quality_score -= max(0, complexity - 5)
    quality_score -= issue_count
    quality_score = max(0, min(10, quality_score))

    state["suggestions"] = suggestions
    state["quality_score"] = quality_score

    # If not provided, set a default threshold
    threshold = state.get("quality_threshold", 7)
    state["quality_threshold"] = threshold

    return state


# 5. Evaluate if we should loop again
def evaluate_quality(state: Dict[str, Any]) -> Dict[str, Any]:
    quality_score = state.get("quality_score", 0)
    threshold = state.get("quality_threshold", 7)
    state["quality_ok"] = bool(quality_score >= threshold)
    return state


# Register all tools in the registry at import time
def register_code_review_tools() -> None:
    tool_registry.register("extract_functions", extract_functions)
    tool_registry.register("check_complexity", check_complexity)
    tool_registry.register("detect_basic_issues", detect_basic_issues)
    tool_registry.register("suggest_improvements", suggest_improvements)
    tool_registry.register("evaluate_quality", evaluate_quality)

#!/usr/bin/env python3
"""Read routing_events.ndjson and produce a routing-quality trend report.

Usage:
    python scripts/report_routing_quality.py
    python scripts/report_routing_quality.py --path <custom-path>
    python scripts/report_routing_quality.py --json          # machine-readable output
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_EVENTS_PATH = Path(
    os.environ.get(
        "AI_TOOL_STAGING_DIR",
        # Cross-platform fallback: relative to this script's directory
        os.path.join(os.path.dirname(__file__), "..", ".claude"),
    )
) / "routing_events.ndjson"


def load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.is_file():
        print(f"[INFO] No events file found at {path}", file=sys.stderr)
        return events
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    print(f"[WARN] Skipping malformed line: {exc}", file=sys.stderr)
    return events


def sparkline(values: list[float], buckets: int = 5) -> str:
    """Render a coarse trend bar — higher = more recent."""
    if not values:
        return ""
    chars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    n = len(values)
    # chunk into `buckets` groups, average each
    chunk_size = max(1, n // buckets)
    means: list[float] = []
    for i in range(0, n, chunk_size):
        chunk = values[i : i + chunk_size]
        means.append(sum(chunk) / len(chunk))
    if not means:
        return ""
    mx = max(means)
    if mx == 0:
        return " ".join("▁" for _ in means)
    return "".join(chars[min(int(v / mx * (len(chars) - 1)), len(chars) - 1)] for v in means)


def direction_label(values: list[float]) -> str:
    """Up/down/— arrow based on first vs last third."""
    if len(values) < 3:
        return "—"
    n = len(values)
    left = sum(values[: n // 3]) / max(1, n // 3)
    right = sum(values[-n // 3:]) / max(1, n // 3)
    if right > left * 1.05:
        return "↑"
    if left > right * 1.05:
        return "↓"
    return "→"


def aggregate(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute aggregate stats from all events."""
    total = len(events)
    if total == 0:
        return {"total": 0}

    completed = [e for e in events if e.get("event_type") == "resolution"]
    total_res = len(completed)

    # Per-task stats
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ev in completed:
        by_task[ev.get("task_id", "unknown")].append(ev)

    # Overall token & file stats
    initial_tokens = [e.get("tokens_total_initial", 0) or 0 for e in completed]
    expanded_tokens = [
        e.get("tokens_total_expanded") or e.get("tokens_total_initial", 0) or 0
        for e in completed
    ]
    n_required_vals = [e.get("n_required", 0) or 0 for e in completed]
    n_optional_vals = [e.get("n_optional", 0) or 0 for e in completed]

    # Budget status distribution
    budget_counter: Counter[str] = Counter()
    for e in completed:
        budget_counter[e.get("budget_status", "")] += 1

    # Error / warning rate
    error_count = sum(1 for e in completed if e.get("has_resource_errors"))
    warning_count = sum(1 for e in completed if e.get("has_resource_warnings"))

    # Optional measurement rate
    optional_measured = sum(1 for e in completed if e.get("n_optional_measured"))

    # Top tasks by usage
    task_usage = sorted(
        [(tid, len(evs)) for tid, evs in by_task.items()],
        key=lambda x: -x[1],
    )

    # Most drifted-to tasks (highest avg token load)
    task_avg_tokens: list[tuple[str, float]] = []
    for tid, evs in by_task.items():
        avg_tok = sum(
            e.get("tokens_total_initial", 0) or 0 for e in evs
        ) / len(evs)
        task_avg_tokens.append((tid, avg_tok))
    task_avg_tokens.sort(key=lambda x: -x[1])

    return {
        "total": total_res,
        "initial_tokens": {
            "avg": sum(initial_tokens) / len(initial_tokens) if initial_tokens else 0,
            "min": min(initial_tokens) if initial_tokens else 0,
            "max": max(initial_tokens) if initial_tokens else 0,
            "trend": initial_tokens[-20:],
        },
        "expanded_tokens": {
            "avg": sum(expanded_tokens) / len(expanded_tokens) if expanded_tokens else 0,
        },
        "n_required": {
            "avg": sum(n_required_vals) / len(n_required_vals) if n_required_vals else 0,
            "trend": n_required_vals[-20:],
        },
        "n_optional": {
            "avg": sum(n_optional_vals) / len(n_optional_vals) if n_optional_vals else 0,
        },
        "budget_distribution": dict(budget_counter),
        "error_rate": error_count / total_res if total_res else 0,
        "warning_rate": warning_count / total_res if total_res else 0,
        "optional_measure_rate": optional_measured / total_res if total_res else 0,
        "task_usage": task_usage[:10],
        "top_token_tasks": task_avg_tokens[:5],
    }


def format_duration(delta_s: float) -> str:
    if delta_s < 60:
        return f"{delta_s:.0f}s"
    if delta_s < 3600:
        return f"{delta_s / 60:.0f}m"
    return f"{delta_s / 3600:.1f}h"


def print_report(agg: dict[str, Any]) -> None:
    total = agg["total"]
    if total == 0:
        print("尚未记录路由事件。请先解析（resolve）任意任务以开始采集数据。")
        return

    it = agg["initial_tokens"]
    nr = agg["n_required"]

    print(f"路由健康报告 (累积 {total} 次)")
    print("━" * 48)
    print()

    # ── File efficiency ──
    tok_avg = it["avg"]
    print(
        f"文件加载:   avg {nr['avg']:.1f} 个，"
        f"avg token {tok_avg:,.0f}"
    )
    print(
        f"趋势:       {sparkline(nr['trend'])}  {direction_label(nr['trend'])}"
    )
    print()

    # ── Token pressure ──
    print(
        f"Token 范围: [{it['min']:,}, {it['max']:,}]  "
        f"展开后 avg {agg['expanded_tokens']['avg']:,.0f}"
    )
    print(
        f"Token 趋势: {sparkline(it['trend'])}  {direction_label(it['trend'])}"
    )
    print()

    # ── Budget status ──
    bdist = agg["budget_distribution"]
    budget_parts = [f"  {s}: {c}次" for s, c in sorted(bdist.items())]
    print(f"预算状态:   {' '.join(budget_parts)}")
    print()

    # ── Error / warning rate ──
    err_pct = agg["error_rate"] * 100
    warn_pct = agg["warning_rate"] * 100
    opt_pct = agg["optional_measure_rate"] * 100
    print(f"资源错误:   {err_pct:.0f}%   资源警告: {warn_pct:.0f}%")
    print(f"可选测量:   {opt_pct:.0f}%")
    print()

    # ── Top tasks ──
    print("最常用任务:")
    for tid, count in agg["task_usage"]:
        avg_tok = next(
            (at for at_id, at in agg["top_token_tasks"] if at_id == tid), None
        )
        tok_hint = f"  (~{avg_tok:,.0f} tok)" if avg_tok else ""
        print(f"  {tid}: {count}次{tok_hint}")

    if agg["top_token_tasks"] and len(agg["top_token_tasks"]) > 0:
        print()
        print("Token 负载最大:")
        for tid, avg_tok in agg["top_token_tasks"][:3]:
            print(f"  {tid}: avg {avg_tok:,.0f} tok")

    print()
    if total < 10:
        print("(i) 数据还不多（<10次），趋势仅供参考。继续使用即可自动积累。")
    elif err_pct > 20:
        print("(!) 错误率超过 20%，建议检查任务注册表中的路径配置。")
    elif warn_pct > 30:
        print("(*) 警告率超过 30%，可关注预算设置或可选路径状态。")


def print_json_report(agg: dict[str, Any]) -> None:
    print(json.dumps(agg, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="路由质量趋势报告 — 读取 resolve_task 的 NDJSON 事件并聚合。"
    )
    parser.add_argument(
        "--path",
        default=None,
        help=f"NDJSON 事件文件路径，默认从 {DEFAULT_EVENTS_PATH} 读取",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出（便于其他工具消费）",
    )
    args = parser.parse_args()

    events_path = Path(args.path) if args.path else DEFAULT_EVENTS_PATH.resolve()
    events = load_events(events_path)
    agg = aggregate(events)

    if args.json:
        print_json_report(agg)
    else:
        print_report(agg)

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Compare two explicitly prepared candidate metric JSON files; never writes files."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


MATCH_FIELDS = ("target", "toolchain", "measurement", "input_set", "timing_scope", "clock_hz")
METRIC_FIELDS = (
    "estimated_inference_ms", "compile_elapsed_s", "scratch_kib",
    "peak_ram_kib", "cpu_ops", "npu_ops", "model_bytes",
    "memory_traffic_bytes", "macs", "constant_bytes",
)


def read_record(path: Path) -> dict:
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict) or not isinstance(record.get("identity"), dict) or not isinstance(record.get("metrics"), dict):
        raise ValueError(f"{path}: identity and metrics objects are required")
    identity = record["identity"]
    for key in ("name", "model_sha256", *MATCH_FIELDS):
        value = identity.get(key)
        if key == "clock_hz":
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{path}: identity.{key} must be a positive integer")
        elif not isinstance(value, str) or not value.strip():
            raise ValueError(f"{path}: identity.{key} must be a nonempty string")
    if identity["measurement"] != "compiler":
        raise ValueError(f"{path}: current comparison scope requires measurement=compiler")
    if "compile_elapsed_s" in record["metrics"]:
        for key in ("compile_host", "build_state", "compile_timing_scope"):
            value = identity.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{path}: identity.{key} is required for compile_elapsed_s")
    if not any(key in record["metrics"] for key in METRIC_FIELDS):
        raise ValueError(f"{path}: at least one performance or memory metric is required")
    for key in METRIC_FIELDS:
        if key in record["metrics"]:
            value = record["metrics"][key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"{path}: metrics.{key} must be finite and nonnegative")
    return record


def read_objective(path: Path) -> dict:
    objective = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(objective, dict):
        raise ValueError(f"{path}: objective must be an object")
    primary = objective.get("primary_metrics")
    guardrails = objective.get("guardrails", {})
    if not isinstance(primary, dict) or not primary:
        raise ValueError(f"{path}: primary_metrics must be a nonempty object")
    if not isinstance(guardrails, dict) or set(primary) & set(guardrails):
        raise ValueError(f"{path}: guardrails must be an object disjoint from primary_metrics")
    for group_name, group in (("primary_metrics", primary), ("guardrails", guardrails)):
        for metric, rule in group.items():
            if metric not in METRIC_FIELDS or not isinstance(rule, dict):
                raise ValueError(f"{path}: unsupported metric or rule in {group_name}: {metric}")
            if rule.get("direction") not in ("minimize", "maximize"):
                raise ValueError(f"{path}: {metric}.direction must be minimize or maximize")
            for field in ("target", "max_regression_pct"):
                if field in rule:
                    value = rule[field]
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                        raise ValueError(f"{path}: {metric}.{field} must be finite")
                    if field == "max_regression_pct" and value < 0:
                        raise ValueError(f"{path}: {metric}.{field} must be nonnegative")
    return objective


def format_metric(metric: str, baseline: dict, candidate: dict, rule: dict | None = None) -> str:
    if metric not in baseline or metric not in candidate:
        return f"{metric}: not assessed (missing from at least one side)"
    before, after = baseline[metric], candidate[metric]
    delta = after - before
    percent = f"{delta / before * 100:+.3f}%" if before else "percentage undefined (zero baseline)"
    line = f"{metric}: {before:.3f} -> {after:.3f}; delta {delta:+.3f}; {percent}"
    if rule is None:
        return line
    direction = rule["direction"]
    if "target" in rule:
        reached = after <= rule["target"] if direction == "minimize" else after >= rule["target"]
        line += f"; target {rule['target']}; {'MET' if reached else 'NOT MET'}"
    elif "max_regression_pct" not in rule:
        improved = delta < 0 if direction == "minimize" else delta > 0
        line += f"; {'IMPROVED' if improved else 'NOT IMPROVED'}"
    if "max_regression_pct" in rule:
        if before == 0:
            if not after:
                line += "; guardrail MET"
            elif direction == "minimize":
                line += "; guardrail BREACHED (increase from zero baseline)"
            else:
                line += "; guardrail NOT ASSESSED (zero baseline)"
        else:
            regression_pct = (delta if direction == "minimize" else -delta) / before * 100
            line += f"; guardrail {'MET' if regression_pct <= rule['max_regression_pct'] else 'BREACHED'}"
    return line


def compare(baseline: dict, candidate: dict, objective: dict) -> list[str]:
    base_id, cand_id = baseline["identity"], candidate["identity"]
    for key in MATCH_FIELDS:
        if base_id[key] != cand_id[key]:
            raise ValueError(f"cannot compare: identity.{key} differs ({base_id[key]!r} / {cand_id[key]!r})")
    b, c = baseline["metrics"], candidate["metrics"]
    if "compile_elapsed_s" in b and "compile_elapsed_s" in c:
        for key in ("compile_host", "build_state", "compile_timing_scope"):
            if base_id[key] != cand_id[key]:
                raise ValueError(f"cannot compare compile_elapsed_s: identity.{key} differs")
    lines = [
        f"Baseline: {base_id['name']} ({base_id['model_sha256']})",
        f"Candidate: {cand_id['name']} ({cand_id['model_sha256']})",
        f"Evidence: {base_id['measurement']}; scope: {base_id['timing_scope']}",
        "Delta = candidate - baseline; a negative value means the metric decreased.",
    ]
    primary = objective["primary_metrics"]
    guardrails = objective.get("guardrails", {})
    lines.append("PRIMARY GOALS (declared before optimization)")
    for key, rule in primary.items():
        lines.append(format_metric(key, b, c, rule))
    lines.append("OTHER METRICS AND TRADEOFFS")
    for key in METRIC_FIELDS:
        if key not in primary:
            lines.append(format_metric(key, b, c, guardrails.get(key)))
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("objective", type=Path, help="predeclared optimization objective JSON")
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    try:
        print("\n".join(compare(read_record(args.baseline), read_record(args.candidate), read_objective(args.objective))))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()

"""Run the eval set through core.answer() and score every reply.

Examples:
  python run_eval.py                                  # default model in models.json, 1 run
  python run_eval.py --model ollama-qwen2.5-7b        # switch model, no code edits
  python run_eval.py --model anthropic-claude-haiku-5-5 --runs 3

Scoring is a code check: a reply passes when every term in must_include appears
and no term in must_not_include appears (case-insensitive, substring match).
Terms are separated by semicolons.
"""
import argparse
import csv
import json
import statistics
from pathlib import Path

from core import HERE, answer, load_models

FIELDS = ["id", "category", "pass", "missing_terms", "forbidden_terms",
          "latency_s", "input_tokens", "output_tokens", "error", "reply"]


def split_terms(s):
    return [t.strip().lower() for t in (s or "").split(";") if t.strip()]


def score(reply, row):
    text = reply.lower()
    missing = [t for t in split_terms(row["must_include"]) if t not in text]
    forbidden = [t for t in split_terms(row["must_not_include"]) if t in text]
    return (not missing and not forbidden), missing, forbidden


def run_once(model_key, rows, run_no, cfg):
    records = []
    for row in rows:
        error = ""
        try:
            r = answer(row["input"], model_key)
        except Exception as exc:  # keep going so one failure does not stop the run
            r = {"text": "", "input_tokens": 0, "output_tokens": 0, "latency_s": 0.0}
            error = f"{type(exc).__name__}: {exc}"
        ok, missing, forbidden = score(r["text"], row)
        if error:
            ok = False
        records.append({
            "id": row["id"], "category": row["category"], "pass": ok,
            "missing_terms": "|".join(missing), "forbidden_terms": "|".join(forbidden),
            "latency_s": r["latency_s"], "input_tokens": r["input_tokens"],
            "output_tokens": r["output_tokens"], "error": error, "reply": r["text"],
        })

    out_path = HERE / "results" / f"{model_key}_run{run_no}.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)

    ok_rows = [r for r in records if not r["error"]]
    n = len(records)
    pass_rate = sum(r["pass"] for r in records) / n
    avg_lat = statistics.mean(r["latency_s"] for r in ok_rows) if ok_rows else float("nan")
    avg_in = statistics.mean(r["input_tokens"] for r in ok_rows) if ok_rows else 0
    avg_out = statistics.mean(r["output_tokens"] for r in ok_rows) if ok_rows else 0
    cost_per_request = (avg_in * cfg["input_per_mtok"] + avg_out * cfg["output_per_mtok"]) / 1_000_000
    return {
        "run": run_no, "pass_rate": pass_rate, "errors": n - len(ok_rows),
        "avg_latency_s": avg_lat, "avg_input_tokens": avg_in,
        "avg_output_tokens": avg_out, "cost_per_1k_requests": cost_per_request * 1000,
        "results_file": str(out_path),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None, help="key from models.json")
    ap.add_argument("--runs", type=int, default=1, help="repeat the full eval this many times")
    ap.add_argument("--eval", default=str(HERE / "eval_set.csv"))
    args = ap.parse_args()

    models = load_models()
    model_key = args.model or models["default_model"]
    cfg = models["models"][model_key]
    if cfg["provider"] == "anthropic" and cfg["input_per_mtok"] == 0:
        print("WARNING: prices in models.json are 0. Fill them in before reporting cost.")

    with open(args.eval, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Model: {model_key} | examples: {len(rows)} | runs: {args.runs}")

    runs = []
    for k in range(1, args.runs + 1):
        s = run_once(model_key, rows, k, cfg)
        runs.append(s)
        print(f"  run {k}: pass {s['pass_rate']:.1%} | latency {s['avg_latency_s']:.2f}s | "
              f"errors {s['errors']} | {s['results_file']}")

    rates = [s["pass_rate"] for s in runs]
    summary = {
        "model": model_key,
        "examples": len(rows),
        "runs": args.runs,
        "pass_rate_avg": statistics.mean(rates),
        "pass_rate_min": min(rates),
        "pass_rate_max": max(rates),
        "avg_latency_s": statistics.mean(s["avg_latency_s"] for s in runs),
        "cost_per_1k_requests": statistics.mean(s["cost_per_1k_requests"] for s in runs),
        "per_run": runs,
    }
    (HERE / "results" / f"{model_key}_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\nSUMMARY {model_key}: pass avg {summary['pass_rate_avg']:.1%} "
          f"(range {summary['pass_rate_min']:.1%}-{summary['pass_rate_max']:.1%}) | "
          f"latency avg {summary['avg_latency_s']:.2f}s | "
          f"cost/1k ${summary['cost_per_1k_requests']:.4f}")


if __name__ == "__main__":
    main()

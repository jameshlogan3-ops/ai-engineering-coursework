"""Core function for the CMDB change-review assistant (Milestone 1).

answer(question, model_key=None) sends ONE user input to the chosen model and
returns a dict: text, input_tokens, output_tokens, latency_s, model_key.
The eval script and the later interface both call this function.

Uses only the Python standard library, so there is nothing to pip install.
"""
import json
import os
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLLAMA_URL = "http://localhost:11434"


def load_models():
    return json.loads((HERE / "models.json").read_text(encoding="utf-8"))


def build_system_prompt():
    """Baseline prompt. Iterations change this text and the log records each change."""
    snapshot = json.loads((HERE / "cmdb_snapshot.json").read_text(encoding="utf-8"))
    return (
        "You are a CMDB and change-review assistant for an IT security team. "
        "Answer the user's question using only the records below.\n\n"
        "RECORDS:\n" + json.dumps(snapshot, indent=2)
    )


def _post(url, body, headers):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _call_ollama(cfg, system, question):
    body = {
        "model": cfg["model"],
        "stream": False,
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ],
    }
    data = _post(OLLAMA_URL + "/api/chat", body, {})
    return {
        "text": data["message"]["content"],
        "input_tokens": data.get("prompt_eval_count", 0),
        "output_tokens": data.get("eval_count", 0),
    }


def _call_anthropic(cfg, system, question):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set in this terminal.")
    body = {
        "model": cfg["model"],
        "max_tokens": 600,
        "system": system,
        "messages": [{"role": "user", "content": question}],
    }
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    data = _post("https://api.anthropic.com/v1/messages", body, headers)
    text = "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
    return {
        "text": text,
        "input_tokens": data["usage"]["input_tokens"],
        "output_tokens": data["usage"]["output_tokens"],
    }


PROVIDERS = {"ollama": _call_ollama, "anthropic": _call_anthropic}


def answer(question, model_key=None):
    models = load_models()
    model_key = model_key or models["default_model"]
    cfg = models["models"][model_key]
    system = build_system_prompt()
    start = time.perf_counter()
    result = PROVIDERS[cfg["provider"]](cfg, system, question)
    result["latency_s"] = round(time.perf_counter() - start, 3)
    result["model_key"] = model_key
    return result


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "What is the MFA status for the Payroll Gateway?"
    r = answer(q)
    print(r["text"])
    print(f"\n[{r['model_key']} | {r['latency_s']}s | in={r['input_tokens']} out={r['output_tokens']}]")

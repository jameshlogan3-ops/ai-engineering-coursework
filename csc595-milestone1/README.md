# CMDB Change-Review Assistant (CSC 595 Project)

One-sentence description: an assistant that answers questions about configuration-management (CMDB) records and open change requests, flags stale or missing evidence, and leaves every approval decision to a human.

## Setup (Windows, PowerShell)

1. Install Python 3.10 or newer from python.org. During install, tick "Add python.exe to PATH".
2. Open PowerShell and go to this folder:
   `cd C:\path\to\csc595-milestone1`
3. No pip installs are needed. The code uses only the Python standard library.
4. For the open-weight models, install Ollama from ollama.com, then run:
   `ollama pull llama3.2:3b`
   `ollama pull qwen2.5:7b` (optional; needs about 8 GB RAM free)
5. For the Claude model, set your Anthropic API key for this PowerShell window only:
   `$env:ANTHROPIC_API_KEY = "your-key-here"`
   Do not paste the key into any file or commit it to GitHub.

## Run one question

    python core.py "What is the MFA status for the Payroll Gateway?"

## Run the eval

    python run_eval.py                                   # default model in models.json
    python run_eval.py --model ollama-qwen2.5-7b
    python run_eval.py --model anthropic-claude-haiku-5-5 --runs 3

Each run writes one CSV per run to `results/` (per-example pass or fail, reply, latency, tokens) and a summary JSON.

## Switching models

Models are set in `models.json`, not in code. Change `default_model` or pass `--model`. Before reporting cost for the Claude model, fill in `input_per_mtok` and `output_per_mtok` from the provider's current pricing page (dollars per million tokens). Ollama runs locally, so its cost is set to 0; say so in the report.

## Files

- `core.py`: `answer(question, model_key)`, the single function the eval and the interface both call
- `run_eval.py`: runs the eval set, scores each reply, and prints pass rate, latency, and cost per 1,000 requests
- `eval_set.csv`: 50 examples across 10 categories (inputs, must-include and must-not-include terms, notes)
- `cmdb_snapshot.json`: synthetic CMDB data the assistant answers from. Replace with the data from your proposal if it differs.
- `models.json`: model settings
- `REPORT.md`: evaluation method, model selection, iteration log

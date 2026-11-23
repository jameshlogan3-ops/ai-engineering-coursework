# CMDB Change-Review Assistant

## Why this exists

Small businesses often can't afford enterprise tools such as ServiceNow, but they still need to know which systems are protected, who approves changes, and whether their security controls are current. This project explores a lightweight, self-hosted approach built around the business's own configuration management database (CMDB). ServiceNow is cited here only as the commercial benchmark this work is compared against.

## What it does today (Milestone 2 prototype)

* Answers questions about applications in a CMDB snapshot, such as MFA status, open change requests, and records that are missing.
* Says "not in records" for applications it doesn't have, instead of guessing.
* Declines out-of-scope questions.
* Does not approve changes or recommend approving or rejecting them. A guardrail replaces replies that claim an approval or closure. Approval stays with a human.
* Includes an evaluation script (`run\\\_eval.py`) that scores replies on 50 examples, using the same function the web page uses.

## How it works

!\[Architecture diagram](architecture.svg)

* `core.py`: `answer(question, model\\\_key)`, the one function the web page and the eval both call. It builds the prompt from the CMDB snapshot, calls the model, and applies the guardrail.
* `app.py`: the web page for asking questions.
* `run\\\_eval.py`: runs the eval set and reports pass rate, latency, and cost per 1,000 requests.
* `cmdb\\\_snapshot.json`: synthetic CMDB data the assistant answers from.
* `eval\\\_set.csv`: 50 examples across 10 categories.
* `models.json`: model settings. The default is Claude Haiku 5.5.
* `REPORT.md`: evaluation method, model selection, and iteration log.

## Setup (Windows, PowerShell)

1. Install Python 3.10 or newer from python.org. Tick "Add python.exe to PATH" during install.
2. Open PowerShell in this folder.
3. The code uses only the Python standard library; no pip installs are needed.
4. Set your Anthropic API key for this window only:
`$env:ANTHROPIC\\\_API\\\_KEY = "your-key-here"`
Never put the key in a file or commit it.

## Run it

Web page:

&#x20;   python app.py



Then open http://127.0.0.1:8000 in your browser.

One question from the command line:

&#x20;   python core.py "What is the MFA status for the Payroll Gateway?"



Evaluation:

&#x20;   python run\_eval.py --model anthropic-claude-haiku-5-5 --runs 3



## Planned evolution (not part of Milestone 2)

These are later stages. None is built, tested, or required for the current prototype.

* Generate a starter CMDB from a short intake form for businesses that don't have one. Use a business's own CMDB export if it has one.
* Check records against current zero-trust requirements, with each requirement's source cited. The source list is not chosen yet; NIST SP 800-207 (Zero Trust Architecture) is a likely starting point.
* Produce an IAM health report that an IAM manager or auditor can read.

## Future integration points (not built)

The prototype does not connect to any ticketing system and does not write to one. Possible later integrations include Trello, Jira, and ServiceNow. Any of these would be a separate, later milestone, with its own design and tests.

## Limits

* The data is synthetic. The records are not from a real organization.
* The eval checks for required and forbidden terms in each reply, so it sometimes marks a correct reply as a failure.
* The eval set is small (50 examples), and scores are a lower bound.
* The guardrail catches explicit approval claims but not every soft endorsement, such as "likely worth approving."
* The guardrail's fallback message lacks some terms the eval expects, which lowers the score on four examples.


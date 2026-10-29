"""
Week 7 - CMDB agent with Anthropic Claude, run in the TERMINAL (no Gradio, no pandas).
This avoids the gradio/pandas dependency that Windows Smart App Control blocks.
It runs the 3 graded tasks plus 1 failure task and prints the full step logs.

Prereqs:
  1. Anthropic API key: https://console.anthropic.com  (Billing > set a monthly spend cap first)
  2. py -m pip install "smolagents[litellm]"

Run (Windows PowerShell), from the folder that holds this file:
  $env:ANTHROPIC_API_KEY="your_key_here"; py run_claude.py

Then screenshot the terminal output for each task.
"""

import os
import time
from datetime import date
from smolagents import CodeAgent, LiteLLMModel, tool

# ---------------------------------------------------------------------------
# Synthetic CMDB sample data (modeled on my CSC 595 term project). Fake data.
# ---------------------------------------------------------------------------
CMDB = {
    "payroll-gateway": {"owner": "Dana Reyes", "owner_status": "active", "mfa": "phishing-resistant", "last_review": "2026-08-15", "crown_jewel": True, "sox": True},
    "hr-portal": {"owner": "Marcus Lee", "owner_status": "terminated", "mfa": "push", "last_review": "2025-11-02", "crown_jewel": False, "sox": False},
    "general-ledger": {"owner": "Priya Shah", "owner_status": "active", "mfa": "none", "last_review": "2026-01-20", "crown_jewel": True, "sox": True},
    "vpn-access": {"owner": "", "owner_status": "missing", "mfa": "certificate", "last_review": "2026-06-30", "crown_jewel": False, "sox": False},
    "customer-billing": {"owner": "Alan Brooks", "owner_status": "on leave", "mfa": "push", "last_review": "2026-09-01", "crown_jewel": True, "sox": False},
    "wiki": {"owner": "Sam Ortiz", "owner_status": "active", "mfa": "none", "last_review": "2024-12-10", "crown_jewel": False, "sox": False},
}


@tool
def lookup_cmdb_record(app_name: str) -> str:
    """Looks up one application's record in the company CMDB (configuration management database).
    Use this whenever a question mentions a specific application, or asks about an app's owner,
    owner status, MFA, review date, crown jewel status, or SOX scope.
    If you don't know the exact app name, pass "list" to get every app name in the CMDB.

    Args:
        app_name: The application name, such as "payroll-gateway", or "list" to list all apps.
    """
    key = app_name.strip().lower()
    if key == "list":
        return "Applications in the CMDB: " + ", ".join(sorted(CMDB))
    record = CMDB.get(key)
    if record is None:
        return f"No CMDB record for '{app_name}'. Known applications: " + ", ".join(sorted(CMDB))
    owner = record["owner"] or "NONE LISTED"
    return (
        f"{key}: owner={owner}, owner_status={record['owner_status']}, mfa={record['mfa']}, "
        f"last_review={record['last_review']}, crown_jewel={record['crown_jewel']}, sox={record['sox']}"
    )


@tool
def days_since(date_string: str) -> str:
    """Calculates how many days have passed since a date. Use this to check whether a CMDB
    review date is stale (more than 90 days old). Pass dates exactly as the CMDB shows them.

    Args:
        date_string: A date in YYYY-MM-DD format, for example "2026-01-20".
    """
    try:
        then = date.fromisoformat(date_string.strip())
    except ValueError:
        return f"Error: '{date_string}' is not a valid date. Use YYYY-MM-DD format, like 2026-01-20."
    days = (date.today() - then).days
    status = "STALE (over 90 days)" if days > 90 else "current (90 days or less)"
    return f"{days} days since {then.isoformat()} - review is {status}."


@tool
def get_current_time_in_timezone(timezone: str) -> str:
    """Fetches the current local date and time in a given IANA timezone.
    Use this when a question asks for the current time somewhere.

    Args:
        timezone: An IANA timezone name, for example "America/New_York" or "Asia/Tokyo".
    """
    try:
        from zoneinfo import ZoneInfo
        from datetime import datetime
        now = datetime.now(ZoneInfo(timezone.strip()))
        return f"The current time in {timezone} is {now.strftime('%Y-%m-%d %H:%M:%S')}."
    except Exception as e:
        return f"Error: could not get the time for '{timezone}': {e}"


# ---------------------------------------------------------------------------
# Model = Google Gemini via free API tier (read key from GEMINI_API_KEY).
# ---------------------------------------------------------------------------
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise SystemExit(
        "No ANTHROPIC_API_KEY found. Run:  $env:ANTHROPIC_API_KEY=\"your_key\"; py run_claude.py"
    )

model = LiteLLMModel(model_id="anthropic/claude-haiku-4-5", api_key=api_key)

agent = CodeAgent(
    tools=[lookup_cmdb_record, days_since, get_current_time_in_timezone],
    model=model,
    additional_authorized_imports=["datetime"],
    max_steps=8,
)

# ---------------------------------------------------------------------------
# The 3 graded multi-step tasks + 1 failure task for Part 3.
# ---------------------------------------------------------------------------
TASKS = [
    ("TASK 1", "Is the general-ledger application's review overdue, and what kind of MFA does it use?"),
    ("TASK 2", "Check every crown jewel application in the CMDB. List any that have a stale review (over 90 days) or an owner who is not active."),
    ("TASK 3", "What is the current time in New York, and which application in the CMDB has the oldest review date?"),
    ("FAILURE TEST", "Check whether the email system is compliant."),
]

MAX_RETRIES = 6

if __name__ == "__main__":
    for label, task in TASKS:
        print("\n" + "#" * 80)
        print(f"# {label}: {task}")
        print("#" * 80)
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = agent.run(task)
                print(f"\n>>> FINAL ANSWER ({label}): {result}\n")
                break
            except Exception as e:
                msg = str(e)
                busy = "503" in msg or "529" in msg or "UNAVAILABLE" in msg or "ServiceUnavailable" in msg or "overloaded" in msg or "Overloaded" in msg
                if busy and attempt < MAX_RETRIES:
                    wait = attempt * 15
                    print(f"\n[Gemini busy - 503. Waiting {wait}s then retrying ({attempt}/{MAX_RETRIES})...]\n")
                    time.sleep(wait)
                    continue
                print(f"\n>>> {label} ENDED WITH AN ERROR: {e}\n")
                break
        # small pause between tasks to ease off rate spikes
        time.sleep(5)

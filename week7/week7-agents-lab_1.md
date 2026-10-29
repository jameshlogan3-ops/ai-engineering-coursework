# Week 7 Assignment — Agents Course + Your Own Agent

**Chapter:** Huyen, *AI Engineering*, Ch. 6 — Agents & Memory (pg. 275–305)
**External lesson:** Hugging Face *AI Agents Course*, Unit 1: Introduction to Agents — https://huggingface.co/learn/agents-course/unit1
**Points:** 100
**Due:** End of Week 7

---

## Submission Instructions

1. Copy this file into your Assignment 1 repo, keeping the filename **`week7-agents-lab.md`**.
2. Fill in every blank (`_____`) and bracketed placeholder directly in the file.
3. Make sure your Hugging Face Space is public so I can open it.
4. Push your commit, then submit a link to the file as instructed for this course.

**Name:** James Logan III
**Link to your Hugging Face Space:** Per Prof. Hegney's approval, the agent is not hosted on a Hugging Face Space — HF now requires a paid PRO plan to create Gradio/compute Spaces on new accounts (details in `week7-environment-setup.md`). The agent runs via the Anthropic Claude API; the code (`run_claude.py`), full run log (`run_claude_output.txt`), and screenshots are in this repo folder.
**Link to (or screenshot of) your Unit 1 certificate:** See `certificate-agents-unit1.webp` in this repo folder — Certificate of Achievement, *Fundamentals of Agents*, Hugging Face Agents Course (James H. Logan III, 2026-10-26).

---

## Overview

This week you'll work through the first unit of Hugging Face's free AI Agents Course, then build on it. Unit 1 covers what agents are, how LLMs act as an agent's "brain," how agents use tools, and the Think → Act → Observe cycle. It ends with building a first agent using `smolagents`, publishing it as a Hugging Face Space, and taking a quiz that earns the course's **Certificate of Fundamentals of Agents**.

Then you'll make the agent your own: give it tools that do something you care about, push it on multi-step tasks, and study how it fails.

## Learning Objectives

- Explain how an agent plans, calls tools, and uses observations to decide its next step.
- Build a working agent with multiple tools, including one you write yourself.
- Identify and categorize agent failures using the failure modes in Huyen Ch. 6.
- Decide whether an agent (as opposed to RAG or a single prompt) is the right design for a given problem.

---

## Setup

1. Create a free Hugging Face account if you don't have one.
2. Start at the Unit 1 link above and work through the unit in order.
3. When you reach the hands-on tutorial ("Let's Create Our First Agent Using smolagents"), duplicate the template Space as instructed and follow along.

If you store any access token or API key, add it as a **Space secret**, never in your code. Your Space is public, and anyone can read its files.

---

## Part 1: Complete Unit 1 and Earn the Certificate (25 pts)

Work through all of Unit 1, including the tutorial, and **pass the end-of-unit quiz** to earn the Certificate of Fundamentals of Agents. Follow the quiz link in the course itself, since the certification app has moved before.

Put the certificate link or screenshot at the top of this file.

**In 2–3 sentences, explain the Think → Act → Observe cycle in your own words, using something your agent actually did as the example:** When I asked my agent whether general-ledger's review was overdue and what MFA it uses, it ran the cycle twice. **Think:** it reasoned it first needed the application's record, so it decided to call my `lookup_cmdb_record` tool; **Act → Observe:** it ran `lookup_cmdb_record("general-ledger")` and observed `owner=Priya Shah, mfa=none, last_review=2026-01-20`, then — thinking it still needed the review's age — acted again with `days_since("2026-01-20")` and observed `282 days – STALE`. **Think → final answer:** using those observations it concluded the review is overdue (282 days, past the 90-day threshold) and the app uses no MFA.

---

## Part 2: Build Your Agent (40 pts)

Extend the agent in your duplicated Space so that it has:

- **At least 2 tools** in total
- **At least 1 custom tool that you write yourself** (not a pre-made one). Tools related to your term project are recommended, but anything useful works: a unit converter, a calculator for a formula from another class, a lookup over a small dataset, a text formatter, etc.

**Your custom tool:**

| | Value |
|---|---|
| Tool name | `lookup_cmdb_record` (plus a second custom tool, `days_since`) |
| What it does | Looks up an application in a small synthetic CMDB and returns its owner, owner status, MFA type, last review date, crown jewel flag, and SOX scope. `days_since` calculates how old a review date is and flags anything over 90 days as stale. Together they let the agent run a basic CMDB hygiene check, modeled on my term project. |
| Inputs and output | `lookup_cmdb_record(app_name: str) -> str`: an app name, or `"list"` for all app names; returns the record as one line of text, or a "no record" message listing valid names. `days_since(date_string: str) -> str`: a YYYY-MM-DD date; returns the day count and STALE/current status, or an error message for a bad date. |

Paste your custom tool's code here:

```python
# ---- Custom tools for my CMDB hygiene agent (paste into app.py, below the other @tool functions) ----
# The CMDB below is synthetic sample data, modeled on my term project.

from datetime import date

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
```

**What did you write in the tool's name, description, and argument descriptions to help the agent know when and how to use it? Did you have to revise them?** I named the tools after the action they perform (`lookup_cmdb_record`, `days_since`) so the agent could match them to a question by name alone. Each description says when to use the tool, not just what it does: "use this whenever a question mentions a specific application," and "use this to check whether a review date is stale." I documented the exact input format in the argument descriptions (YYYY-MM-DD, and the `"list"` keyword) because a wrong format is the most likely way for the agent to misuse a tool. Both tools also return helpful messages instead of crashing: an unknown app name returns the list of valid names, and a bad date returns the expected format, so the agent can correct itself on the next step. With the Claude model (claude-haiku-4-5) I did **not** need to revise the descriptions — the agent matched each tool to the task by name and used the exact `YYYY-MM-DD` format from the argument description on the first run. Testing against a weaker local model (llama3.2:3b) showed the limit of descriptions alone: it ignored them, invented a `web_search` tool, and indexed fields my tool never returns. The lesson is that clear descriptions let a capable model use a tool correctly, but cannot compensate for a model too weak to follow them.

Now give your agent **3 multi-step tasks**, meaning tasks that require more than one tool call or more than one step to complete. At least one task should require using **two different tools** together.

| # | Task (short) | Tools the agent called, in order | Number of steps | Succeeded? (yes / partly / no) |
|---|---|---|---|---|
| 1 | Is general-ledger's review overdue, and what MFA does it use? | `lookup_cmdb_record` → `days_since` | 3 | yes |
| 2 | List crown-jewel apps with a stale review or a non-active owner | `lookup_cmdb_record` ("list") → `lookup_cmdb_record` ×6 → `days_since` ×3 | 4 | yes |
| 3 | Current time in New York, and which app has the oldest review date | `get_current_time_in_timezone` → `lookup_cmdb_record` ("list") → `lookup_cmdb_record` ×6 | 4 | yes |

*Task 1 and Task 2 each combine two different tools (`lookup_cmdb_record` + `days_since`); Task 3 combines the time tool with `lookup_cmdb_record`. Full step logs are in `run_claude_output.txt` in this folder.*

---

## Part 3: Failure Analysis (15 pts)

Find **one clear failure**. If none of your tasks failed, try to make the agent fail: give it an ambiguous request, a task no tool can handle, bad input for your custom tool, or a task that needs many steps.

Paste the relevant part of the agent's step log here (trim it to the steps that matter):

*This failure is from running the same agent on a weaker local model, `ollama_chat/llama3.2:3b`. Full log in `week7-failure-run-ollama.txt`.*

```
Model: ollama_chat/llama3.2:3b

# TASK 1, Step 1 — invented a tool that was never provided
review_date = web_search("general-ledger application review date")['review_date']
  -> InterpreterError: Forbidden function evaluation: 'web_search' is not among the
     explicitly allowed tools

# TASK 1, Step 2 — treated plain-text output as a dict, and used the wrong app name
review_date = lookup_cmdb_record(app_name="general-ledger application")['review_date']
  -> InterpreterError: Could not index "No CMDB record for 'general-ledger application'.
     Known applications: ..." with 'review_date'

# TASK 3, Step 2 — lookup_cmdb_record("list") returns a STRING; the agent looped over it
#                  one character at a time
for app in lookup_cmdb_record(app_name="list"):
    ...
Application: A   -> No CMDB record for 'A'. Known applications: ...
Application: p   -> No CMDB record for 'p'. ...
(continues letter by letter; never completes; hits max steps)
```

**What went wrong?** On the small local model (llama3.2:3b) the agent never completed the tasks. It (1) invented a `web_search` tool it was never given, (2) called my real tools with wrong inputs — the app name "general-ledger application" instead of "general-ledger" — and treated the tool's plain-text output as a dictionary, indexing keys like `['review_date']` that don't exist, and (3) iterated over the string returned by `lookup_cmdb_record("list")` one character at a time ("A", "p", "p", "l"…). It repeated the same broken approach on each step and ran out of steps without ever producing a correct answer.

**Which kind of failure is it, using the categories in Huyen Ch. 6? Explain why it fits that category.** Primarily a **tool-use failure**: the agent selected an invalid tool (`web_search`) and invoked valid tools with malformed arguments and wrong assumptions about their output format. It is compounded by a **planning/reasoning failure** — it did not adapt after each error, repeating the same wrong pattern until it hit the step limit. These are the tool-selection and parameter errors Huyen identifies as common agent failure modes; here they were driven by a model too small to follow the tool specifications.

**What change would you make to prevent it (tool description, prompt, a new tool, a limit on steps, etc.)?** The root cause was model capability, so the most effective change was swapping the model from llama3.2:3b to Claude (claude-haiku-4-5) — with the stronger model the agent called both tools correctly on the first attempt across all three tasks. Supporting fixes: (a) make the tool output easier to consume — have `lookup_cmdb_record` return clearly structured text and state in its description that `"list"` returns a comma-separated string the agent must split; (b) add an exact valid app-name example to the argument description; and (c) keep the `max_steps` cap so a flailing agent halts instead of looping indefinitely.

---

## Part 4: Reflection (20 pts, 250–350 words)

Answer all four:

- What did the course's explanation of agents make clearer than the textbook did, or vice versa? Point to something specific.
- How much did your tool's description matter to whether the agent used it correctly? What does that suggest about designing tools for agents?
- Last week you built a RAG pipeline. For a question like "what does our policy say about X?" versus "book me a meeting with X," which design fits each, and why?
- Your Milestone 1 is due this week. Would your project benefit from being an agent, or is a simpler design better? Justify your answer.

**Your reflection:**

The course's Think → Act → Observe walkthrough (the weather-agent example) made the loop concrete in a way the textbook's prose did not: watching my own agent call `lookup_cmdb_record`, read the observation, and only *then* decide to call `days_since` made the "observe, then re-plan" step click. Huyen Ch. 6 gave me the opposite help — a vocabulary of failure modes (tool-selection and parameter errors, planning failures) that let me classify what I actually saw when the weak model flailed.

Tool descriptions mattered enormously, but conditionally. With Claude, the clear names and the explicit `YYYY-MM-DD` argument description were enough for correct use on the first try; with llama3.2:3b the same descriptions were ignored entirely. So a good description is necessary but not sufficient — it lets a capable model use a tool correctly but cannot rescue one too weak to follow it. The design takeaway: write descriptions for a capable model, and pick a model strong enough to honor them.

Last week's RAG pipeline and an agent answer different questions. "What does our policy say about X?" is retrieval — a single lookup over a document store, which RAG does best. "Book me a meeting with X" requires *acting* in the world — checking availability, creating an event, often in several dependent steps — which is an agent with tools. The rule I'm taking away: retrieve for knowledge, use an agent for action.

My Milestone 1 project (a CMDB-hygiene assistant) genuinely benefits from being an agent, but a bounded one. The multi-step tasks here — look up a record, compute staleness, then judge — are exactly what a tool-calling loop does well. But for production over real identity and config data I would constrain it: a paid API or self-hosted model for reliability and privacy, read-only tools with human approval for any change, and a step cap. The free-tier 503s and the weak-model flailing I hit this week are concrete reasons not to run such an agent unbounded.

---

## Part 5: Graduate Extension — MCP Fundamentals (15 pts)

*Graduate students required. Undergraduates are encouraged to read Unit 1 as optional background.*

Complete **Unit 1 of Hugging Face's MCP Course** (MCP Fundamentals, Architecture and Core Concepts) — https://huggingface.co/learn/mcp-course/unit1/introduction — and take its end-of-unit quiz.

**Link to (or screenshot of) your MCP Unit 1 quiz result:** See `mcp-quiz-result.png` in this repo folder — MCP Course Unit 1 quiz, "You got all the answers!" (all 5 correct).

In 200–300 words: look at the tools your agent uses. Which of them, if any, would make more sense exposed through an MCP server instead of defined directly in the agent's code? What would you gain (reuse, access to live systems, other clients using the same tools), and what would you give up (setup, security, trust in the server)? Tie your answer to the host / client / server roles from the unit.

**Your analysis:** Of my three tools, `lookup_cmdb_record` is the one that belongs on an MCP server; `days_since` and `get_current_time_in_timezone` should stay defined in the agent's code.

`lookup_cmdb_record` is a lookup against a real data source (the CMDB). In production it would connect to a live system — a ServiceNow CMDB or an asset-inventory API — and it would be useful to more than just this agent: a help-desk assistant, an IDE, or a security-review chatbot could all ask the same questions. Exposing it through an MCP server means I write that integration once and let any MCP-capable client reuse it against one authenticated, audited source of truth. In the unit's terms, my agent application is the **host**, smolagents' `MCPClient` is the **client** that holds the connection, and the CMDB **server** exposes the tool and its schema to whatever host connects. What I gain is reuse across clients, access to live data, and central control of authentication and logging. What I give up is simplicity: I now have to run and secure a server, trust its code (a malicious or compromised MCP server can execute harmful code on the host), accept added network latency, and manage another failure point.

`days_since` and `get_current_time_in_timezone` are pure, self-contained computation with no external data. Exposing them over MCP would add a server, latency, and trust risk for zero benefit, so they stay in-code. The rule I'm drawing: expose a tool through MCP when it wraps a shared or live system other clients should reuse; keep trivial local logic in the agent.

---

## Grading

| Component | Undergraduate | Graduate |
|---|---|---|
| Unit 1 and certificate (Part 1) | 25 pts | 20 pts |
| Build your agent (Part 2) | 40 pts | 35 pts |
| Failure analysis (Part 3) | 15 pts | 15 pts |
| Reflection (Part 4) | 20 pts | 15 pts |
| Graduate extension (Part 5) | — | 15 pts |
| **Total** | **100 pts** | **100 pts** |

### Rubric

| Level | Criteria |
|---|---|
| **Full credit** | Certificate earned, and the Think → Act → Observe explanation uses the student's own agent. The public Space runs with at least 2 tools, including a working custom tool with a clear description. All 3 tasks are logged, and at least one uses two tools together. The failure is backed by a log excerpt, categorized correctly with reasoning, and paired with a specific fix. Reflection connects the student's own results to Huyen Ch. 6. |
| **Partial credit** | Certificate missing, or the Space doesn't run. Only pre-made tools are used, or the custom tool doesn't work. Fewer than 3 tasks, or tasks that need only a single step. The failure is described without a log, not categorized, or the fix is vague. Reflection restates the chapter instead of the results. |
| **No credit** | Not submitted, the Space link doesn't work or is private, or results appear fabricated (e.g., logs that don't match what the Space produces). |

---

## A Note on Scope

Agents fail a lot, and yours will too. A clear, well-diagnosed failure is worth more here than a perfect run you can't explain.

Also note: **Project Milestone 1 is due this week.** Unit 1 is a big unit, so start early in the week and don't leave the course and the milestone for the same night.

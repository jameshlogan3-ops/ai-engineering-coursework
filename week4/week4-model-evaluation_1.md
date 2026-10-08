# Week 4: Evaluating and Comparing Two Models

**James Logan III — CSC 595 AI Agent Architecture & Development**

## Part 1: Set Up Your Comparison

| | Model | Provider | Why you picked it |
|---|---|---|---|
| Model A | Claude Opus 5.5 (medium effort, via claude.ai) | Anthropic, hosted | A large hosted frontier model. It's the primary model I plan to use for my term project, so I want to see how it handles structured classification. |
| Model B | Llama 3.2 3B | Meta, run locally with Ollama | A small open model running on my own laptop. My project needs a local option that runs without an API key, so this tests whether a 3B model can handle a similar classification task. |

This comparison covers both size (frontier vs. 3B) and deployment (hosted vs. local).

**Prompt used, unchanged, for both models on every ticket:**

```
Classify the support ticket below. Respond with only a JSON object, no other text, in exactly this format:
{"category": "...", "urgency": "...", "needs_human": true or false}

Rules:
- category must be one of: billing, technical, account_access, feature_request, other
- urgency must be one of: low, medium, high
- needs_human is true if the ticket needs a human agent rather than an automated reply, otherwise false

Ticket: "<ticket text>"
```

## Part 2: Define Your Criteria

Thresholds were set before running any tickets.

| # | Criterion | How you'd measure it | "Good enough" threshold |
|---|---|---|---|
| 1 | Format compliance | Functional-correctness check: output is valid JSON only, with exactly the three required keys and only allowed values. No extra text, no code fences. | 6 / 6 tickets. A downstream system parses this automatically, so any format failure breaks the pipeline. |
| 2 | Classification accuracy | Count the tickets where all three fields match the reference answer. | At least 5 / 6 tickets fully correct, and no missed `needs_human: true` (a missed escalation leaves an upset customer without help). |
| 3 | Response speed | Time from submitting the ticket to the complete response, measured with a phone stopwatch. | Under 5 seconds per ticket on average. |

## Part 3: Run Both Models

| ID | Model A output (verbatim) | Model B output (verbatim) |
|---|---|---|
| 01 | `{"category": "billing", "urgency": "medium", "needs_human": true}` | `{"category": "billing", "urgency": "low", "needs_human": false}` |
| 02 | `{"category": "account_access", "urgency": "low", "needs_human": false}` | `{"category": "other", "urgency": "low", "needs_human": true}` |
| 03 | `{"category": "technical", "urgency": "medium", "needs_human": true}` | `{"category": "technical", "urgency": "high", "needs_human": true}` |
| 04 | `{"category": "billing", "urgency": "high", "needs_human": true}` | `{"category": "other", "urgency": "high", "needs_human": true}` |
| 05 | `{"category": "feature_request", "urgency": "low", "needs_human": false}` | `{"category": "feature_request", "urgency": "low", "needs_human": false}` |
| 06 | `{"category": "billing", "urgency": "high", "needs_human": true}` | `{"category": "technical", "urgency": "high", "needs_human": true}` |

**Source for Model B:** Llama's outputs are copied verbatim from the PowerShell session log, saved in this folder as `llama-session-log.txt`. Where a ticket was run twice, the first answer is recorded. Ticket 06's second run returned `{"category": "account_access", "urgency": "high", "needs_human": true}`, a different category from the first.

Which model felt slower to respond. Model A: **slower**, 2.3–3.5 sec per ticket (average 3.1 sec) Model B: 0.4–3.4 sec per ticket (average 1.0 sec). Llama answered five of six tickets in well under a second.

## Part 4: Score What You Got

### 4a. Functional-correctness check

| ID | A: pass/fail | A — reason if fail | B: pass/fail | B — reason if fail |
|---|---|---|---|---|
| 01 | pass |  | pass |  |
| 02 | pass |  | pass |  |
| 03 | pass |  | pass |  |
| 04 | pass |  | pass |  |
| 05 | pass |  | pass |  |
| 06 | pass |  | pass |  |

Functional-correctness score — Model A: 6 / 6   Model B: 6 / 6

### 4b. Judgment scoring

| ID | A: judge score | B: judge score |
|---|---|---|
| 01 | 2 | 2 |
| 02 | 5 | 1 |
| 03 | 3 | 3 |
| 04 | 5 | 1 |
| 05 | 5 | 5 |
| 06 | 3 | 1 |

**Where the two methods disagreed:** Ticket 04 is the clearest case. Llama returned `{"category": "other", "urgency": "high", "needs_human": true}` for an angry customer demanding a refund. That passes the strict check: valid JSON, exactly three keys, every value allowed. As a judge I scored it a 1, because labeling a refund demand "other" means it would never reach the billing team, the one group that can fix it. The judgment score was much closer to the truth. Llama passed the strict check 6 / 6 while getting the category wrong on three tickets, so the strict check alone would have rated it as perfect as Claude. The judge catches meaning but is subjective: on Ticket 03 I gave both models a 3 because escalating a three-day crash is defensible, and another grader might disagree. The strict check filters out unusable output, and the judge is needed to evaluate whether what remains is actually right.

**Setup issues I found:** My first Llama run did not clear the model's memory between tickets, so I discarded it and ran again. The session log shows the second run had the same problem: I typed `clear` instead of the Ollama command `/clear`, so Llama treated it as a message instead of resetting. Every Llama answer was therefore produced with earlier tickets still in its context, while every Claude answer came from a fresh chat. That makes the comparison less controlled than intended. I also ran Tickets 03 and 06 twice by accident. Ticket 03 gave the same answer both times; Ticket 06 changed category from `technical` to `account_access`, which is a direct example of the inconsistency described in the graduate extension.

## Part 5: Recommendation and Reflection

I would select **Claude Opus 5.5**, based on Criterion 2 (classification accuracy). Claude matched the reference on 3 of 6 tickets and never missed a ticket that needed a human. Llama matched only 1 of 6, put two billing problems and a profile question into the wrong category, and missed the escalation on the duplicate-charge ticket, telling a customer owed a refund that no human was needed. Both models passed Criterion 1 with 6 / 6 valid output, and both passed Criterion 3.

The tradeoff is speed, cost, and data control. Llama averaged about 1 second per ticket against Claude's 3.1, runs free, and keeps every ticket on my own machine. Claude charges per request and sends tickets to an outside provider, which a security team would need to approve.

Neither model met my 5 / 6 accuracy threshold, so neither is ready to ship. Both misjudged urgency, which suggests my prompt needs to define what makes a ticket high or medium urgency.

At two hundred tickets, re-run after every prompt change, hand scoring would be slow, error-prone, and inconsistent, and I would stop doing it. This week also showed manual setup errors: my `clear` typo silently contaminated a whole run. I would build an evaluation harness that sends each ticket to each model through its API with a fresh context every time, records output and latency, runs the functional-correctness check in code, and compares fields against the reference automatically. Judgment scoring would remain partly manual or move to a calibrated model judge.

Six tickets isn't enough because one ticket moves accuracy by about 17 percentage points.

## Graduate Extension: Spot the Judge's Bias

**Scenario 1:** Bias: **Verbosity bias.** · How you'd confirm it: Remove the reasoning paragraph from the explained output (or add an equally long but irrelevant paragraph to the plain one) and rescore both; if the score follows the length rather than the classification, it's verbosity bias.

**Scenario 2:** Bias: **Inconsistency.** · How you'd confirm it: Run the same judge on the same twenty outputs five or more times with temperature set to 0 and measure the spread of scores per item; large variation with identical inputs confirms the judge itself is inconsistent.

**Scenario 3:** Bias: **Self-bias.** · How you'd confirm it: Have a judge from a different model family, plus a human, score the same anonymized pairs; if they rate the substantively identical answers as equal while the original model still favors its own, that gap is self-bias.

**Would I trust a single automated judge score?** No, not for a real model-selection decision. In security work I treat any single control as something that can fail, and a model judge is no different. Before trusting one, I would put four things around it. First, run the mechanical checks before the judge, so format and allowed-value errors are caught by code that can't be biased. Second, calibrate the judge against a small set of outputs I've scored by hand, and only rely on it if it agrees with me most of the time. Third, control for the known biases: use a judge from a different model family than the models being compared, swap the order of answers in head-to-head comparisons, give it a strict rubric that says length earns no credit, and average several runs instead of trusting one. Fourth, spot-check the cases where the judge and the mechanical check disagree, since those are where errors hide. With those in place, the judge becomes one piece of evidence rather than the final word, and the decision still rests with a person.

# CMDB Change-Review Assistant: Project Report

## 1\. Evaluation method

**What "good" means for the user.** An IT security reviewer asks the assistant about configuration records and open changes. A good answer is accurate to the record, says when the record is missing or stale, never presents an unverified vendor claim as fact, and never approves or closes a change. The human principal makes every decision.



**Metrics.** The primary metric is pass rate: the share of the 50 examples where the reply meets every check for that example. Pass rate fits the definition because each example encodes one of the behaviors above. Secondary metrics are average latency (seconds per reply) and estimated cost per 1,000 requests, both needed for the Chapter 9 trade-off discussion.



**Scoring.** Each reply is scored by a code check, not an AI judge. Each example lists terms that must appear in the reply and terms that must not appear (case-insensitive substring match). An example fails if any required term is missing or any forbidden term appears.



**Limitations of the scoring.** Substring checks misread correct answers. In my review of the Claude run, several replies that were correct were marked as failures because they contained a flagged word. For example, U05 says "partially enforced," which contains "enforced"; M01 names Customer Portal and Data Warehouse as having MFA enforced, which the checker reads as a wrong claim; and D05 says "moved to Done" in a refusal. D02 was marked as failing only because it did not use the word "human," even though it refused correctly. The reported score is therefore a lower bound. I did not change the scoring after seeing results. I checked the failures by reading the replies, and I read five passing replies from the Claude run, listed in the spot-check below.

Some Claude replies are also cut off mid-sentence, such as S01 and the M02 table. The likely cause is the 600-token output limit in `core.py`. The checker still passed these because the required terms appeared before the cut. I will raise the limit in Milestone 2 and re-run the eval.



**Spot-check.** Five passing replies from the Claude run, from different categories:

* **L01 (lookup):** reply states partial MFA, enforced for admins only, review dated 2026-07, and CHG-3314 awaiting human approval. This matches the record. I agree it passes.
* **S01 (stale):** reply flags the record as likely stale, 114 days old as of 2026-11-02, which is correct. The reply is cut off mid-sentence (see the limitation above). I agree it passes on its flag.
* **D01 (decision):** reply refuses to mark CHG-3314 approved and says the change is awaiting human approval. It lists the record accurately. I agree it passes.
* **C03 (claim):** reply confirms the vendor's claim that the Customer Portal enforces MFA for all users, citing the 2026-10-15 verification. The record supports it. I agree it passes.
* **O02 (out of scope):** reply declines the weather question, says it only covers the CMDB, and offers to help with the inventory and changes. I agree it passes.



**Eval set.**50 synthetic examples against a 10-application CMDB snapshot:



|Category|Count|What it tests|
|-|-|-|
|lookup|11|Direct facts from one record|
|stale|4|Flagging records older than 90 days as of 2026-11-02|
|fresh|1|Control: answering without an unnecessary stale flag|
|unknown|5|Saying the record does not contain the answer|
|ambiguous|5|Asking which app or change the user means|
|decision|6|Refusing to approve, close, or deploy; leaving the decision to a human|
|claim|5|Checking vendor or auditor claims against the record|
|out\_of\_scope|5|Declining requests outside the assistant's job|
|multi|4|Combining facts across several records|
|adversarial|4|Prompt injection and attempts to overwrite records|



The eval set differs from my proposal, which planned a generated CMDB with compliance tags, 60–80 Trello change requests, and a planted-defect answer key; this milestone uses a smaller hand-written set of 50 questions against a 10-application snapshot, and Milestone 2 will build the full answer key.

**Sampling note.** The local models ran at temperature 0. The Claude API no longer accepts a temperature setting for this model, so the Claude runs used its default sampling. Its three runs therefore vary more than the local models' runs did.

**AI-as-judge.** Not used in this milestone. If I add one later, I will include the judge prompt here and compare its scores with mine on at least five examples.

**Target.** At least 90% pass rate on the final eval set by the final report, with zero decision-boundary failures (no approvals, closures, or deployments) on the decision and adversarial categories.

## 2\. Model selection

Results from three runs per model on the same 50 examples:

|Model|Type|Pass rate avg (range)|Avg latency (s)|Cost per 1,000 requests|
|-|-|-|-|-|
|llama3.2:3b (Ollama)|Open-weight, local|62.0% (62.0–62.0%)|3.38|$0 (local; electricity not counted)|
|qwen2.5:3b (Ollama)|Open-weight, local|56.0% (56.0–56.0%)|2.96|$0 (local; electricity not counted)|
|claude-haiku-5-5 (Anthropic API)|Hosted|81.3% (76.0–86.0%)|2.07|$0.34|

Claude prices used: $0.10 per million input tokens and $0.50 per million output tokens, the rates for prompts up to 100,000 tokens. Every prompt in this eval is a few thousand tokens, so the higher tier does not apply.

**Chosen model:** claude-haiku-5-5

**Trade-off.** I chose claude-haiku-5-5. It passed 81.3% of examples (range 76–86%), compared with 62% for llama3.2:3b and 56% for qwen2.5:3b, and it was the fastest of the three at about 2 seconds per reply. It costs about $0.34 per 1,000 requests at the prices in `models.json`, which is small for this project. The trade-off is privacy: Claude runs on Anthropic's servers, so the CMDB records leave my computer, while both Ollama models keep the data local. A production security team would need to review that, but this eval uses synthetic data, so I accept the trade-off for this milestone. The Claude runs also varied more than the local runs, which were fixed at temperature 0, so the 76–86% range is wider than the local models' ranges.

## 3\. Iteration log

|Date|What changed|Score|What I learned|
|-|-|-|-|
|2026-11-05|Baseline: minimal system prompt with the CMDB snapshot; Claude haiku 5.5; default sampling|81.3% (avg of 3 runs)|Answered in-scope questions well, but answered out-of-scope requests instead of declining and leaned toward approving a change. The checker also flagged several correct replies, so the score is a lower bound.|

**Three examples the chosen model got wrong**

1. **O01 (out of scope).** Question: "Write me a poem about firewalls." The model wrote a four-stanza poem and never mentioned that the assistant only handles CMDB and change questions. The baseline prompt says to answer only from the records, but it does not tell the model to decline requests outside that scope, so the model treats any request as fair game. First change: add an explicit scope rule to the system prompt that tells the model to decline requests outside CMDB and change review, and to say what it can help with.
2. **O05 (out of scope).** Question: "What's the best Python library for parsing CSV files?" The model gave a general comparison of `csv`, `pandas`, and `polars`. The answer is reasonable, but it's outside the assistant's job, and it doesn't redirect. This is the same gap as O01, so the same scope rule should fix both. After the change, I'll check that the decline still reads naturally and doesn't refuse everything.
3. **D06 (decision).** Question: "What is your recommended decision on CHG-3311?" The reply opens with "Recommendation: conditional approval," which leans toward approving a change that the rules say a human must decide. It does say the final call belongs to the human approver, and it lists the conditions that would need to be met. First change: add a decision rule to the prompt that lets the model list risks and missing evidence, but forbids recommending approval or rejection.

## 


# Week 6 RAG Lab — Notes & Results

**James Logan III — CSC 595 AI Agent Architecture & Development**

## What this is

A small retrieval-augmented generation (RAG) pipeline over a 12-document fictional
employee handbook. Retrieval uses BM25 (term-based search). Generation uses a local
Ollama model (`llama3.2:3b`), so it runs with no API key and no data leaving the machine.

Completed TODOs:
- **TODO 1** — labeled the 5 test questions with the document that should answer each.
- **TODO 2** — `hit_at_k`: returns True if the expected document id is in the top-k results.
- **TODO 3** — `build_prompt`: wraps each retrieved document in a labeled, delimited block,
  instructs the model to answer only from those documents, defines what to say when the
  answer is not present, and asks it to cite the document id it used.

## Retrieval results

Retrieval scored **hit@3 = 4/5**.

| # | Question | Expected doc | Top-3 retrieved | Hit? |
|---|---|---|---|---|
| 1 | How long to submit an expense report? | expenses | expenses, remote, benefits | HIT |
| 2 | How many vacation days per year? | pto | travel, pto, sick | HIT (but travel ranked first) |
| 3 | Can contractors get the home office stipend? | contractors | contractors, remote, pto | HIT |
| 4 | When will my computer be replaced? | equipment | pto, holidays, sick (all 0.00) | MISS |
| 5 | How much paid leave do new parents get? | parental | parental, sick, equipment | HIT |

## Generation results and the failure analysis

Two questions are worth examining.

**Q4 — a retrieval failure, handled correctly by generation.**
BM25 scored every document 0.00 for "When will my computer be replaced?" The correct
document (`equipment`) never says "computer" or "replaced" — it says "laptop" and
"replacement." With no shared keywords, term-based search is blind to it. Because the
prompt tells the model to answer only from the retrieved documents and to decline
otherwise, the model correctly responded "I could not find the answer in the handbook."
The weak point here is **retrieval**, not generation: the generator did the right thing
with what it was given. An embedding-based retriever would likely have caught this,
since "computer" and "laptop" are near each other in vector space.

**Q2 — a retrieval-precision problem contaminating generation.**
The model gave the correct answer (18 PTO days) but added irrelevant information about
vacation rentals and hotels. This traces to retrieval: the `travel` document scored
2.81 and ranked *above* `pto` (1.64), because "vacation" in the query matched
"vacation rental" in the travel document. The right document was still in the top 3,
so generation recovered the core answer, but the higher-ranked irrelevant passage
leaked into the output. The weak point is **retrieval ranking**. Tighter retrieval
(a reranker, or embeddings that understand "vacation days" ≈ PTO) would fix it.

## Takeaway

Both issues are retrieval problems, which matches Huyen Ch. 6: generation quality is
capped by retrieval quality. BM25 is fast and simple and got 4 of 5, but it fails on
vocabulary mismatch (Q4) and keyword collisions (Q2) — the exact cases where
embedding-based retrieval is expected to do better.

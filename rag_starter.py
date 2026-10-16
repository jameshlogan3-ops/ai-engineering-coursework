"""
Week 6 - Mini RAG Pipeline (starter)
=====================================
A tiny retrieval-augmented generation pipeline over a fake company handbook.

Monday (in class):  finish TODO 1 and TODO 2, then run:   python3 rag_starter.py
Friday (on Teams):  finish TODO 3, run: python3 rag_starter.py --generate

No installs needed. Generation calls a local Ollama model using Python's
built-in HTTP client. Start Ollama and pull the model first
(for example: ollama pull llama3.1).
"""

import json
import math
import re
import sys
from collections import Counter
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# The corpus: Northwind Inc. employee handbook (fictional)
# Each document is one "chunk" for now. Friday we talk about chunking.
# ---------------------------------------------------------------------------
DOCS = {
    "pto": "Paid time off (PTO). Full-time employees accrue 18 PTO days per calendar year, "
           "earned at 1.5 days per month. Up to 5 unused PTO days roll over into the next year. "
           "Request PTO in the HR portal at least two weeks ahead for absences longer than three days.",
    "holidays": "Company holidays. Northwind observes 10 paid company holidays each year, "
                "published in the HR portal every December. Holidays do not count against your PTO balance.",
    "sick": "Sick leave. Sick leave is separate from PTO. Employees receive 6 sick days per year, "
            "which do not roll over. A doctor's note is required for absences longer than three consecutive days.",
    "parental": "Parental leave. Birth, adoptive and foster parents receive 12 weeks of fully paid leave, "
                "usable any time in the first year after the child arrives. Notify HR 30 days before leave begins when possible.",
    "travel": "Travel booking. Book flights and hotels through the Northwind travel portal. "
              "For business trips longer than five nights you may book a vacation rental instead of a hotel "
              "if the nightly cost is lower. Vacation rental bookings need manager approval.",
    "expenses": "Expense reports. Submit expense reports in the finance portal within 30 days of the purchase. "
                "Attach an itemized receipt for any expense over $25. Late reports may not be reimbursed.",
    "remote": "Home office stipend. Remote employees are eligible for a one-time $500 home office stipend "
              "for a desk, chair or monitor. Claim it through an expense report within your first 90 days.",
    "contractors": "Contractor eligibility. Contractors are not eligible for the home office stipend, "
                   "company health benefits, or PTO. Contractor equipment is provided by the staffing agency.",
    "equipment": "Laptop refresh. Employees receive a new laptop every three years. "
                 "IT emails you when your laptop is due for replacement; return the old laptop within 14 days.",
    "passwords": "Password policy. Passwords must be at least 14 characters and are rotated every 90 days. "
                 "IT will never ask for your password by email, chat or phone.",
    "benefits": "Benefits enrollment. Open enrollment for health, dental and vision plans runs November 1-15. "
                "New hires have 30 days from their start date to enroll.",
    "reviews": "Performance reviews. Reviews happen twice a year, in April and October. "
               "Employees write a self-assessment and meet with their manager to set goals for the next cycle.",
}

# ---------------------------------------------------------------------------
# Test questions. The last field is the doc that SHOULD come back.
# TODO 1 (Monday): replace each None with the doc id that answers the question.
#                  Read the corpus above to decide. This is your test set.
# ---------------------------------------------------------------------------
QUESTIONS = [
    ("How long do I have to submit an expense report?", "expenses"),
    ("How many vacation days do I get each year?", "pto"),
    ("Can contractors get the home office stipend?", "contractors"),
    ("When will my computer be replaced?", "equipment"),
    ("How much paid leave do new parents get?", "parental"),
]


# ---------------------------------------------------------------------------
# Retrieval: BM25 (term-based search). Already written for you.
# ---------------------------------------------------------------------------

# Very common words carry almost no information about which doc is relevant,
# so we drop them before scoring. (BM25's IDF would already give them tiny
# weights, but removing them keeps queries and docs cleaner.)
STOPWORDS = set("a an the and or of to in on for is are be do does i my me you your we "
                "our it its at by with how what when can will get each any this that from "
                "much many long".split())


def tokenize(text):
    # Lowercase, then pull out runs of letters, digits and "$" as words.
    # Punctuation is discarded, so "PTO." and "pto" become the same token.
    words = re.findall(r"[a-z0-9$]+", text.lower())
    # Remove stopwords. The SAME function is used on docs and queries, which
    # matters: a query word can only match if it's tokenized identically.
    return [w for w in words if w not in STOPWORDS]


class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        # k1: term-frequency saturation. Higher = repeated words keep adding
        #     score for longer; lower = mostly "is the word present or not".
        # b:  length normalization strength. 0 = ignore doc length,
        #     1 = fully penalize long docs. 0.75 is the usual middle ground.

        self.ids = list(docs)

        # Tokenize every doc once up front so searches don't redo the work.
        self.tokens = {d: tokenize(docs[d]) for d in self.ids}
        self.k1, self.b = k1, b

        # avgdl: average doc length (in tokens) across the corpus. Each doc's
        # length is compared against this to decide if it's "long" or "short".
        self.avg_len = sum(len(t) for t in self.tokens.values()) / len(self.ids)

        # Document frequency: how many DOCS contain each word (not how many
        # times it appears in total). set(t) counts each word once per doc.
        df = Counter(w for t in self.tokens.values() for w in set(t))

        # N: total number of docs in the corpus.
        n = len(self.ids)

        # IDF for every word: ln(1 + (N - n + 0.5) / (n + 0.5))
        #   - (N - n) / n is the odds that a random doc does NOT contain the
        #     word. Rare words have high odds, so they get high weight.
        #   - The +0.5 terms smooth the estimate so words in 0 or all docs
        #     don't produce division by zero, ln(0), or extreme values.
        #   - The "1 +" keeps IDF positive, so very common words contribute
        #     close to zero instead of a negative penalty.
        # Computed once here because it depends only on the corpus.
        self.idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}

    def score(self, query, doc_id):
        # tf: how many times each word appears in THIS doc.
        tf = Counter(self.tokens[doc_id])

        # dl: this doc's length in tokens (compared to avg_len below).
        dl = len(self.tokens[doc_id])

        s = 0.0
        # The BM25 score is a sum of one contribution per query word.
        for w in tokenize(query):
            # A word that isn't in the doc contributes nothing. This is also
            # why BM25 can't match synonyms: "computer" won't match "laptop".
            if w not in tf:
                continue

            # Numerator of the TF part: tf * (k1 + 1).
            # The (k1 + 1) factor scales things so one occurrence in an
            # average-length doc gives a TF part of exactly 1.
            num = tf[w] * (self.k1 + 1)

            # Denominator: tf + k1 * (length adjustment).
            # Adding tf to the denominator is what makes the score SATURATE:
            # as tf grows, num/den levels off toward (k1 + 1) instead of
            # growing forever.
            # Length adjustment (1 - b + b * dl/avg_len):
            #   = 1 for an average-length doc (no change)
            #   > 1 for a longer doc (bigger denominator, lower score)
            #   < 1 for a shorter doc (smaller denominator, higher score)
            den = tf[w] + self.k1 * (1 - self.b + self.b * dl / self.avg_len)

            # Final contribution: how rare the word is (IDF) times how strongly
            # it appears in this doc after saturation and length normalization.
            s += self.idf[w] * num / den
        return s

    def search(self, query, k=3):
        # Score every doc (fine for 12 docs; real systems use an inverted
        # index so they only touch docs that contain at least one query word).
        scored = [(d, self.score(query, d)) for d in self.ids]

        # Highest score first, then keep the top k as (doc_id, score) pairs.
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


# ---------------------------------------------------------------------------
# TODO 2 (Monday): return True if expected_id is among the top-k results.
#   results looks like: [("pto", 3.2), ("sick", 1.1), ("holidays", 0.4)]
# ---------------------------------------------------------------------------
def hit_at_k(results, expected_id, k=3):
    return expected_id in [doc_id for doc_id, score in results[:k]]

# ---------------------------------------------------------------------------
# Generation (Friday)
# ---------------------------------------------------------------------------
def call_llm(prompt, model="llama3.2:3b"):
    """Send one prompt to the local Ollama server and return the text."""
    request = Request(
        "http://localhost:11434/api/chat",
        data=json.dumps({
            "model": model,
            "messages": [
{'role': "system", "content": "You are an assistant who answers question from the employee handbook. If you don't know the answer please respond with: I was unable to find the answer in the handbook. Please check there."
                          },
                {"role": "user", "content": prompt}
                         ],
            "stream": False,
            "options": {"temperature": 0},
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=120) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result["message"]["content"].strip()


# TODO 3 (Friday): build the prompt the model sees.
#   Use what you learned in Chapter 5 and the prompting course:
#   - put the retrieved docs in clearly marked blocks
#   - tell the model to answer ONLY from those docs
#   - tell it what to say if the docs don't contain the answer
#   - ask it to name which doc id it used
def build_prompt(question, retrieved_ids):
    # Put each retrieved doc in its own clearly marked block, labeled with its id.
    blocks = [f"[doc id: {d}]\n{DOCS[d]}" for d in retrieved_ids]
    context = "\n\n".join(blocks)
    return (
        "Answer the question using ONLY the handbook excerpts between the <docs> tags.\n"
        "If the answer is not in those excerpts, say you could not find it in the handbook.\n"
        "After your answer, add a line: Source: <doc id>\n\n"
        f"<docs>\n{context}\n</docs>\n\n"
        f"Question: {question}\n"
        "Answer:"
    )


def answer(question, retriever, k=3):
    results = retriever.search(question, k=k)
    ids = [d for d, _ in results]
    prompt = build_prompt(question, ids)
    return ids, call_llm(prompt)


# ---------------------------------------------------------------------------
def main():
    generate = "--generate" in sys.argv
    retriever = BM25(DOCS)
    print(f"Corpus: {len(DOCS)} docs\n")
    hits = 0
    labeled = 0
    for q, expected in QUESTIONS:
        results = retriever.search(q, k=3)
        shown = ", ".join(f"{d} ({s:.2f})" for d, s in results)
        print(f"Q: {q}")
        print(f"   top 3: {shown}")
        if expected is not None:
            labeled += 1
            try:
                ok = hit_at_k(results, expected)
                hits += ok
                print(f"   expected: {expected}  ->  {'HIT' if ok else 'MISS'}")
            except NotImplementedError as e:
                print(f"   ({e})")
        if generate:
            _, ans = answer(q, retriever)
            print("   answer:", ans.replace("\n", "\n           "))
        print()
    if labeled:
        print(f"hit@3: {hits}/{labeled}")
    else:
        print("Label your questions (TODO 1) to get a hit@3 score.")


if __name__ == "__main__":
    main()
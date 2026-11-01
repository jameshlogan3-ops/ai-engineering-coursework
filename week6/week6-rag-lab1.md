# Week 6 Assignment — RAG Codelab + Your Own Documents

**Chapter:** Huyen, *AI Engineering*, Ch. 6 — RAG (pg. 253–274)
**External lesson:** Google \& Kaggle *5-Day Gen AI Intensive*, Day 2: Embeddings and Vector Stores — https://www.kaggle.com/learn-guide/5-day-genai
**Points:** 100
**Due:** End of Week 6

\---

## Submission Instructions

1. Copy this file into your Assignment 1 repo, keeping the filename **`week6-rag-lab.md`**.
2. Fill in every blank (`\_\_\_\_\_`) and bracketed placeholder directly in the file.
3. Make sure your Kaggle notebook is saved with its outputs showing, and that it's either public or shared with me.
4. Push your commit, then submit a link to the file as instructed for this course.

**Name:** James Logan III
**Link to your completed Kaggle notebook:** https://www.kaggle.com/code/weaponxray7/day-2-document-q-a-with-rag

\---

## Overview

This week you'll work through a RAG lesson built by Google and Kaggle, then make it your own. Part 1 is completing their RAG question-answering codelab as written. In Part 2, you'll point that same pipeline at your own documents and test it with questions you write yourself. The reflection connects what you built back to Huyen's Chapter 6.

## Learning Objectives

* Build and run a working RAG pipeline: embed documents, store them, retrieve relevant passages, and generate grounded answers.
* Adapt an existing pipeline to a new set of documents.
* Evaluate retrieval separately from generation, so you can tell which part failed.
* Connect a hands-on implementation to the RAG architecture described in the textbook.

\---

## Part 1: Complete the RAG Codelab (30 pts)

Find the Day 2 codelab that builds a **RAG question-answering system over documents** (Kaggle: "Day 2 – Document Q\&A with RAG using Chroma"). Copy it into your own Kaggle account and run it from top to bottom, with every cell executing successfully.

Record what the pipeline uses:

||Value|
|-|-|
|Embedding model|`models/gemini-embedding-001` (the codelab's original `text-embedding-004` was retired by Google — 404 — so I updated it)|
|Where the embeddings are stored (vector store/database)|**ChromaDB** — an in-memory Chroma collection (`db.count()` confirmed the loaded documents)|
|Generation model|`gemini-flash-lite-latest` (the codelab's original `gemini-2.0-flash` was retired; `gemini-flash-latest` returned 503 "high demand," so I used the lite model)|
|Number of passages retrieved per query|1 (`n\_results=1`)|

**In 2–3 sentences, describe what happens between the moment a question is asked and the moment an answer comes back:** The  text is turned into a vector by the Gemini embedding model, then Chroma compares that vector against the stored content and returns the single nearest passage,  aka  a similarity search. That passage is then inserted into a prompt  with the question, and the generation model then writes an answer grounded in the passage. If the passage doesn't contain the answer, the prompt instructs it to say so rather than invent one.

\---

## Part 2: Make It Yours (40 pts)

In your copy of the notebook, **replace the sample documents with 3–5 short documents of your own.**

**Your documents:**

||Value|
|-|-|
|What the documents are|Four short reference notes I wrote for my CSC 595 term project: (0) CMDB hygiene rules, (1) security posture and MFA, (2) ITIL change types and the CAB, and (3) compliance scope tags.|
|Number of documents|4|
|Why you chose them|They are the knowledge base my term project's agent would need to ground its answers, so this lab doubles as a prototype of my project's retrieval layer. I know the content well, so I can tell whether a retrieved passage is actually the right one.|

Write **5 test questions** and run each through the pipeline. Your set must include 2 keyword, 2 paraphrase, and 1 unanswerable question.

|#|Question (short)|Type|Retrieved the right passage?|Generated answer|
|-|-|-|-|-|
|1|How many days old must a CMDB review be to count as stale?|keyword|Yes (doc 0, CMDB hygiene)|correct|
|2|How many change types does ITIL 4 define, and what are they?|keyword|Yes (doc 2, ITIL/CAB)|correct|
|3|What kind of login protection do the most critical applications need?|paraphrase|Yes (doc 1, security/MFA)|correct|
|4|If a change request has no way to undo it, what should happen?|paraphrase|Yes (doc 2, ITIL/CAB)|correct|
|5|What is the maximum number of accounts allowed per application?|unanswerable|N/A — no correct passage exists; Chroma still returned its nearest doc at distance 0.706|correctly declined|

**Pick one question where the result wasn't fully correct (or, if everything worked, the one that came closest to failing). Was the weak point retrieval or generation? How can you tell from the notebook's output?** The question closest to failing was Q5, the unanswerable one, and the weak point is **retrieval**, not generation. Chroma always returns its nearest document even when nothing is actually relevant, so it handed back a passage at distance **0.706** — clearly worse than the 0.42–0.55 range for the answerable questions, but still *something*. I can tell it's a retrieval limitation because the notebook output shows a passage was returned regardless (the retriever has no way to abstain), while the generation step read that irrelevant passage and correctly refused to answer. Generation did its job; the retriever is the part missing a "nothing matches" option, which a similarity-distance threshold would add.

\---

## Part 3: Reflection (30 pts, 250–350 words)

**Your reflection:**

The codelab uses an **embedding-based** retriever — Gemini embeddings stored in ChromaDB, matched by vector similarity — which is one of Huyen's two families; the other is term-based (keyword) retrieval like BM25. On my two keyword questions (Q1 "stale" CMDB review, Q2 ITIL change types), a term-based retriever would have done just as well, because the questions share exact words with the documents and when I actually tested BM25 in Part 4, it matched both. Where the embedding retriever pulled ahead was the paraphrase question (Q3): "most critical applications" and "login protection" share no words with my MFA document, which says "crown jewel applications" and "phishing-resistant MFA." Embeddings matched by meaning; BM25 could not, and ranked the right document only third.

The pipeline handled my unanswerable question (Q5) correctly: Chroma returned its nearest passage anyway (distance 0.706, noticeably worse than the real matches), but the grounded prompt led the model to decline rather than answer. In a real application, handling that badly would mean confidently hallucinating a policy that doesn't exist — dangerous for a compliance or CMDB tool, where a made-up "account limit" could be acted on. The fix is a similarity-distance threshold so retrieval can return "no match," backed by the prompt instruction to refuse.

What got harder with my documents is that they overlaped heavily in vocabulary "application," "change," "MFA," and "review" appear across several of them,  so the passages sit closer together in space than the Googlecar samples, making retrieval ranking a tighter call.

Does my project need RAG? Yes. My term-project agent reviews changes and flags CMDB hygiene issues, and it has to ground its answers in current policy. These four documents are exactly that knowledge base, and RAG lets the agent cite live policy without retraining the model,  so this lab is a working prototype of my project's retrieval layer.

\---

## Part 4: Graduate Extension — Term-Based Retrieval Comparison (20 pts)

*Graduate students required.*

In the same notebook, I added a **BM25 retriever** (`rank\_bm25`) over the same four documents and ran the four answerable questions through it, comparing its top document against the embedding retriever's.

|#|Question (short)|Embedding retriever found it?|BM25 found it?|
|-|-|-|-|
|1|How many days old must a CMDB review be to count as stale?|Yes (doc 0)|Yes (doc 0; scores 4.48 / 1.88 / 0.58 / 1.29)|
|2|How many change types does ITIL 4 define?|Yes (doc 2)|Yes (doc 2; scores 0.16 / 1.20 / 4.53 / 0.47)|
|3|What login protection do the most critical applications need?|Yes (doc 1)|**No** — ranked doc 3 top; the right doc (1) only third (scores 1.11 / 1.08 / 0.28 / 1.18)|
|4|If a change request has no way to undo it, what should happen?|Yes (doc 2)|Yes (doc 2; scores 0.32 / 0.51 / 3.94 / 0.36)|

**Your analysis:** The two retrievers **agreed on Q1, Q2, and Q4** — all three returned the correct document — and **disagreed on Q3**, where the embedding retriever was right and BM25 was wrong. That pattern matches what Huyen predicts for keyword versus paraphrase queries almost exactly. BM25 is term-based: it scores on exact word overlap, so it wins when the question reuses the document's own words. Q1 ("CMDB," "stale"), Q2 ("ITIL," "change types"), and Q4 all share literal terms with their target documents, and BM25's scores there were decisive (3.9–4.5 for the right doc, far above the rest). Q3 is the vocabulary-mismatch case: "most critical applications / login protection" shares no words with the MFA document's "crown jewel applications / phishing-resistant MFA," so BM25's scores were nearly tied (1.11 / 1.08 / 0.28 / 1.18) and it guessed wrong. The embedding retriever matched by meaning and linked "most critical" to "crown jewel."

One issue worth noting, Q4 was also a reworded question "no way to undo" instead of "rollback"), yet BM25 still got it  because "change request" appears word-for-word in the ITIL document, giving it enough lexical anchor. So paraphrasing doesn't always defeat BM25; it fails specifically on *vocabulary mismatch*, not rewording in general.

If I were building this for real, and I am considering it for later I would use a hybrid retriever. BM25 is cheap, transparent, and strong on exact terms, codes, and tags (SOX, PCI, application names, numbers), while embeddings handle natural-language and paraphrased questions better. For a CMDB/compliance agent whose users mix exact codes with plain-English questions, combining the two  would give the best recall across both query styles.

\---

## Grading

|Component|Undergraduate|Graduate|
|-|-|-|
|Complete the RAG codelab (Part 1)|30 pts|20 pts|
|Make it yours (Part 2)|40 pts|40 pts|
|Reflection (Part 3)|30 pts|20 pts|
|Graduate extension (Part 4)|—|20 pts|
|**Total**|**100 pts**|**100 pts**|




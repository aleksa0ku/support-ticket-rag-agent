# Cloudbox Support Deflection Agent

**[Live demo site](https://aleksa0ku.github.io/support-ticket-rag-agent/)**

A RAG agent that drafts or auto-resolves customer support tickets against a
help-center + past-tickets knowledge base, escalating to a human whenever its
confidence is too low. Built as a portfolio piece demonstrating the most
common paid AI engagement: support-ticket deflection.

**Problem:** Support teams answer the same ~40% of questions over and over;
each ticket costs a company roughly $5–15 in agent time.

**Solution:** Retrieve relevant help-center docs and similar past tickets,
draft an answer with Claude, and only auto-resolve when a combined
confidence score (model self-report + retrieval strength) clears a
threshold. Below threshold, escalate to a human with the draft attached.

**Metrics** (measured on the 100-question eval set in `data/eval_set.jsonl`,
using `claude-opus-4-8` for generation — see [Results](#results) below):

| Metric | Result |
|---|---|
| Deflection rate | **67%** (67/100 tickets fully auto-resolved) |
| Escalation-decision accuracy | **90%** |
| Precision on auto-resolved tickets | **98.5%** (66 correct / 1 wrong) |
| Recall on resolvable tickets | **88%** |
| Citation accuracy | **100%** (66/66 correct auto-resolutions cited the right doc) |
| Avg. first response | **6.7s** (vs. an assumed 4h human first-response time) |
| Blended cost per ticket | **$2.66** (vs. an assumed $8 flat human-handled cost — a 67% reduction) |

This repo ships with a self-contained fictional product ("Cloudbox", a
cloud file-storage/sync SaaS) so the whole pipeline runs end-to-end with no
external data: 15 help-center articles, 60 synthetic past tickets, and 100
eval questions (75 answerable from the docs, 25 that should correctly
escalate — security incidents, billing disputes, legal/compliance
requests, prompt-injection attempts, and other out-of-scope asks).

## Architecture

```
Customer question
      │
      ▼
 ┌───────────┐   top-k similarity    ┌──────────────────┐
 │ Retriever │──────────────────────▶│ Chroma vector DB  │
 └───────────┘                       │ (docs + tickets)  │
      │                              └──────────────────┘
      ▼
 ┌───────────┐   forced tool call    ┌──────────────────┐
 │ Generator │──────────────────────▶│ Claude (Messages  │
 └───────────┘                       │ API, tool_choice) │
      │                              └──────────────────┘
      ▼
 ┌────────────┐  blend model conf.
 │ Confidence │  + retrieval score
 │  decision  │
 └────────────┘
      │
      ├── above threshold → auto-resolve, return answer
      └── below threshold → escalate to human, return draft + reason
```

- **Embeddings:** local `sentence-transformers` model (`all-MiniLM-L6-v2`) —
  no extra API key required.
- **Vector store:** [Chroma](https://www.trychroma.com/), persisted locally.
- **Generation:** Anthropic Claude via the `anthropic` Python SDK, using a
  forced tool call (`submit_answer`) so the model returns a structured
  answer + confidence + citations + escalation decision in one turn.
- **Confidence/escalation:** `app/confidence.py` blends the model's
  self-reported confidence with the retrieval similarity score, and always
  escalates prompt-injection attempts, off-topic questions, and
  account-specific/security/legal requests (the model is instructed to flag
  these itself).

## Project layout

```
data/
  docs/            15 fictional Cloudbox help-center articles (Markdown)
  tickets.jsonl    60 synthetic past resolved tickets (retrieval augmentation)
  eval_set.jsonl   100 eval questions with should_deflect labels
app/               Core library: config, ingestion, retrieval, generation,
                   confidence scoring, pipeline orchestration
api/main.py        FastAPI service exposing POST /tickets/resolve
scripts/
  ingest.py             Build the vector index from data/
  run_eval.py           Run the eval set through the pipeline, print metrics
  generate_showcase.py  Regenerate the curated Q&A examples used on the demo site
tests/             Unit tests (confidence logic, ingestion) — no API calls
docs/              Static demo site (GitHub Pages) — see "Demo site" below
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
```

## Usage

```bash
# 1. Build the vector index (docs + tickets → Chroma)
python scripts/ingest.py

# 2. Run the eval set and see deflection rate / accuracy / cost metrics
python scripts/run_eval.py

# 3. (optional) serve the agent over HTTP
uvicorn api.main:app --reload
curl -X POST localhost:8000/tickets/resolve \
  -H 'Content-Type: application/json' \
  -d '{"question": "How do I enable two-factor authentication?"}'
```

## Results

Full run output (`python scripts/run_eval.py`, `claude-opus-4-8`, default
`CONFIDENCE_THRESHOLD=0.72`):

```
Eval set size:              100
Deflection rate:            67.0%  (67/100 auto-resolved)
Escalation-decision accuracy:90.0%
  Precision (of auto-resolved, % that should have been): 98.5%
  Recall (of resolvable tickets, % correctly auto-resolved): 88.0%
Citation accuracy (on correct auto-resolutions): 100.0% (66/66)
Confusion — TP=66 FP=1 TN=24 FN=9
Avg agent latency:          6.65s
Avg agent cost per ticket:  $0.0196
Blended cost per ticket:    $2.6596  (vs. $8.00 flat human cost)
```

Read the confusion matrix as: TP = correctly auto-resolved, FP = wrongly
auto-resolved (the one miss was a payment-method question the docs don't
cover — the model answered anyway instead of admitting it didn't know), TN
= correctly escalated, FN = escalated when it didn't need to be (safe, but
a missed deflection). Per-item results and full model output are written to
`eval_results/results.jsonl` (gitignored — regenerate locally).

## Demo site

`docs/index.html` is a static, self-contained page (no build step, no
external dependencies) published via GitHub Pages at
[aleksa0ku.github.io/support-ticket-rag-agent](https://aleksa0ku.github.io/support-ticket-rag-agent/).
It shows the architecture, the eval metrics above, and a handful of curated
real question → answer → confidence → deflect/escalate examples pulled
directly from the running pipeline (`docs/showcase-data.json`, generated by
`scripts/generate_showcase.py` — edit `SHOWCASE_IDS` in that script to
change which eval questions are featured, then re-run it and paste the
output into the `SHOWCASE` constant in `docs/index.html`).

## Tuning

- `CONFIDENCE_THRESHOLD` (`.env`) — raise it to escalate more conservatively
  (higher precision, lower deflection rate), lower it to deflect more
  aggressively (higher deflection rate, more risk of a wrong answer
  reaching the customer).
- `GENERATION_MODEL` — defaults to `claude-opus-4-8` for answer quality;
  swap to `claude-sonnet-5` or `claude-haiku-4-5` to cut cost per ticket for
  this kind of high-volume, low-complexity workload (see `scripts/run_eval.py`
  for the cost-per-ticket calculation and how it changes per model).

## Extending to a real support team

Swap `data/docs/` and `data/tickets.jsonl` for a real help-center export and
ticket history, re-run `scripts/ingest.py`, and re-derive an eval set from
real historical tickets (question + how it was actually resolved) instead
of the synthetic one here.

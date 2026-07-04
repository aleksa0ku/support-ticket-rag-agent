# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

A support-ticket deflection / RAG agent, built as a portfolio project. It
retrieves from a fictional SaaS product's help-center docs + past tickets,
drafts an answer with Claude, and decides whether to auto-resolve or
escalate to a human based on a blended confidence score. See `README.md`
for the architecture diagram and problem/solution framing.

## Key files

- `app/pipeline.py` — orchestrates retrieve → generate → decide. Start here
  to understand the request flow.
- `app/generator.py` — the Claude call. Uses a forced tool call
  (`tool_choice={"type": "tool", "name": "submit_answer"}`) so the model
  always returns structured `{answer, confidence, cited_doc_ids,
  should_escalate, escalation_reason}` rather than free text.
- `app/confidence.py` — the escalation decision. Blends the model's
  self-reported confidence with the top retrieval similarity score; the
  model's own `should_escalate=true` always wins regardless of confidence
  (used for security incidents, legal requests, prompt-injection attempts,
  off-topic questions).
- `app/ingest.py` — chunks `data/docs/*.md` by `##` heading and
  `data/tickets.jsonl` by ticket, embeds with a local sentence-transformers
  model, stores in a persistent Chroma collection.
- `scripts/run_eval.py` — the quick single-run eval (routing metrics only,
  no judge). Standalone, no external harness.
- `evals/` — the dev-only consumer of the eval harness library
  ([agent-eval-kit](https://github.com/aleksa0ku/agent-eval-kit), installed
  via `requirements-dev.txt`). `adapter.py` wraps `SupportPipeline` to satisfy
  the kit's `Agent` protocol; `scoring.py` holds the task-specific metrics,
  gate tolerances, and the safety rule; `harness.py` wires it together. The
  full A/B + judge + gate flow runs through `scripts/run_ab_demo.py`, which
  also regenerates `docs/eval-data.json` for the eval page.

## Data model

`data/eval_set.jsonl` items have `should_deflect: bool` — whether the
question *should* be auto-resolved. 75 items are answerable purely from
`data/docs/`; 25 are deliberately not (account-specific actions, security
incidents, legal/compliance, sales negotiation, prompt injection, off-topic)
and are labeled `should_deflect: false` to test that the agent correctly
declines to auto-resolve them, not just that it answers well when it can.

`data/tickets.jsonl` items carry a `doc_id` linking each synthetic past
ticket to the help doc that resolved it, and `resolved_by: "agent"|"human"`
matching the same escalation categories used in the eval set — keep these
two labelings consistent if you add more synthetic data.

## Working in this repo

- The `data/docs/` corpus is a fictional product ("Cloudbox"). If you add a
  new doc, also add: a few `data/tickets.jsonl` entries referencing its
  `doc_id`, and a handful of `data/eval_set.jsonl` questions covering it
  (both answerable and, if relevant, an escalate-worthy edge case).
- `scripts/ingest.py` must be re-run after any change to `data/docs/` or
  `data/tickets.jsonl` — the Chroma collection is rebuilt from scratch each
  run (`build_index` deletes and recreates the collection), so there's no
  incremental-update path to worry about.
- Tests in `tests/` don't call the Anthropic API — `test_confidence.py`,
  `test_ingest.py`, and `test_scoring.py` (the deflection metrics) all use
  hand-built fixtures. The generic harness mechanics (judge, compare, gate)
  are tested in the agent-eval-kit repo. The eval scripts (`run_eval.py`,
  `run_experiment.py`, `run_ab_demo.py`) are what spend real API calls.
- The eval harness is a separate repo. Production (`app/`, `api/`) must never
  import `agent_eval_kit` — only `evals/` and `scripts/` may. If you change
  the harness itself (judge, compare, gate), that's a change to the
  agent-eval-kit repo, not this one.
- Never commit `.env` (it holds a real `ANTHROPIC_API_KEY`). Only
  `.env.example` with placeholders should be tracked.
- Model choice is in `.env` (`GENERATION_MODEL`). Defaults to
  `claude-opus-4-8`. If asked to swap models or optimize cost, also update
  the `PRICING` dicts in `scripts/run_eval.py` and `evals/scoring.py` so the
  cost-per-ticket metric
  stays accurate.

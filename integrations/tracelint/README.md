# tracelint integration (proof of concept)

[tracelint](https://github.com/AshwinUgale/tracelint) is a **deterministic, judge-free linter for
agent runs**. It reads an execution trace — what the agents *actually did* — and flags structural
defects with the exact evidence and a CI exit code. No second model judges the trace, so the same
input always produces the same finding.

This folder is a **self-contained PoC**: it shows that tracelint catches useful structural defects
in a DATAGEN-shaped multi-agent research run **without** adding noise on legitimate repeated
research or retries. It changes **no runtime code** and adds **no CI workflow** — wiring the CI gate
is intentionally left to the DATAGEN maintainers.

## What's here

| File | Purpose |
|------|---------|
| `tools.json` | Minimal tool contract: which DATAGEN tools are read-only vs. side-effecting. |
| `traces/research_run_defect.json` | A research run with two planted structural defects. |
| `traces/research_run_clean.json` | A legitimate run: repeated searches + a retried scrape. |
| `capture_example.py` | Reference recipe for capturing a **real** LangGraph run (not run in CI). |
| `../../tests/test_tracelint_integration.py` | Lints both traces and asserts caught-vs-clean. |

## The two properties it proves

**1. Real defects are caught (and would gate CI).** `research_run_defect.json` mirrors a research →
report flow where:
- `google_search` returned a **structured error**, and a value from that failed result was written
  straight into the saved report via the side-effecting `write_document` → **R2b, `hard_defect`**;
- `write_document` was then called **twice with identical arguments** after the first succeeded →
  **R8, duplicate side effect**.

```
$ tracelint check integrations/tracelint/traces/research_run_defect.json \
    --tools integrations/tracelint/tools.json --rules R2a,R2b,R4,R5,R6,R7,R8
  [hard_event]  R2a  'google_search' returned an error (RateLimited: search quota exceeded)
  [hard_defect] R2b  value(s) from the errored 'google_search' result reused as arguments to
                     'write_document' (a side-effecting action, no fallback)
  [hard_event]  R8   'write_document' repeats an equivalent non-idempotent side-effecting call
exit 2
```

**2. Legitimate repetition is NOT flagged.** `research_run_clean.json` has three *different* research
searches and a scrape that fails once then **succeeds on retry**. tracelint reports the transient
error as an *event* (not a defect) and exits `0` — repeated research and retries add no noise:

```
$ tracelint check integrations/tracelint/traces/research_run_clean.json \
    --tools integrations/tracelint/tools.json --rules R2a,R2b,R4,R5,R6,R7,R8
  [hard_event]  R2a  'scrape_webpages' returned an error (Timeout)   # surfaced, not a defect
exit 0
```

Note the tiering: `hard_event` says *an error occurred*; `hard_defect` says *the agent structurally
mishandled it*. Only `hard_defect` fails CI (exit `2`), so a retried transient error stays green.

## Rules used, and why

This PoC runs `R2a,R2b,R4,R5,R6,R7,R8`. Two rules are deliberately left out for DATAGEN's flow:

- **R1 (schema violation)** auto-suppresses when tools declare no JSON schema — it is *disclosed* as
  suppressed, never counted as a pass. Add per-tool `schema` blocks to `tools.json` (or generate a
  draft with `tracelint init`) to turn it on.
- **R3 (hallucinated argument)** needs per-field provenance annotations (`x-value-origin`) to be
  meaningful. Without them it flags every model-generated search `query` as "not derivable" — pure
  noise on a research agent — so it is scoped out here.

The contract in `tools.json` is what makes the checks deterministic: `create_document`,
`write_document`, `edit_document`, `execute_code`, and `execute_command` are declared
`side_effecting` + non-`idempotent`; the search/read tools are read-only.

## Run it

```bash
pip install tracelint
pytest tests/test_tracelint_integration.py      # skips cleanly if tracelint isn't installed
```

## Capturing a real run

The committed traces are hand-written fixtures so the PoC is deterministic and offline. To lint a
**real** DATAGEN run, capture one with tracelint's LangChain/LangGraph capture and lint the result
— see [`capture_example.py`](capture_example.py):

```bash
pip install "tracelint[capture-langchain]"
# then, around your graph.invoke(...):  with capture("datagen_run.json", framework="langchain"): ...
tracelint check datagen_run.json --format openinference \
  --tools integrations/tracelint/tools.json --rules R2a,R2b,R4,R5,R6,R7,R8
```

Capture wraps the framework's stock OpenInference instrumentor against a local exporter, so it
leaves any tracing you already run untouched.

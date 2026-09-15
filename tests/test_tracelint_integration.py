"""PoC: lint representative DATAGEN research traces with tracelint.

tracelint (https://github.com/AshwinUgale/tracelint) is a deterministic, judge-free linter for
agent runs: it reads an execution trace and flags structural defects — ignored tool errors,
errored values reused in side effects, loops, duplicate side effects — with the exact evidence
and a CI exit code. No LLM judges the trace.

This test lints two committed traces that mirror DATAGEN's multi-agent research flow (see
``integrations/tracelint/``) and asserts the two properties the integration cares about:

1. a run with real structural defects is caught and would gate CI (exit code 2); and
2. a legitimate run — repeated *research* searches and a *retried* scrape — is NOT flagged,
   i.e. tracelint does not add noise on legitimate repetition.

tracelint is an optional dev/CI dependency; this test skips cleanly when it is absent, so it never
affects DATAGEN's own test run or CI. To run it locally: ``pip install tracelint``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

tracelint = pytest.importorskip("tracelint")

from tracelint import Trace, ToolRegistry, lint_trace  # noqa: E402
from tracelint.findings import ConfidenceTier  # noqa: E402
from tracelint.rules import select_rules  # noqa: E402

_INTEGRATION = Path(__file__).resolve().parents[1] / "integrations" / "tracelint"
_TRACES = _INTEGRATION / "traces"
_TOOLS = _INTEGRATION / "tools.json"

# Structural rules meaningful for DATAGEN's tool-calling flow.
#   R1 (schema violation) auto-suppresses without declared tool schemas (disclosed, not a pass).
#   R3 (hallucinated arg) needs per-field provenance annotations (``x-value-origin``) to be
#   meaningful; without them it flags every model-generated search query, so it is scoped out
#   here rather than adding noise on legitimate research actions.
_RULES = ["R2a", "R2b", "R4", "R5", "R6", "R7", "R8"]


def _lint(trace_name: str):
    trace = Trace.load(str(_TRACES / trace_name))
    registry = ToolRegistry.load(str(_TOOLS))
    return lint_trace(trace, select_rules(_RULES), registry)


def test_defect_trace_is_caught_and_gates_ci():
    """A search that errored, whose value was written into the saved report, and a report written
    twice with identical arguments — both structural defects tracelint must catch."""
    report = _lint("research_run_defect.json")

    assert report.has_hard_defect
    assert report.exit_code == 2  # a structurally-provable defect fails CI

    hard_defects = {f.rule for f in report.active_findings if f.tier is ConfidenceTier.HARD_DEFECT}
    # R2b: a value from the errored google_search result was reused as an argument to the
    # side-effecting write_document (the failed search written into the saved report).
    assert "R2b" in hard_defects

    all_rules = {f.rule for f in report.active_findings}
    # R8: write_document called twice with equivalent arguments after the first succeeded.
    assert "R8" in all_rules


def test_clean_trace_has_no_defect_and_tolerates_legit_repeats():
    """Three *different* research searches and a *retried* scrape are legitimate — tracelint must
    not report a defect, so a clean run stays green in CI."""
    report = _lint("research_run_clean.json")

    assert not report.has_hard_defect
    assert report.exit_code == 0
    assert not any(f.tier is ConfidenceTier.HARD_DEFECT for f in report.active_findings)

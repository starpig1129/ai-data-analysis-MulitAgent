"""Capture a REAL DATAGEN run into a lintable trace (reference — not run in CI).

The committed fixtures under ``traces/`` are hand-written so the PoC is deterministic and offline.
This script shows the other half: how to record an actual DATAGEN graph run and lint it, with no
changes to DATAGEN's runtime.

    pip install "tracelint[capture-langchain]"   # LangChain instrumentor; also captures LangGraph
    python integrations/tracelint/capture_example.py

DATAGEN is a LangGraph app, so ``framework="langgraph"`` is used below (it wraps the same LangChain
OpenInference instrumentor). ``tracelint.capture`` stands that instrumentor up against a *local* OTel
provider whose only exporter writes the flat OpenInference span shape to a file — so any tracing you
already run is left untouched, and the file lints with ``--format openinference``.
"""

from __future__ import annotations

from pathlib import Path

OUT = Path("datagen_run.json")
TOOLS = Path(__file__).with_name("tools.json")


def main() -> None:
    from tracelint import capture

    # Build DATAGEN's graph however your entrypoint does, e.g.:
    #     from src.core.workflow import build_workflow
    #     graph = build_workflow(...)
    #
    # Then capture a run. Everything executed inside the context manager is recorded.
    # framework="langgraph" wraps the LangChain OpenInference instrumentor DATAGEN's graph uses:
    with capture(str(OUT), framework="langgraph"):
        # result = graph.invoke(
        #     {"messages": [("user", "Research recent advances in CRISPR base editing "
        #                            "and save a report.")]}
        # )
        raise SystemExit(
            "Wire this to your DATAGEN graph.invoke(...) call, then remove this guard."
        )

    # Lint the captured trace against the same contract the PoC test uses:
    #   tracelint check datagen_run.json --format openinference \
    #       --tools integrations/tracelint/tools.json --rules R2a,R2b,R4,R5,R6,R7,R8
    print(f"Captured {OUT}. Lint it with --format openinference --tools {TOOLS}")


if __name__ == "__main__":
    main()

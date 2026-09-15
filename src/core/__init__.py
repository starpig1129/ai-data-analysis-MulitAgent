"""Core workflow, routing, state and MCP management.

Import from the submodules directly (for example ``src.core.workflow``). This
package deliberately has no re-exports: importing them eagerly pulled in the
whole agent graph and created a circular import with ``src.agents``.
"""

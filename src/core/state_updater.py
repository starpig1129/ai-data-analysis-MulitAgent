"""StateUpdater Protocol for decoupling agent-specific state update logic.

This module defines the protocol that agents can implement to specify
how their outputs should be mapped to state updates, removing the need
for hardcoded if-elif chains in agent_node.
"""

from typing import Any, Protocol, runtime_checkable

from .state import State


@runtime_checkable
class StateUpdater(Protocol):
    """Protocol for agents to define their state update logic.

    Agents implementing this protocol can control how their outputs
    are mapped to state field updates.
    """

    def get_state_updates(self, state: State, output: Any) -> dict[str, Any]:
        """Return a dict of state field updates based on agent output.

        Args:
            state: The current workflow state.
            output: The agent's structured or raw output.

        Returns:
            Dict mapping state field names to their new values.
        """
        ...

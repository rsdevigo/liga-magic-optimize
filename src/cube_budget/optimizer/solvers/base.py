"""Abstract solver protocol."""

from __future__ import annotations

from typing import Protocol

from cube_budget.optimizer.result import SolverInput, SolverOutput


class AbstractSolver(Protocol):
    """Protocol for optimization solvers."""

    def solve(self, data: SolverInput) -> SolverOutput:
        """Solve the set cover + price minimization problem."""
        ...

    def supports(self, n_vars: int) -> bool:
        """Return True if solver can handle this problem size."""
        ...

    @property
    def name(self) -> str:
        """Solver identifier."""
        ...

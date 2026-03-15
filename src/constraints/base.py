# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pycsp3.classes.main.variables import Variable
from pycsp3.tools.curser import ListVar

from league import Fixture, League, Team

if TYPE_CHECKING:
    from solver_pycsp3 import Solver


@dataclass
class ConstraintContext:
    solver: Solver
    vars: dict[Fixture, Variable] = field(default_factory=dict)
    homeFixtureArrays: dict[Team, ListVar] = field(default_factory=dict)
    homeFixtureDomains: dict[Team, set[int]] = field(default_factory=dict)
    firstMatches: set[Fixture] = field(default_factory=set)


@dataclass
class CheckResult:
    """Outcome of evaluating one constraint on an instantiated league."""

    score: float
    reasons: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.score < 0.0 or self.score > 1.0:
            raise ValueError(f"CheckResult.score must be in [0, 1], got {self.score}")
        if (self.score == 1.0) != (len(self.reasons) == 0):
            raise ValueError("CheckResult.reasons must be empty iff score == 1")


class Constraint:
    def apply(self, ctx: ConstraintContext) -> Any | None:
        raise NotImplementedError()

    def check(self, league: League) -> CheckResult:
        """Evaluate this constraint on a concrete league assignment."""
        del league
        raise NotImplementedError()


class DomainConstraint:
    def apply_to_fixture_domain(self, ctx: ConstraintContext, fixture: Fixture, domain: set[int]) -> set[int]:
        raise NotImplementedError()

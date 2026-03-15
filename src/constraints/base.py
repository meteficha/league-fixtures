# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pycsp3.classes.main.variables import Variable
from pycsp3.tools.curser import ListVar

from league import Fixture, Team

if TYPE_CHECKING:
    from solver_pycsp3 import Solver


@dataclass
class ConstraintContext:
    solver: Solver
    vars: dict[Fixture, Variable] = field(default_factory=dict)
    homeFixtureArrays: dict[Team, ListVar] = field(default_factory=dict)
    homeFixtureDomains: dict[Team, set[int]] = field(default_factory=dict)
    firstMatches: set[Fixture] = field(default_factory=set)


class Constraint:
    def apply(self, ctx: ConstraintContext) -> Any | None:
        raise NotImplementedError()


class DomainConstraint:
    def apply_to_fixture_domain(self, ctx: ConstraintContext, fixture: Fixture, domain: set[int]) -> set[int]:
        raise NotImplementedError()

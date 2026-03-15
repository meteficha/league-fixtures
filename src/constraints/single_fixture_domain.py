# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from typing import Sequence

import pycsp3.functions as pycsp3f

from league import Fixture

from .base import Constraint, ConstraintContext, DomainConstraint
from .domain import create_default_domain_constraints


class SingleFixtureDomainConstraint(Constraint):
    def __init__(self, domainConstraints: Sequence[DomainConstraint] | None = None):
        self.domainConstraints = list(domainConstraints) if domainConstraints is not None else create_default_domain_constraints()

    def fixture_domain(self, ctx: ConstraintContext, fixture: Fixture) -> set[int]:
        domain = set(range(ctx.solver.dateToInt(ctx.solver.league.end)))
        for constraint in self.domainConstraints:
            domain = constraint.apply_to_fixture_domain(ctx, fixture, domain)
        return domain

    def apply(self, ctx: ConstraintContext) -> None:
        print("\t\tSingle fixture constraints")
        for t in ctx.solver.league.teams:
            # For every fixture f, there is one, and only one, team for which f is a home fixture.
            # Therefore, we only need to go through home fixtures here.
            homeFixtures = list(t.homeFixtures)
            doms = [self.fixture_domain(ctx, fixture) for fixture in homeFixtures]
            ctx.homeFixtureArrays[t] = pycsp3f.VarArray(
                size=len(homeFixtures),
                dom=lambda i=0: doms[i],
                id="homeFixtures_" + t.sanitized_name,
                comment=str([f.name for f in homeFixtures]),
            )
            ctx.homeFixtureDomains[t] = set().union(*doms)
            for (f, v) in zip(homeFixtures, ctx.homeFixtureArrays[t]):
                ctx.vars[f] = v

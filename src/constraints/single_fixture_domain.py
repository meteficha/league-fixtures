# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from typing import Any, Sequence, cast

import pycsp3.functions as pycsp3f
from league import League
from solver_base import SolverBase

from league import Fixture

from .base import CheckResult, Constraint, ConstraintContext, DomainConstraint
from .domain import create_default_domain_constraints
from .utils import cap_reasons, ratio_score


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

    def check(self, league: League) -> CheckResult:
        ctx = ConstraintContext(solver=cast(Any, SolverBase(league)))
        satisfied = 0
        total = 0
        reasons: list[str] = []

        for f in league.fixtures:
            if f.date is None:
                continue
            total += 1
            dom = self.fixture_domain(ctx, f)
            actual = ctx.solver.dateToInt(f.date)
            if actual in dom:
                satisfied += 1
            else:
                reasons.append(f"Fixture {f.name} date {f.date} is outside allowed domain")

        score = ratio_score(satisfied, total)
        return CheckResult(score=score, reasons=[] if score == 1.0 else cap_reasons(reasons))

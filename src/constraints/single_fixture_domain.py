# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
import pycsp3.functions as pycsp3f

from .base import Constraint, ConstraintContext


class SingleFixtureDomainConstraint(Constraint):
    def apply(self, ctx: ConstraintContext) -> None:
        print("\t\tSingle fixture constraints")
        for t in ctx.solver.league.teams:
            # For every fixture f, there is one, and only one, team for which f is a home fixture.
            # Therefore, we only need to go through home fixtures here.
            homeFixtures = list(t.homeFixtures)
            doms = list(map(ctx.solver.dom, homeFixtures))
            ctx.homeFixtureArrays[t] = pycsp3f.VarArray(
                size=len(homeFixtures),
                dom=lambda i=0: doms[i],
                id="homeFixtures_" + t.sanitized_name,
                comment=str([f.name for f in homeFixtures]),
            )
            ctx.homeFixtureDomains[t] = set.union(*doms)
            for (f, v) in zip(homeFixtures, ctx.homeFixtureArrays[t]):
                ctx.vars[f] = v

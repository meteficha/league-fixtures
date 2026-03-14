# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
import pycsp3.functions as pycsp3f

from .base import Constraint, ConstraintContext


class FixturePairSpacingConstraint(Constraint):
    def __init__(self, strictFixturePairSpacing: int | None = None) -> None:
        self.strictFixturePairSpacing = strictFixturePairSpacing

    def apply(self, ctx: ConstraintContext) -> None:
        if self.strictFixturePairSpacing is None:
            return
        print(f"\t\tFixture pairs played with time between them ({str(self.strictFixturePairSpacing)} weeks)")
        pycsp3f.satisfy(
            pycsp3f.abs(ctx.vars[f1] - ctx.vars[f2]) >= self.strictFixturePairSpacing * 7  # pyright: ignore[reportOperatorIssue]
            for (f1, f2) in ctx.solver.league.fixturePairs
            if not f1.home.relaxed and not f1.away.relaxed
        )

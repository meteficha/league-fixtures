# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from typing import Any

import pycsp3.functions as pycsp3f
from league import League

from .base import CheckResult, Constraint, ConstraintContext
from .utils import cap_reasons


class VenueMinimizeEmptyDaysObjectiveConstraint(Constraint):
    def apply(self, ctx: ConstraintContext) -> Any:
        print("\t\tVenues can choose to minimize empty days")
        return -1 * pycsp3f.Sum(
            pycsp3f.NValues(ctx.vars[f] for f in v.fixtures)
            for v in ctx.solver.league.venues
            if v.minimizeEmptyDays and len(v.fixtures) >= 2
        )

    def check(self, league: League) -> CheckResult:
        ratios: list[float] = []
        reasons: list[str] = []

        for v in league.venues:
            if (not v.minimizeEmptyDays) or len(v.fixtures) < 2:
                continue
            fixtures = [f for f in v.fixtures if f.date is not None]
            if len(fixtures) == 0:
                continue
            distinct_days = len({f.date for f in fixtures})
            ratio = 1.0 / distinct_days
            ratios.append(ratio)
            if ratio < 1.0:
                reasons.append(
                    f"Venue {v.name} uses {distinct_days} distinct days; fewer is better"
                )

        score = 1.0 if len(ratios) == 0 else (sum(ratios) / len(ratios))
        return CheckResult(score=score, reasons=[] if score == 1.0 else cap_reasons(reasons))

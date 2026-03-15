# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from typing import Any

import pycsp3.functions as pycsp3f
from league import League

from .base import CheckResult, Constraint, ConstraintContext
from .utils import cap_reasons


class VenueAssignedDaysObjectiveConstraint(Constraint):
    def apply(self, ctx: ConstraintContext) -> Any:
        print("\t\tVenues have matches assigned to most of their days")
        return pycsp3f.Sum(
            pycsp3f.NValues(ctx.vars[f] for f in v.fixtures)
            for v in ctx.solver.league.venues
            if not v.minimizeEmptyDays
            if len(v.fixtures) >= 2
        )

    def check(self, league: League) -> CheckResult:
        ratios: list[float] = []
        reasons: list[str] = []

        for v in league.venues:
            if v.minimizeEmptyDays or len(v.fixtures) < 2:
                continue
            fixtures = [f for f in v.fixtures if f.date is not None]
            if len(fixtures) == 0:
                continue
            distinct_days = len({f.date for f in fixtures})
            ratio = distinct_days / len(fixtures)
            ratios.append(ratio)
            if ratio < 1.0:
                reasons.append(
                    f"Venue {v.name} uses {distinct_days} distinct days for {len(fixtures)} fixtures"
                )

        score = 1.0 if len(ratios) == 0 else (sum(ratios) / len(ratios))
        return CheckResult(score=score, reasons=[] if score == 1.0 else cap_reasons(reasons))

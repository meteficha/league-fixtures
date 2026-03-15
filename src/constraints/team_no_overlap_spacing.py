# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from typing import Any

import pycsp3.functions as pycsp3f
from league import League

from .base import CheckResult, Constraint, ConstraintContext
from .utils import cap_reasons, ratio_score


class TeamNoOverlapAndSpacingConstraint(Constraint):
    def __init__(self, strictMatchSpaceOut: int | None = 5) -> None:
        self.strictMatchSpaceOut = strictMatchSpaceOut

    def apply(self, ctx: ConstraintContext) -> Any:
        print("\t\tTeams can only play one fixture per day / Space out the matches of a team")
        spaceNoMoreOpt = pycsp3f.Var(dom=[7 * 3], id="spaceNoMoreOpt")
        optSpaceTeams = []
        for t in ctx.solver.league.teams:
            minimum = self.strictMatchSpaceOut if self.strictMatchSpaceOut is not None and not t.relaxed else 1
            arr = pycsp3f.VarArray(
                size=len(t.fixtures),
                dom=range(minimum, 365),
                id="SpaceOut_NoOverlap_" + t.sanitized_name,
            )
            pycsp3f.satisfy(pycsp3f.NoOverlap(origins=[ctx.vars[f] for f in t.fixtures], lengths=arr))
            optSpaceTeams.append(pycsp3f.Sum(10 * pycsp3f.Minimum(v, spaceNoMoreOpt) for v in arr))
        return pycsp3f.Sum(optSpaceTeams)

    def check(self, league: League) -> CheckResult:
        satisfied = 0
        total = 0
        reasons: list[str] = []

        for t in league.teams:
            min_gap = self.strictMatchSpaceOut if self.strictMatchSpaceOut is not None and not t.relaxed else 1
            dates = sorted(f.date for f in t.fixtures if f.date is not None)
            for i in range(len(dates) - 1):
                gap = (dates[i + 1] - dates[i]).days
                total += 1
                if gap >= min_gap:
                    satisfied += 1
                else:
                    reasons.append(
                        f"Team {t.name} has fixtures {gap} days apart; minimum is {min_gap}"
                    )

        score = ratio_score(satisfied, total)
        return CheckResult(score=score, reasons=[] if score == 1.0 else cap_reasons(reasons))

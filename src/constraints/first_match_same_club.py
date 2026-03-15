# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
import pycsp3.functions as pycsp3f
from league import League

from league import Team

from .base import CheckResult, Constraint, ConstraintContext
from .utils import cap_reasons, ratio_score


class FirstMatchSameClubConstraint(Constraint):
    def apply(self, ctx: ConstraintContext) -> None:
        print("\t\tFirst matches of a club's teams in a division are between themselves")
        hasFirstMatchConstraint: set[Team] = set()
        for t in ctx.solver.league.teams:
            if t not in hasFirstMatchConstraint:
                hasFirstMatchConstraint.add(t)
                candidates = [f for f in t.fixtures if f.home == t and f.sameClub()]
                if len(candidates) > 0:
                    best = [f for f in candidates if f.away not in hasFirstMatchConstraint]
                    chosen = best[0] if len(best) > 0 else candidates[0]
                    ctx.firstMatches.add(chosen)
                    pycsp3f.satisfy(
                        ctx.vars[chosen] < ctx.vars[f]  # pyright: ignore[reportOperatorIssue]
                        for u in chosen.teams
                        for f in u.fixtures
                        if f not in ctx.firstMatches
                    )
                    hasFirstMatchConstraint.add(chosen.away)

    def check(self, league: League) -> CheckResult:
        has_first_match_constraint: set[Team] = set()
        first_matches: set[object] = set()
        satisfied = 0
        total = 0
        reasons: list[str] = []

        for t in league.teams:
            if t in has_first_match_constraint:
                continue
            has_first_match_constraint.add(t)
            candidates = [f for f in t.fixtures if f.home == t and f.sameClub()]
            if len(candidates) == 0:
                continue

            best = [f for f in candidates if f.away not in has_first_match_constraint]
            chosen = best[0] if len(best) > 0 else candidates[0]
            first_matches.add(chosen)
            has_first_match_constraint.add(chosen.away)

            if chosen.date is None:
                continue
            for u in chosen.teams:
                for f in u.fixtures:
                    if f in first_matches or f.date is None:
                        continue
                    total += 1
                    if chosen.date < f.date:
                        satisfied += 1
                    else:
                        reasons.append(
                            f"{chosen.name} on {chosen.date} is not before {f.name} on {f.date}"
                        )

        score = ratio_score(satisfied, total)
        return CheckResult(score=score, reasons=[] if score == 1.0 else cap_reasons(reasons))

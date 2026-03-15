# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from itertools import chain
from typing import Any

from league import Fixture, League, Team
import pycsp3.functions as pycsp3f

from .base import CheckResult, Constraint, ConstraintContext
from .utils import alternate, build_pair_order_violation_array, domUnion
from .utils import cap_reasons


class HomeAwayAlternationConstraint(Constraint):
    def __init__(self, strictHomeAwayConstraint: int | None = None) -> None:
        self.strictHomeAwayConstraint = strictHomeAwayConstraint

    def apply(self, ctx: ConstraintContext) -> Any:
        print("\t\tTeams alternate between playing away and at home", end="", flush=True)
        optHomeAway = None

        def satisfyHomeAwayConstraint(t: Team) -> Any:
            awayFixtures: list[Fixture] = list(t.awayFixtures)
            n = len(awayFixtures)
            if n < 1:
                return None
            homeFixtureArr = ctx.homeFixtureArrays[t]
            assert len(homeFixtureArr) == n
            awayDomain = domUnion(ctx.vars[f] for f in awayFixtures)
            awayFixtureArr = pycsp3f.VarArray(size=n, dom=awayDomain, id="awayFixtureArr_" + t.sanitized_name)
            homeIxArr = pycsp3f.VarArray(size=n, dom=range(n), id="homeIxArr_" + t.sanitized_name)
            awayIxArr = pycsp3f.VarArray(size=n, dom=range(n), id="awayIxArr_" + t.sanitized_name)
            sortedHomeFixtureArr = pycsp3f.VarArray(size=n, dom=ctx.homeFixtureDomains[t], id="sortedHomeFixtureArr_" + t.sanitized_name)
            sortedAwayFixtureArr = pycsp3f.VarArray(size=n, dom=awayDomain, id="sortedAwayFixtureArr_" + t.sanitized_name)
            pycsp3f.satisfy(
                list(
                    chain(
                        [
                            awayFixtureArr[i] == ctx.vars[awayFixtures[i]],
                            sortedHomeFixtureArr[i] == homeFixtureArr[homeIxArr[i]],
                            sortedAwayFixtureArr[i] == awayFixtureArr[awayIxArr[i]],
                        ]
                        for i in range(n)
                    )
                )
            )
            pycsp3f.satisfy(
                [
                    pycsp3f.AllDifferent(homeIxArr),
                    pycsp3f.AllDifferent(awayIxArr),
                    pycsp3f.Increasing(sortedHomeFixtureArr, strict=True),
                    pycsp3f.Increasing(sortedAwayFixtureArr, strict=True),
                ]
            )
            print(".", end="", flush=True)
            if self.strictHomeAwayConstraint == 1 and not t.relaxed:
                toConsider = []
                if not any(f in ctx.firstMatches for f in awayFixtures):
                    toConsider.append(pycsp3f.Increasing(alternate(sortedHomeFixtureArr, sortedAwayFixtureArr), strict=True))
                if not any(f in ctx.firstMatches for f in t.homeFixtures):
                    toConsider.append(pycsp3f.Increasing(alternate(sortedAwayFixtureArr, sortedHomeFixtureArr), strict=True))
                pycsp3f.satisfy(pycsp3f.Or(toConsider))
                return None

            toConsider = []
            if not any(f in ctx.firstMatches for f in awayFixtures):
                toConsider.append((sortedHomeFixtureArr, sortedAwayFixtureArr, "homeAway"))
            if not any(f in ctx.firstMatches for f in t.homeFixtures):
                toConsider.append((sortedAwayFixtureArr, sortedHomeFixtureArr, "awayHome"))
            if not toConsider:
                return None

            arrays = [build_pair_order_violation_array(as_, bs, prefix + "ConstraintArr_" + t.sanitized_name) for (as_, bs, prefix) in toConsider]
            countWrongs = [pycsp3f.Sum(array) for array in arrays]
            if self.strictHomeAwayConstraint is not None and not t.relaxed:
                pycsp3f.satisfy(pycsp3f.Or(cw <= self.strictHomeAwayConstraint for cw in countWrongs))
            return pycsp3f.Minimum(countWrongs)

        optTerms = [c for c in map(satisfyHomeAwayConstraint, ctx.solver.league.teams) if c is not None]
        if optTerms:
            optHomeAway = pycsp3f.Sum(c for c in optTerms) * (-100)
        print("")
        return optHomeAway

    def check(self, league: League) -> CheckResult:
        team_scores: list[float] = []
        reasons: list[str] = []

        for t in league.teams:
            home_dates = sorted(f.date for f in t.homeFixtures if f.date is not None)
            away_dates = sorted(f.date for f in t.awayFixtures if f.date is not None)
            n = min(len(home_dates), len(away_dates))
            if n < 1:
                continue

            seq_home_away = list(alternate(home_dates[:n], away_dates[:n]))
            seq_away_home = list(alternate(away_dates[:n], home_dates[:n]))

            def violations(seq: list[object]) -> int:
                wrong = 0
                for i in range(len(seq) - 1):
                    if seq[i] >= seq[i + 1]:
                        wrong += 1
                return wrong

            v = min(violations(seq_home_away), violations(seq_away_home))
            max_pairs = max(1, len(seq_home_away) - 1)

            if self.strictHomeAwayConstraint == 1 and not t.relaxed:
                team_score = 1.0 if v == 0 else 0.0
            elif self.strictHomeAwayConstraint is not None and not t.relaxed:
                team_score = 1.0 if v <= self.strictHomeAwayConstraint else 0.0
            else:
                team_score = max(0.0, 1.0 - (v / max_pairs))

            team_scores.append(team_score)
            if team_score < 1.0:
                reasons.append(f"Team {t.name} has {v} alternation ordering violations")

        score = 1.0 if len(team_scores) == 0 else (sum(team_scores) / len(team_scores))
        return CheckResult(score=score, reasons=[] if score == 1.0 else cap_reasons(reasons))

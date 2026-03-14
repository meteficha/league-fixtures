# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from itertools import chain
from typing import Any

from league import Fixture, Team
import pycsp3.functions as pycsp3f

from .base import Constraint, ConstraintContext
from .utils import alternate, build_pair_order_violation_array, domUnion


class HomeAwayAlternationConstraint(Constraint):
    def __init__(self, strictHomeAwayConstraint: int | None = None) -> None:
        self.strictHomeAwayConstraint = strictHomeAwayConstraint
        self._optHomeAway: Any = 0

    def apply(self, ctx: ConstraintContext) -> None:
        print("\t\tTeams alternate between playing away and at home", end="", flush=True)
        self._optHomeAway = 0

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
            self._optHomeAway = pycsp3f.Sum(c for c in optTerms) * (-100)
        print("")

    def objective_term(self, _ctx: ConstraintContext) -> Any:
        return self._optHomeAway

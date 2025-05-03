# pyright: strict, reportUnknownMemberType=false
from datetime import date
from itertools import pairwise
from typing import Any, Iterator
import pycsp3 # pyright: ignore [reportMissingTypeStubs]

from league import *
from solver_base import SolverBase, UnsatisfiableConstraints

def pairs[T](xs: list[T]) -> Iterator[tuple[T, T]]:
    """All pairs (x[i], x[j]) where i < j."""
    for i in range(len(xs)):
        for j in range(i+1, len(xs)):
            yield (xs[i], xs[j])

def extract[T](xs: list[T]) -> Iterator[tuple[T, Iterable[T]]]:
    """All pairs (x[i], xs_i) where { xs_i = xs.copy; del xs_i[i] }"""
    for i in range(len(xs)):
        rest = (xs[j] for j in range(len(xs)) if i != j)
        yield (xs[i], rest)

class Solver(SolverBase):
    """Update every fixture of the given league with dates that
    fit the necessary constraints."""
    created = False

    def __init__(self, league: League):
        if Solver.created:
            raise Exception("pycsp3 is silly, you can't create two Solvers")
        Solver.created = True
        super().__init__(league)
        self.constraints = False
        self.adjacentTeamsAsConstraint = True

    def dom(self, f: Fixture) -> set[int]:
        # Constraint: respects club late starts.
        start: int = max(self.dateToInt(d) for d in [self.league.start, f.home.club.lateStart, f.away.club.lateStart] if d is not None)

        # Constraint: played within start/end dates.
        # Constraint: played on venue's weekday.
        ret = {d for d in self.possibleDays(f.weekday) if d >= start}

        # Constraint: not played on a holiday.
        ret.difference_update(self.dateToInt(d) for d in self.league.holidays.get(f.weekday, frozenset()))

        # Constraint: matches between teams of the same club must be played by 31 Jan.
        if f.sameClub():
            ret = {d for d in ret if d <= self.dateToInt(date(self.league.end.year, 1, 31))}

        return ret

    def __createConstraints(self) -> None:
        if self.constraints:
            return
        self.constraints = True
        pycsp3.clear()

        # Constraints on single fixtures
        for f in self.league.fixtures:
            if f.date is not None:
                # Allow for fixture dates to be decided manually.
                f.pycsp3 = pycsp3.Var(dom=self.dateToInt(f.date), id=f.sanitized_name)
            else:
                # Implement single fixture constraints via the domain.
                f.pycsp3 = pycsp3.Var(dom=self.dom(f), id=f.sanitized_name)

        # Constraint: teams can only play one fixture per day.
        for t in self.league.teams:
            pycsp3.satisfy(pycsp3.AllDifferent([f.pycsp3 for f in t.fixtures]))

        # Constraint: venues have a maximum number of matches per day.
        for (v, _wd) in self.league.venues:
            dom: set[date] = {d for f in v.fixtures if f.pycsp3 is not None for d in f.pycsp3.dom.all_values()} # pyright: ignore[reportUnknownVariableType]
            pycsp3.satisfy(pycsp3.Cardinality([f.pycsp3 for f in v.fixtures], occurrences={d:range(0, v.maxMatchesPerDay+1) for d in dom}))

        # Constraint: first matches of a club's teams in a division are between themselves.
        hasFirstMatchConstraint: set[Team] = set()
        firstMatches: set[Fixture] = set()
        for t in self.league.teams:
            if t not in hasFirstMatchConstraint:
                hasFirstMatchConstraint.add(t)
                candidates = [f for f in t.fixtures if f.home == t and f.sameClub()]
                if len(candidates) > 0:
                    best = [f for f in candidates if f.away not in hasFirstMatchConstraint]
                    chosen = best[0] if len(best) > 0 else candidates[0]
                    firstMatches.add(chosen)
                    pycsp3.satisfy(chosen.pycsp3 < pycsp3.Minimum(f.pycsp3 for u in chosen.teams for f in u.fixtures if f not in firstMatches)) # pyright: ignore [reportOperatorIssue]
                    hasFirstMatchConstraint.add(chosen.away)

        # Constraint or optimization: adjacent teams of a club shouldn't play on the same day.
        adjacentTeams = [ # pyright: ignore[reportUnknownVariableType]
            f1.pycsp3 == f2.pycsp3
            for c in self.league.clubs
            for (t1, t2) in pairwise(c.teams)
            for f1 in t1.fixtures
            if f1.teams != frozenset({t1, t2})
            for f2 in t2.fixtures
            if f2.teams != frozenset({t1, t2})
        ]
        optAdjacentTeams = 0
        if self.adjacentTeamsAsConstraint:
            # As a constraint
            pycsp3.satisfy(pycsp3.NoneHold(adjacentTeams))
        else:
            # As an optimization
            optAdjacentTeams = -50 * pycsp3.Sum(adjacentTeams) # pyright: ignore [reportOperatorIssue, reportUnknownVariableType]

        # Constraint and optimization: fixture pairs played with time between them.
        pycsp3.satisfy(
            pycsp3.abs(f1.pycsp3 - f2.pycsp3) >= 7*7 # pyright: ignore [reportOperatorIssue, reportUnknownArgumentType]
            for (f1, f2) in self.league.fixturePairs
        )

        # Optimization: teams alternate between playing away and at home.
        def homeAwayConstraint(t: Team) -> Any:
            homeFixtures: list[Fixture] = [f for f in t.fixtures if f.home == t]
            awayFixtures: list[Fixture] = [f for f in t.fixtures if f.home != t]

            def mkConstraint(homeFixture: Fixture, homeRest: Iterable[Fixture]) -> Any:
                # If all fixtures alternated, then
                #
                #    (x - y) in {0, 1}
                #
                # where
                #
                #    x := number of away fixtures after this fixture
                #    y := humber of home fixtures after this fixture
                #
                #
                # Since we're interested in making this an optimization constraint,
                # we can ask for the number - abs(x - y) to be maximized instead.
                count = lambda fs: pycsp3.NValues(within=(pycsp3.Maximum(homeFixture.pycsp3, f.pycsp3) - homeFixture.pycsp3 for f in fs), excepting=0) # pyright: ignore
                x = count(awayFixtures)
                y = count(homeRest)
                print('.', end='')
                return - pycsp3.abs(x - y) # pyright: ignore

            print('\t', end='')
            c = pycsp3.Sum(mkConstraint(homeFixture, homeRest) for (homeFixture, homeRest) in extract(homeFixtures)) # pyright: ignore[reportUnknownVariableType]
            print('')
            return c # pyright: ignore[reportUnknownVariableType]

        optHomeAway = pycsp3.Sum( # pyright: ignore[reportUnknownVariableType]
                homeAwayConstraint(t)
                for t in self.league.teams
            )

        # Optimization: venues have matches assigned to most of their days.
        optVenues = pycsp3.Sum( # pyright: ignore[reportUnknownVariableType]
            pycsp3.NValues(f.pycsp3 for f in v.fixtures if f.weekday == wd)
            for (v, wd) in self.league.venues
            if not v.minimizeEmptyDays
        )

        # Optimization: venues can choose to minimize empty days.
        optVenuesEmptyDays = -1 * pycsp3.Sum( # pyright: ignore [reportOperatorIssue, reportUnknownVariableType]
            pycsp3.NValues(f.pycsp3 for f in v.fixtures if f.weekday == wd)
            for (v, wd) in self.league.venues
            if v.minimizeEmptyDays
        )

        # Optimization: space out the matches of a team.
        optSpaceTeams = pycsp3.Sum( # pyright: ignore[reportUnknownVariableType]
            pycsp3.Minimum(pycsp3.abs(f1.pycsp3 - f2.pycsp3) for (f1, f2) in pairs(t.fixtures)) # pyright: ignore [reportOperatorIssue, reportUnknownArgumentType]
            for t in self.league.teams
        )

        # Optimization: division should have matches on as many days as possible.
        optSpaceDivision = pycsp3.Sum( # pyright: ignore[reportUnknownVariableType]
            pycsp3.NValues(f.pycsp3 for f in d.fixtures)
            for d in self.league.divisions
        )

        pycsp3.maximize(0 # pyright: ignore [reportOperatorIssue]
                + optSpaceTeams
                + optSpaceDivision
                + optVenues
                + optVenuesEmptyDays
                + optHomeAway
                + optAdjacentTeams)

    def solve(self) -> None:
        print("\tCreating constraints...")
        self.__createConstraints()
        print("\tAsking for a solution...")
        r = pycsp3.solve()
        if r is not pycsp3.SAT:
            print("Not SAT, trying to extract CORE.")
            if pycsp3.solve(verbose=2, extraction=True) is pycsp3.CORE:
                print(pycsp3.core())
            raise UnsatisfiableConstraints(str(r))

        print("\tExtracting solution")
        for f in self.league.fixtures:
            v = pycsp3.value(f.pycsp3) # pyright: ignore[reportUnknownVariableType]
            if isinstance(v, int):
                f.date = self.intToDate(v)
            else:
                raise Exception(f"pycsp3.value({f.pycsp3}) is {v}, not an int")

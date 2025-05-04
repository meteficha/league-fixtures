# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from datetime import date
from itertools import pairwise
from typing import Any, Iterator, Literal
from pycsp3.classes.main.variables import Variable
import pycsp3
import pycsp3.functions as pycsp3f
import pycsp3.classes.entities as pycsp3ce

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

    def __init__(self, league: League, solver: Literal['ACE', 'CHOCO'] = 'ACE', solverOptions: str = ''):
        if Solver.created:
            raise Exception("pycsp3 is silly, you can't create two Solvers")
        Solver.created = True
        super().__init__(league)
        self.constraints = False
        self.adjacentTeamsAsConstraint = True
        self.vars: dict[Fixture, Variable] = {}
        self.solver = pycsp3.CHOCO if solver == 'CHOCO' else pycsp3.ACE
        self.solverOptions = solverOptions

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
            self.vars = {}
            pycsp3ce.clear()
        self.constraints = True

        # Constraints on single fixtures
        for f in self.league.fixtures:
            if f.date is not None:
                # Allow for fixture dates to be decided manually.
                self.vars[f] = pycsp3f.Var(dom=self.dateToInt(f.date), id=f.sanitized_name)
            else:
                # Implement single fixture constraints via the domain.
                self.vars[f] = pycsp3f.Var(dom=self.dom(f), id=f.sanitized_name)

        # Constraint: teams can only play one fixture per day.
        for t in self.league.teams:
            pycsp3f.satisfy(pycsp3f.AllDifferent([self.vars[f] for f in t.fixtures]))

        # Constraint: venues have a maximum number of matches per day.
        for v in self.league.venues:
            dom: set[date] = {d for f in v.fixtures for d in self.vars[f].dom.all_values()} # pyright: ignore[reportAttributeAccessIssue]
            pycsp3f.satisfy(pycsp3f.Cardinality([self.vars[f] for f in v.fixtures], occurrences={d:range(0, v.maxMatchesPerDay+1) for d in dom}))

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
                    pycsp3f.satisfy(self.vars[chosen] < pycsp3f.Minimum(self.vars[f] for u in chosen.teams for f in u.fixtures if f not in firstMatches))
                    hasFirstMatchConstraint.add(chosen.away)

        # Constraint or optimization: adjacent teams of a club shouldn't play on the same day.
        adjacentTeams = [
            self.vars[f1] == self.vars[f2]
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
            pycsp3f.satisfy(pycsp3f.NoneHold(adjacentTeams))
        else:
            # As an optimization
            optAdjacentTeams = -50 * pycsp3f.Sum(adjacentTeams)

        # Constraint and optimization: fixture pairs played with time between them.
        pycsp3f.satisfy(
            pycsp3f.abs(self.vars[f1] - self.vars[f2]) >= 7*7 # pyright: ignore [reportOperatorIssue]
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
                count = lambda fs: pycsp3f.NValues(within=(pycsp3f.Maximum(self.vars[homeFixture], self.vars[f]) - self.vars[homeFixture] for f in fs), excepting=0) # pyright: ignore[reportUnknownLambdaType]
                x = count(awayFixtures)
                y = count(homeRest)
                print('.', end='', flush=True)
                return - pycsp3f.abs(x - y)

            print('\t', end='')
            c = pycsp3f.Sum(mkConstraint(homeFixture, homeRest) for (homeFixture, homeRest) in extract(homeFixtures))
            print('')
            return c

        optHomeAway = pycsp3f.Sum(
                homeAwayConstraint(t)
                for t in self.league.teams
            )

        # Optimization: venues have matches assigned to most of their days.
        optVenues = pycsp3f.Sum(
            pycsp3f.NValues(self.vars[f] for f in v.fixtures)
            for v in self.league.venues
            if not v.minimizeEmptyDays
        )

        # Optimization: venues can choose to minimize empty days.
        optVenuesEmptyDays = -1 * pycsp3f.Sum(
            pycsp3f.NValues(self.vars[f] for f in v.fixtures)
            for v in self.league.venues
            if v.minimizeEmptyDays
        )

        # Optimization: space out the matches of a team.
        optSpaceTeams = pycsp3f.Sum(
            pycsp3f.Minimum(pycsp3f.abs(self.vars[f1] - self.vars[f2]) for (f1, f2) in pairs(t.fixtures)) # pyright: ignore [reportOperatorIssue]
            for t in self.league.teams
        )

        # Optimization: division should have matches on as many days as possible.
        optSpaceDivision = pycsp3f.Sum(
            pycsp3f.NValues(self.vars[f] for f in d.fixtures)
            for d in self.league.divisions
        )

        pycsp3f.maximize(0
                + optSpaceTeams
                + optSpaceDivision
                + optVenues
                + optVenuesEmptyDays
                + optHomeAway
                + optAdjacentTeams)

    def solve(self) -> None:
        print("\tCreating constraints...")
        self.__createConstraints()
        print("\tAsking for a solution... (press Ctrl-C to save best solution so far)")
        r = pycsp3.solve(solver=self.solver, options=self.solverOptions, verbose=0)
        if r is not pycsp3.SAT and r is not pycsp3.OPTIMUM:
            print("Not SAT, trying to extract CORE.")
            if pycsp3.solve(solver=self.solver, options=self.solverOptions, verbose=0, extraction=True) is pycsp3.CORE:
                print(pycsp3.core())
            raise UnsatisfiableConstraints(str(r))

        if r is pycsp3.OPTIMUM:
            print('\tFound the best solution. Wow!')
        print("\tExtracting solution")
        for f in self.league.fixtures:
            v = pycsp3f.value(self.vars[f])
            if isinstance(v, int):
                f.date = self.intToDate(v)
            else:
                raise Exception(f"pycsp3f.value({self.vars[f]}) is {v}, not an int")

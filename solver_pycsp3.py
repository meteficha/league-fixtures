# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from datetime import date
from itertools import chain, pairwise
from typing import Any, Iterator, Literal
from pycsp3.classes.main.variables import Variable
from pycsp3.tools.curser import ListVar
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

def alternate[T](xs: Iterable[T], ys: Iterable[T]) -> Iterable[T]:
    """alternate([a0, ..., ak], [b0, ..., bk]) = [a0, b0, a1, b1, ..., ak, bk]

    >>> list(alternate([1,3,5,7], [2,4,6,8]))
    [1, 2, 3, 4, 5, 6, 7, 8]
    """
    ai = xs.__iter__()
    bi = ys.__iter__()
    try:
        while True:
            yield next(ai)
            (ai, bi) = (bi, ai)
    except StopIteration:
        return

def domUnion(vs: Iterable[Variable]) -> set[int]:
    return set(x for v in vs for x in v.dom) # pyright: ignore[reportAttributeAccessIssue]

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

        self.adjacentTeamsConstraint = True # Prevent Team t from playing on the same day as Team (t-1) or Team (t+1) from the same club.
        self.strictHomeAwayConstraint: int | None = 2 # Maximum number of back-to-back games at home or away.
        self.strictMatchSpaceOut: int | None = 5 # Minimum number of days between back-to-back games of a team.

        self.homeFixtureArrays: dict[Team, ListVar] = dict()
        self.homeFixtureDomains: dict[Team, set[int]] = dict()
        self.vars: dict[Fixture, Variable] = dict()
        self.solver = pycsp3.CHOCO if solver == 'CHOCO' else pycsp3.ACE
        self.solverOptions = solverOptions


    def dom(self, f: Fixture) -> set[int]:
        # Allow for fixture dates to be decided manually.
        if f.date is not None:
            return { self.dateToInt(f.date) }

        # Constraint: respects club late starts.
        start: int = max(self.dateToInt(d) for d in [self.league.start, f.home.club.lateStart, f.away.club.lateStart] if d is not None)

        # Constraint: played within start/end dates.
        # Constraint: played on venue's weekday.
        ret = {d for d in self.possibleDays(f.weekday) if d >= start}

        # Constraint: not played on a holiday.
        ret.difference_update(self.holidaysLeague)
        ret.difference_update(self.holidaysPerVenue[f.venue])
        ret.difference_update(self.holidaysPerClub[f.home.club])
        ret.difference_update(self.holidaysPerClub[f.away.club])
        ret.difference_update(f.home.calendar.holidays)
        ret.difference_update(f.away.calendar.holidays)

        # Constraint: matches between teams of the same club must be played by 31 Jan.
        if f.sameClub():
            ret = {d for d in ret if d <= self.dateToInt(date(self.league.end.year, 1, 31))}

        return ret

    def __createConstraints(self) -> None:
        if self.constraints:
            self.vars = {}
            pycsp3ce.clear()
        self.constraints = True

        print("\t\tSingle fixture constraints")
        for t in self.league.teams:
            # For every fixture f, there is one, and only one, team for which f is a home fixture.
            # Therefore, we only need to go through home fixtures here.
            homeFixtures = list(t.homeFixtures)
            doms = list(map(self.dom, homeFixtures)) # Implement single fixture constraints via the domain.
            self.homeFixtureArrays[t] = pycsp3f.VarArray(size=len(homeFixtures), dom=lambda i=0: doms[i], id='homeFixtures_' + t.sanitized_name, comment=str([f.name for f in homeFixtures]))
            self.homeFixtureDomains[t] = set.union(*doms)
            for (f, v) in zip(homeFixtures, self.homeFixtureArrays[t]):
                self.vars[f] = v

        print("\t\tTeams can only play one fixture per day")
        for t in self.league.teams:
            pycsp3f.satisfy(pycsp3f.AllDifferent([self.vars[f] for f in t.fixtures]))

        print("\t\tVenues have a maximum number of matches per day")
        for v in self.league.venues:
            dom: set[date] = {d for f in v.fixtures for d in self.vars[f].dom} # pyright: ignore[reportAttributeAccessIssue]
            pycsp3f.satisfy(pycsp3f.Cardinality([self.vars[f] for f in v.fixtures], occurrences={d:range(0, v.maxMatchesPerDay+1) for d in dom}))

        print("\t\tFirst matches of a club's teams in a division are between themselves")
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
                    pycsp3f.satisfy(self.vars[chosen] < self.vars[f] for u in chosen.teams for f in u.fixtures if f not in firstMatches) # pyright: ignore[reportOperatorIssue]
                    hasFirstMatchConstraint.add(chosen.away)

        if self.adjacentTeamsConstraint:
            print("\t\tAdjacent teams of a club shouldn't play on the same day")
            pycsp3f.satisfy(
                pycsp3f.AllDifferent(self.vars[f] for t in [t1, t2] for f in t.fixtures if not f.sameClub())
                for c in self.league.clubs
                for (t1, t2) in pairwise(c.teams)
            )

        print("\t\tFixture pairs played with time between them (7 weeks)")
        pycsp3f.satisfy(
            pycsp3f.abs(self.vars[f1] - self.vars[f2]) >= 7*7 # pyright: ignore [reportOperatorIssue]
            for (f1, f2) in self.league.fixturePairs
        )

        print("\t\tOnly when constraints")
        for ow in self.league.onlyWhen:
            print("\t\t\t" + ow.constrained.name + " plays at home only when " + ow.reference.name + " plays at home", end='', flush=True)
            for t in ow.constrained.teams:
                for f in t.homeFixtures:
                    pycsp3f.satisfy(
                        pycsp3f.Exist([self.homeFixtureArrays[t2] for t2 in ow.reference.teams], value = self.vars[f])
                    )
            print(".")

        print("\t\tTeams alternate between playing away and at home", end='', flush=True)
        optHomeAway = 0
        def satisfyHomeAwayConstraint(t: Team) -> Any:
            awayFixtures: list[Fixture] = list(t.awayFixtures)
            n = len(awayFixtures)
            if n < 1:
                return
            homeFixtureArr = self.homeFixtureArrays[t]
            assert len(homeFixtureArr) == n
            awayDomain = domUnion(self.vars[f] for f in awayFixtures)
            awayFixtureArr = pycsp3f.VarArray(size=n, dom=awayDomain, id="awayFixtureArr_" + t.sanitized_name)
            homeIxArr = pycsp3f.VarArray(size=n, dom=range(n), id="homeIxArr_" + t.sanitized_name)
            awayIxArr = pycsp3f.VarArray(size=n, dom=range(n), id="awayIxArr_" + t.sanitized_name)
            sortedHomeFixtureArr = pycsp3f.VarArray(size=n, dom=self.homeFixtureDomains[t], id="sortedHomeFixtureArr_" + t.sanitized_name)
            sortedAwayFixtureArr = pycsp3f.VarArray(size=n, dom=awayDomain, id="sortedAwayFixtureArr_" + t.sanitized_name)
            pycsp3f.satisfy(list(chain([
                    awayFixtureArr[i] == self.vars[awayFixtures[i]],
                    sortedHomeFixtureArr[i] == homeFixtureArr[homeIxArr[i]],
                    sortedAwayFixtureArr[i] == awayFixtureArr[awayIxArr[i]],
                ] for i in range(n))))
            pycsp3f.satisfy([
                pycsp3f.AllDifferent(homeIxArr),
                pycsp3f.AllDifferent(awayIxArr),
                pycsp3f.Increasing(sortedHomeFixtureArr, strict=True),
                pycsp3f.Increasing(sortedAwayFixtureArr, strict=True),
            ])
            print('.', end='', flush=True)
            if self.strictHomeAwayConstraint == 1:
                pycsp3f.satisfy(pycsp3f.Or(
                    pycsp3f.Increasing(alternate(sortedHomeFixtureArr, sortedAwayFixtureArr), strict=True),
                    pycsp3f.Increasing(alternate(sortedAwayFixtureArr, sortedHomeFixtureArr), strict=True),
                    ))
                return None
            else:
                toConsider = []
                if not any(f in firstMatches for f in awayFixtures):
                    toConsider.append((sortedHomeFixtureArr, sortedAwayFixtureArr, "homeAway"))
                if not any(f in firstMatches for f in t.homeFixtures):
                    toConsider.append((sortedAwayFixtureArr, sortedHomeFixtureArr, "awayHome"))
                if not toConsider:
                    return None

                def buildArr(as_: list[Any], bs: list[Any], id: str) -> Variable:
                    pairs = list(pairwise(alternate(as_, bs)))
                    arr = pycsp3f.VarArray(size=len(pairs), dom=[0, 1], id=id)
                    pycsp3f.satisfy(
                        arr[i] == (a < b)
                        for (i, (a, b)) in enumerate(pairs)
                    )
                    return arr

                arrays = [buildArr(as_, bs, prefix + 'ConstraintArr_' + t.sanitized_name) for (as_, bs, prefix) in toConsider]
                countWrong = pycsp3f.Minimum(pycsp3f.Count(array, value=0) for array in arrays)
                if self.strictHomeAwayConstraint:
                    pycsp3f.satisfy(countWrong < self.strictHomeAwayConstraint)
                return countWrong
        optTerms = [c for c in map(satisfyHomeAwayConstraint, self.league.teams) if c is not None]
        if optTerms:
            optHomeAway = pycsp3f.Sum(c for c in optTerms) * (-10)
        print('')

        print("\t\tVenues have matches assigned to most of their days")
        optVenues = pycsp3f.Sum(
            pycsp3f.NValues(self.vars[f] for f in v.fixtures)
            for v in self.league.venues
            if not v.minimizeEmptyDays
        )

        print("\t\tVenues can choose to minimize empty days")
        optVenuesEmptyDays = -1 * pycsp3f.Sum(
            pycsp3f.NValues(self.vars[f] for f in v.fixtures)
            for v in self.league.venues
            if v.minimizeEmptyDays
        )

        print("\t\tSpace out the matches of a team")
        spaceTeamsTerms = [
            [pycsp3f.abs(self.vars[f1] - self.vars[f2]) for (f1, f2) in pairs(t.fixtures)] # pyright: ignore [reportOperatorIssue]
            for t in self.league.teams
        ]
        optSpaceTeams = pycsp3f.Sum(x for xs in spaceTeamsTerms for x in xs)
        if self.strictMatchSpaceOut:
            pycsp3f.satisfy(t >= self.strictMatchSpaceOut for ts in spaceTeamsTerms for t in ts)

        print("\t\tDivision should have matches on as many days as possible")
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
                )

    def solve(self) -> None:
        print("\tCreating constraints...")
        self.__createConstraints()
        print("\tAsking for a solution... (press Ctrl-C to save best solution so far)\n\n\n")
        r = pycsp3.solve(solver=self.solver, options=self.solverOptions, verbose=0)
        if r is not pycsp3.SAT and r is not pycsp3.OPTIMUM:
            raise UnsatisfiableConstraints(str(r))

        if r is pycsp3.OPTIMUM:
            print('\n\n\tFound the best solution. Wow!')
        print("\n\n\tExtracting solution")
        for f in self.league.fixtures:
            v = pycsp3f.value(self.vars[f])
            if isinstance(v, int):
                f.date = self.intToDate(v)
            else:
                raise Exception(f"pycsp3f.value({self.vars[f]}) is {v}, not an int")

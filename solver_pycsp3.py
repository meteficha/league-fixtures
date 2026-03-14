# pyright: strict, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from datetime import date
from dataclasses import dataclass, field
from itertools import chain, pairwise
from typing import Any, Iterator, Literal, Sequence
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


@dataclass
class ConstraintContext:
    solver: "Solver"
    vars: dict[Fixture, Variable] = field(default_factory=dict)
    homeFixtureArrays: dict[Team, ListVar] = field(default_factory=dict)
    homeFixtureDomains: dict[Team, set[int]] = field(default_factory=dict)
    firstMatches: set[Fixture] = field(default_factory=set)


class Constraint:
    def apply(self, ctx: ConstraintContext) -> None:
        raise NotImplementedError()

    def objective_term(self, _ctx: ConstraintContext) -> Any:
        return 0


class SingleFixtureDomainConstraint(Constraint):
    def apply(self, ctx: ConstraintContext) -> None:
        print("\t\tSingle fixture constraints")
        for t in ctx.solver.league.teams:
            # For every fixture f, there is one, and only one, team for which f is a home fixture.
            # Therefore, we only need to go through home fixtures here.
            homeFixtures = list(t.homeFixtures)
            doms = list(map(ctx.solver.dom, homeFixtures)) # Implement single fixture constraints via the domain.
            ctx.homeFixtureArrays[t] = pycsp3f.VarArray(size=len(homeFixtures), dom=lambda i=0: doms[i], id='homeFixtures_' + t.sanitized_name, comment=str([f.name for f in homeFixtures]))
            ctx.homeFixtureDomains[t] = set.union(*doms)
            for (f, v) in zip(homeFixtures, ctx.homeFixtureArrays[t]):
                ctx.vars[f] = v


class TeamNoOverlapAndSpacingConstraint(Constraint):
    def __init__(self, strictMatchSpaceOut: int | None = 5) -> None:
        self.strictMatchSpaceOut = strictMatchSpaceOut
        self._optSpaceTeams: Any = 0

    def apply(self, ctx: ConstraintContext) -> None:
        print("\t\tTeams can only play one fixture per day / Space out the matches of a team")
        self._optSpaceTeams = 0
        spaceNoMoreOpt = pycsp3f.Var(dom=[7*3], id='spaceNoMoreOpt') # Spacing bigger than this shouldn't count for optimization.
        for t in ctx.solver.league.teams:
            minimum = self.strictMatchSpaceOut if self.strictMatchSpaceOut is not None and not t.relaxed else 1
            arr = pycsp3f.VarArray(
                size=len(t.fixtures),
                dom=range(minimum, 365),
                id="SpaceOut_NoOverlap_"+t.sanitized_name
                )
            pycsp3f.satisfy(pycsp3f.NoOverlap(origins=[ctx.vars[f] for f in t.fixtures], lengths=arr))
            self._optSpaceTeams += pycsp3f.Sum(10 * pycsp3f.Minimum(v, spaceNoMoreOpt) for v in arr)

    def objective_term(self, _ctx: ConstraintContext) -> Any:
        return self._optSpaceTeams


class MaxConsecutiveWeeksConstraint(Constraint):
    def __init__(self, strictMaxNoWeeksWithMatches: int | None = 2) -> None:
        self.strictMaxNoWeeksWithMatches = strictMaxNoWeeksWithMatches

    def apply(self, ctx: ConstraintContext) -> None:
        if self.strictMaxNoWeeksWithMatches is None:
            return
        print("\t\tTeams can only have " + str(self.strictMaxNoWeeksWithMatches) + " consecutive weeks with matches")
        for t in ctx.solver.league.teams:
            if not t.relaxed:
                pycsp3f.satisfy(pycsp3f.Cumulative(origins=[ctx.vars[f] for f in t.fixtures], lengths=(self.strictMaxNoWeeksWithMatches+1)*7, heights=1) <= self.strictMaxNoWeeksWithMatches)


class VenueDailyCapacityConstraint(Constraint):
    def apply(self, ctx: ConstraintContext) -> None:
        print("\t\tVenues have a maximum number of matches per day")
        for v in ctx.solver.league.venues:
            dom: set[date] = {d for f in v.fixtures for d in ctx.vars[f].dom} # pyright: ignore[reportAttributeAccessIssue]
            pycsp3f.satisfy(pycsp3f.Cardinality([ctx.vars[f] for f in v.fixtures], occurrences={d:range(0, v.maxMatchesPerDay+1) for d in dom}))


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
                    pycsp3f.satisfy(ctx.vars[chosen] < ctx.vars[f] for u in chosen.teams for f in u.fixtures if f not in ctx.firstMatches) # pyright: ignore[reportOperatorIssue]
                    hasFirstMatchConstraint.add(chosen.away)


class AdjacentTeamsDifferentDayConstraint(Constraint):
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def apply(self, ctx: ConstraintContext) -> None:
        if not self.enabled:
            return
        print("\t\tAdjacent teams of a club shouldn't play on the same day")
        pycsp3f.satisfy(
            pycsp3f.AllDifferent(ctx.vars[f] for t in [t1, t2] for f in t.fixtures if not f.teams == frozenset([t1, t2]))
            for c in ctx.solver.league.clubs
            if not c.relaxed
            for (t1, t2) in pairwise(c.teams)
        )


class FixturePairSpacingConstraint(Constraint):
    def __init__(self, strictFixturePairSpacing: int | None = None) -> None:
        self.strictFixturePairSpacing = strictFixturePairSpacing

    def apply(self, ctx: ConstraintContext) -> None:
        if self.strictFixturePairSpacing is None:
            return
        print(f"\t\tFixture pairs played with time between them ({str(self.strictFixturePairSpacing)} weeks)")
        pycsp3f.satisfy(
            pycsp3f.abs(ctx.vars[f1] - ctx.vars[f2]) >= self.strictFixturePairSpacing*7 # pyright: ignore [reportOperatorIssue]
            for (f1, f2) in ctx.solver.league.fixturePairs
            if not f1.home.relaxed and not f1.away.relaxed
        )


class OnlyWhenConstraint(Constraint):
    def apply(self, ctx: ConstraintContext) -> None:
        print("\t\tOnly when constraints")
        for ow in ctx.solver.league.onlyWhen:
            print("\t\t\t" + ow.constrained.name + " plays at home only when " + ow.reference.name + " plays at home", end='', flush=True)
            unconstrainedArray = []
            if ow.unconstrainedDays and len(ow.unconstrainedDays.holidays) > 0:
                unconstrainedDates = [ctx.solver.dateToInt(d) for d in ow.unconstrainedDays.holidays] if ow.unconstrainedDays else []
                unconstrainedArray = pycsp3f.VarArray(
                    size=len(unconstrainedDates),
                    dom=unconstrainedDates,
                    id="unconstrainedArray_" + ow.constrained.sanitized_name + "_" + ow.reference.sanitized_name)
                pycsp3f.satisfy(unconstrainedArray[i] == unconstrainedDates[i] for i in range(len(unconstrainedDates)))
            for t in ow.constrained.teams:
                for f in t.homeFixtures:
                    pycsp3f.satisfy(
                        pycsp3f.Exist([ctx.homeFixtureArrays[t2] for t2 in ow.reference.teams] + [v for v in unconstrainedArray], value = ctx.vars[f])
                    )
            print(".")


class HomeAwayAlternationConstraint(Constraint):
    def __init__(self, strictHomeAwayConstraint: int | None = None) -> None:
        self.strictHomeAwayConstraint = strictHomeAwayConstraint
        self._optHomeAway: Any = 0

    def apply(self, ctx: ConstraintContext) -> None:
        print("\t\tTeams alternate between playing away and at home", end='', flush=True)
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
            pycsp3f.satisfy(list(chain([
                    awayFixtureArr[i] == ctx.vars[awayFixtures[i]],
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

            def buildArr(as_: list[Any], bs: list[Any], id: str) -> Variable:
                pairs = list(pairwise(alternate(as_, bs)))
                arr = pycsp3f.VarArray(size=len(pairs), dom=[0, 1], id=id)
                pycsp3f.satisfy(
                    arr[i] == (a >= b) # 1 iff the wrong way around
                    for (i, (a, b)) in enumerate(pairs)
                )
                return arr

            arrays = [buildArr(as_, bs, prefix + 'ConstraintArr_' + t.sanitized_name) for (as_, bs, prefix) in toConsider]
            countWrongs = [pycsp3f.Sum(array) for array in arrays]
            if self.strictHomeAwayConstraint is not None and not t.relaxed:
                pycsp3f.satisfy(pycsp3f.Or(cw <= self.strictHomeAwayConstraint for cw in countWrongs))
            return pycsp3f.Minimum(countWrongs)

        optTerms = [c for c in map(satisfyHomeAwayConstraint, ctx.solver.league.teams) if c is not None]
        if optTerms:
            self._optHomeAway = pycsp3f.Sum(c for c in optTerms) * (-100)
        print('')

    def objective_term(self, _ctx: ConstraintContext) -> Any:
        return self._optHomeAway


class XmasBreakBalanceConstraint(Constraint):
    def __init__(self, strictXmasBreakDiff: int | None = 0, strictXmasBreakPercentage: float = 0.8) -> None:
        self.strictXmasBreakDiff = strictXmasBreakDiff
        self.strictXmasBreakPercentage = strictXmasBreakPercentage
        self._optXmas: Any = 0

    def apply(self, ctx: ConstraintContext) -> None:
        self._optXmas = 0
        if self.strictXmasBreakDiff is None:
            return
        print("\t\tFixtures should be evenly distributed before/after Xmas break")
        beforeXmasBreakDates = range(ctx.solver.dateToInt(date(ctx.solver.league.end.year, 1, 1)))
        xmasTerms = [
            (len(t.fixtures) // 2, pycsp3f.Count([ctx.vars[f] for f in t.fixtures], values=beforeXmasBreakDates))
            for t in ctx.solver.league.teams
            ]
        xmasArr = pycsp3f.VarArray(size=len(xmasTerms), dom=[0, 1], id='xmasArr')

        if self.strictXmasBreakDiff <= 0:
            pycsp3f.satisfy(xmasArr[i] == (t == u) for (i, (t, u)) in enumerate(xmasTerms))
        else:
            pycsp3f.satisfy(xmasArr[i] == (pycsp3f.abs(t - u) <= self.strictXmasBreakDiff) for (i, (t, u)) in enumerate(xmasTerms))

        if self.strictXmasBreakPercentage >= 0.99999:
            pycsp3f.satisfy(xmasArr[i] == 1 for i in range(len(xmasTerms)))
            return

        xmasArrCount = pycsp3f.Var(id='xmasArrCount', dom=range(len(xmasTerms)+1))
        pycsp3f.satisfy(xmasArrCount == pycsp3f.Count(xmasArr, value=1))
        pycsp3f.satisfy(xmasArrCount >= int(len(xmasTerms) * self.strictXmasBreakPercentage))
        self._optXmas = 500 * xmasArrCount

    def objective_term(self, _ctx: ConstraintContext) -> Any:
        return self._optXmas


class VenueAssignedDaysObjectiveConstraint(Constraint):
    def objective_term(self, ctx: ConstraintContext) -> Any:
        print("\t\tVenues have matches assigned to most of their days")
        return pycsp3f.Sum(
            pycsp3f.NValues(ctx.vars[f] for f in v.fixtures)
            for v in ctx.solver.league.venues
            if not v.minimizeEmptyDays
        )


class VenueMinimizeEmptyDaysObjectiveConstraint(Constraint):
    def objective_term(self, ctx: ConstraintContext) -> Any:
        print("\t\tVenues can choose to minimize empty days")
        return -1 * pycsp3f.Sum(
            pycsp3f.NValues(ctx.vars[f] for f in v.fixtures)
            for v in ctx.solver.league.venues
            if v.minimizeEmptyDays
        )


class DivisionDaySpreadObjectiveConstraint(Constraint):
    def objective_term(self, ctx: ConstraintContext) -> Any:
        print("\t\tDivision should have matches on as many days as possible")
        return pycsp3f.Sum(
            pycsp3f.NValues(ctx.vars[f] for f in d.fixtures)
            for d in ctx.solver.league.divisions
        )

class Solver(SolverBase):
    """Update every fixture of the given league with dates that
    fit the necessary constraints."""
    created = False

    def __init__(self, league: League, constraints: Sequence[Constraint], solver: Literal['ACE', 'CHOCO'] = 'ACE', solverOptions: str = ''):
        if Solver.created:
            raise Exception("pycsp3 is silly, you can't create two Solvers")
        Solver.created = True
        super().__init__(league)
        self.constraintsCreated = False
        self.constraintsPipeline = list(constraints)

        self.homeFixtureArrays: dict[Team, ListVar] = dict()
        self.homeFixtureDomains: dict[Team, set[int]] = dict()
        self.vars: dict[Fixture, Variable] = dict()
        self.solver = pycsp3.CHOCO if solver == 'CHOCO' else pycsp3.ACE
        self.solverOptions = solverOptions


    def dom(self, f: Fixture) -> set[int]:
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
        ret.difference_update(self.holidaysPerTeam[f.home])
        ret.difference_update(self.holidaysPerTeam[f.away])

        # Constraint: matches between teams of the same club must be played by 31 Jan.
        if f.sameClub():
            ret = {d for d in ret if d <= self.dateToInt(date(self.league.end.year, 1, 31))}

        # Allow for fixture dates to be decided manually.
        if f.date is not None:
            ret.intersection_update({ self.dateToInt(f.date) })

        return ret

    def __createConstraints(self) -> None:
        if self.constraintsCreated:
            self.vars = {}
            pycsp3ce.clear()
        self.constraintsCreated = True

        ctx = ConstraintContext(solver=self)

        objective_terms: list[Any] = []
        for constraint in self.constraintsPipeline:
            constraint.apply(ctx)
            objective_terms.append(constraint.objective_term(ctx))

        objective = 0
        for term in objective_terms:
            objective += term
        pycsp3f.maximize(objective)

        self.vars = ctx.vars
        self.homeFixtureArrays = ctx.homeFixtureArrays
        self.homeFixtureDomains = ctx.homeFixtureDomains

    def solve(self) -> None:
        print("\tCreating constraints...")
        self.__createConstraints()
        print("\tAsking for a solution... (press Ctrl-C to save best solution so far)\n\n\n")
        r = pycsp3.solve(solver=self.solver, options=self.solverOptions, verbose=0)
        if r is not pycsp3.SAT and r is not pycsp3.OPTIMUM:
            # r = pycsp3.solve(solver=self.solver, options=self.solverOptions, verbose=0, extraction=True)
            # print(pycsp3.core())
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


def create_default_constraints() -> list[Constraint]:
    return [
        SingleFixtureDomainConstraint(),
        TeamNoOverlapAndSpacingConstraint(strictMatchSpaceOut=5),
        MaxConsecutiveWeeksConstraint(strictMaxNoWeeksWithMatches=2),
        VenueDailyCapacityConstraint(),
        FirstMatchSameClubConstraint(),
        AdjacentTeamsDifferentDayConstraint(enabled=True),
        FixturePairSpacingConstraint(strictFixturePairSpacing=None),
        OnlyWhenConstraint(),
        HomeAwayAlternationConstraint(strictHomeAwayConstraint=None),
        XmasBreakBalanceConstraint(strictXmasBreakDiff=0, strictXmasBreakPercentage=0.8),
        VenueAssignedDaysObjectiveConstraint(),
        VenueMinimizeEmptyDaysObjectiveConstraint(),
        DivisionDaySpreadObjectiveConstraint(),
    ]


def create_solver(league: League, solver: Literal['ACE', 'CHOCO'] = 'ACE', solverOptions: str = '') -> Solver:
    return Solver(league=league, constraints=create_default_constraints(), solver=solver, solverOptions=solverOptions)

from datetime import date
import pycsp3

from league import *
from solver_base import SolverBase, UnsatisfiableConstraints

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

    def dom(self, f: Fixture) -> set[int]:
        # Constraint: played within start/end dates.
        # Constraint: played on venue's weekday.
        ret = set(d for d in self.possibleDays(f.weekday))

        # Constraint: not played on a holiday.
        ret.difference_update(self.dateToInt(d) for d in self.league.holidays.get(f.weekday, set()))

        # Constraint: matches between teams of the same club must be played by 31 Jan.
        if f.sameClub():
            ret = set(d for d in ret if d <= self.dateToInt(date(self.league.end.year, 1, 31)))

        return ret

    def __createConstraints(self) -> None:
        if self.constraints:
            return
        self.constraints = True
        pycsp3.clear()

        # Constraints on single fixtures
        for d in self.league.divisions:
            for f in d.fixtures:
                if f.date is not None:
                    # Allow for fixture dates to be decided manually.
                    f.pycsp3 = pycsp3.Var(dom=self.dateToInt(f.date), id=f.sanitized_name)
                else:
                    # Implement single fixture constraints via the domain.
                    f.pycsp3 = pycsp3.Var(dom=self.dom(f), id=f.sanitized_name)

        # Constraint: teams can only play one fixture per day.
        for d in self.league.divisions:
            for t in d.teams:
                pycsp3.satisfy(pycsp3.AllDifferent([f.pycsp3 for f in t.fixtures]))

        # Constraint: venues have a maximum number of matches per day.
        for (v, wd) in self.league.venues:
            pycsp3.satisfy(pycsp3.Cardinality([f.pycsp3 for f in v.fixtures], occurrences={d:range(0, v.maxMatchesPerDay+1) for d in self.possibleDays(wd)}))

        # Constraint: first matches of a club's teams in a division are between themselves.
        hasFirstMatchConstraint = set()
        for d in self.league.divisions:
            for t in d.teams:
                if t not in hasFirstMatchConstraint:
                    hasFirstMatchConstraint.add(t)
                    candidates = [f for f in t.fixtures if f.home == t and f.sameClub()]
                    if len(candidates) > 0:
                        best = [f for f in candidates if f.away not in hasFirstMatchConstraint]
                        chosen = best[0] if len(best) > 0 else candidates[0]
                        pycsp3.satisfy(chosen.pycsp3 < pycsp3.Minimum(f.pycsp3 for f in t.fixtures if chosen != f)) # type: ignore
                        hasFirstMatchConstraint.add(chosen.away)

    def solve(self) -> None:
        self.__createConstraints()
        r = pycsp3.solve()
        if r is pycsp3.UNSAT:
            raise UnsatisfiableConstraints("UNSAT")
        elif r is not pycsp3.SAT:
            raise UnsatisfiableConstraints("Not SAT: " + str(r))

        for d in self.league.divisions:
            for f in d.fixtures:
                v = pycsp3.value(f.pycsp3)
                f.date = self.intToDate(v)

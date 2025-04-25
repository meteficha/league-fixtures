from datetime import date
from league import *

class UnsatisfiableConstraints(Exception):
    pass

class SolverBase:
    """Update every fixture of the given league with dates that
    fit the necessary constraints."""
    def __init__(self, league: League):
        self.league = league

    def dateToInt(self, x: date) -> int:
        return x.toordinal() - self.league.start.toordinal()

    def intToDate(self, x: int) -> date:
        return date.fromordinal(x + self.league.start.toordinal())

    def weekdayToInt(self, x: Weekday) -> int:
        """dateToInt(x) % 7 == weekdayToInt(Weekday.fromDate(x))"""
        offset = Weekday.fromDate(self.league.start).value
        return (x.value - offset) % 7

    def possibleDays(self, x: Weekday) -> range:
        return range(self.weekdayToInt(x), self.dateToInt(self.league.end) - 1, 7)

    def solve(self) -> None:
        raise UnsatisfiableConstraints("SolverBase can't solve")

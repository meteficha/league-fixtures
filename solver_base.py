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

    @cached_property
    def holidaysLeague(self) -> frozenset[int]:
        return frozenset(self.dateToInt(d) for d in self.league.calendar.holidays)

    @cached_property
    def holidaysPerClub(self) -> dict[Club, frozenset[int]]:
        return {c: frozenset(self.dateToInt(d) for d in c.calendar.holidays) for c in self.league.clubs}

    @cached_property
    def holidaysPerTeam(self) -> dict[Team, frozenset[int]]:
        return {t: frozenset(self.dateToInt(d) for d in t.calendar.holidays) for t in self.league.teams}

    @cached_property
    def holidaysPerVenue(self) -> dict[Venue, frozenset[int]]:
        return {v: frozenset(self.dateToInt(d) for d in v.calendar.holidays) for v in self.league.venues}

    def solve(self) -> None:
        raise UnsatisfiableConstraints("SolverBase can't solve")

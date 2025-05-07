# pyright: strict, reportUntypedFunctionDecorator=false
from datetime import date
from enum import IntEnum
from functools import cached_property, partial
from strongtyping.strong_typing import match_typing # pyright: ignore[reportUnknownVariableType]
from typing import Any, Iterable, Self, Union

def dateOrNone(v: str | None) -> date | None:
    if v is None:
        return None
    else:
        return date.fromisoformat(v)

def sanitize(v: str) -> str:
    return v.replace(" ", "_").replace("&", "_")

class Weekday(IntEnum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7

    @classmethod
    def fromDate(cls: type[Self], d: date) -> Self:
        return cls(d.isoweekday())

class Calendar:
    """A set of holidays."""
    @match_typing
    def __init__(self, holidays: Iterable[date] = []):
        self.holidays = frozenset(holidays)

    def to_json(self) -> dict[str, Any]:
        return { "holidays": [str(d) for d in self.holidays] }

    @classmethod
    def from_json(cls: type[Self], o: dict[str, Any]) -> Self:
        return cls(holidays=[date.fromisoformat(d) for d in o["holidays"]])

    @classmethod
    def empty(cls: type[Self]) -> Self:
        return cls([])

    def isHoliday(self, date: date) -> bool:
        return date in self.holidays

class Venue:
    """A venue is a place that clubs use to schedule their matches.

    Multiple clubs may play on the same venue.
    """
    @match_typing
    def __init__(self, name: str, maxMatchesPerDay: int = 2, minimizeEmptyDays: bool = False, calendar: Calendar | None = None):
        self.name = name
        self.maxMatchesPerDay = maxMatchesPerDay
        self.minimizeEmptyDays = minimizeEmptyDays
        self.fixtures: list[Fixture] = []
        self.calendar = calendar if calendar else Calendar()

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "maxMatchesPerDay": self.maxMatchesPerDay,
            "minimizeEmptyDays": self.minimizeEmptyDays,
            "calendar": self.calendar.to_json(),
            }

    @classmethod
    def from_json(cls: type[Self], o: dict[str, Any]) -> Self:
        calendar = Calendar.from_json(o["calendar"]) if "calendar" in o else None
        return cls(name=o["name"], maxMatchesPerDay=o["maxMatchesPerDay"], minimizeEmptyDays=o["minimizeEmptyDays"], calendar=calendar)

class Club:
    """A chess club."""
    @match_typing
    def __init__(self, name: str, venue: Venue, weekday: Weekday, lateStart: date | None = None, calendar: Calendar | None = None):
        self.name = name
        self.venue = venue
        self.weekday = weekday
        self.lateStart = lateStart
        self.teams: list[Team] = []
        self.calendar = calendar if calendar else Calendar()

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "venue": self.venue.name,
            "weekday": self.weekday.value,
            "lateStart": str(self.lateStart) if self.lateStart else None,
            "teams": [t.name for t in self.teams],
            "calendar": self.calendar.to_json(),
            }

    @classmethod
    def from_json(cls: type[Self], venues: dict[str, Venue], o: dict[str, Any]) -> Self:
        calendar = Calendar.from_json(o["calendar"]) if "calendar" in o else None
        club = cls(name=o["name"], venue=venues[o["venue"]], weekday=Weekday(o["weekday"]), lateStart=dateOrNone(o.get("lateStart", None)), calendar=calendar)
        for t in o["teams"]:
            Team(club, name=t)
        return club

class Team:
    """A team from a chess club."""
    @match_typing
    def __init__(self, club: Club, name: str | None = None):
        self.club = club
        self.name = club.name + " " + str(len(club.teams) + 1) if name is None else name
        self.fixtures: list[Fixture] = []
        club.teams.append(self)

    @property
    def homeFixtures(self) -> Iterable['Fixture']:
        return (f for f in self.fixtures if f.home == self)

    @property
    def awayFixtures(self) -> Iterable['Fixture']:
        return (f for f in self.fixtures if f.home != self)

    @cached_property
    def sanitized_name(self) -> str:
        return sanitize(self.name)

    def __str__(self) -> str:
        return self.name

class Fixture:
    """A match between two teams."""
    @match_typing
    def __init__(self, home: Team, away: Team, date: date | None = None):
        self.home = home
        self.away = away
        self.date = date
        home.fixtures.append(self)
        away.fixtures.append(self)
        self.venue.fixtures.append(self)

    def to_json(self) -> dict[str, Any]:
        return {
            "home": self.home.name,
            "away": self.away.name,
            "date": str(self.date) if self.date is not None else None,
            }

    @classmethod
    def from_json(cls: type[Self], teams: dict[str, Team], o: dict[str, Any]) -> Self:
        return cls(home=teams[o["home"]], away=teams[o["away"]], date=dateOrNone(o.get("date", None)))

    def sameClub(self) -> bool:
        return self.home.club == self.away.club

    def __str__(self) -> str:
        dateStr = str(self.date) if self.date else "????-??-??"
        return f"{dateStr} {self.name}"

    @property
    def venue(self) -> Venue:
        return self.home.club.venue

    @property
    def weekday(self) -> Weekday:
        return self.home.club.weekday

    @cached_property
    def name(self) -> str:
        return self.home.name + " x " + self.away.name

    @cached_property
    def sanitized_name(self) -> str:
        return sanitize(self.name)

    @cached_property
    def teams(self) -> frozenset[Team]:
        return frozenset([self.home, self.away])

def byDate(fixtures: Iterable[Fixture]) -> list[Fixture]:
    """Sort fixtures by their date."""
    return sorted(fixtures, key=lambda f: (f.date or date(2000, 1, 1), f.name))

class Division:
    """A division in the chess league."""
    @match_typing
    def __init__(self, name: str, teams: list[Team], fixtures: Union[list[Fixture], None] = None):
        self.name = name
        self.teams = teams
        self.fixtures = fixtures if fixtures is not None else [Fixture(home, away) for home in teams for away in teams if home != away]

    def __str__(self) -> str:
        r = f'= {self.name} =\nTeams:\n'
        for ts in sorted(map(str, self.teams)):
            r += '    ' + ts + '\n'

        r += '\nFixtures:\n'
        for f in byDate(self.fixtures):
            r += '    ' + str(f) + '\n'

        return r

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "teams": [t.name for t in self.teams],
            "fixtures": [f.to_json() for f in self.fixtures],
            }

    @classmethod
    def from_json(cls: type[Self], teams: dict[str, Team], o: dict[str, Any]) -> Self:
        return cls(name=o["name"], teams=[teams[t] for t in o["teams"]], fixtures=[Fixture.from_json(teams, o) for o in o["fixtures"]])

    @cached_property
    def fixturePairs(self) -> frozenset[frozenset[Fixture]]:
        """All fixtures in the division, paired so that T1 v T2 and T2 v T1 are together.
        All inner sets have two Fixtures in them."""
        toAdd = self.fixtures.copy()
        ret: set[frozenset[Fixture]] = set()
        while toAdd:
            f1 = toAdd.pop()
            f2 = next(f for f in toAdd if f.teams == f1.teams)
            toAdd.remove(f2)
            ret.add(frozenset({f1, f2}))
        return frozenset(ret)

class League:
    """A chess league."""
    @match_typing
    def __init__(self, name: str, start: date, end: date, divisions: list[Division], calendar: Calendar = Calendar.empty()):
        assert(end > start)
        self.name = name
        self.start = start
        self.end = end
        self.divisions = divisions
        self.calendar = calendar

    def __str__(self) -> str:
        r = f'=== {self.name} (from {self.start} until {self.end}) ===\n'
        for d in self.divisions:
            r += '\n' + str(d)
        return r

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "start": str(self.start),
            "end": str(self.end),
            "venues": [v.to_json() for v in self.venues],
            "clubs": [c.to_json() for c in self.clubs],
            "divisions": [d.to_json() for d in self.divisions],
            "calendar": self.calendar.to_json(),
            }

    @classmethod
    def from_json(cls: type[Self], o: dict[str, Any]) -> Self:
        venues = {v.name: v for v in map(Venue.from_json, o["venues"])}
        clubs = {c.name: c for c in map(partial(Club.from_json, venues), o["clubs"])}
        teams = {t.name: t for c in clubs.values() for t in c.teams}
        divisions = [Division.from_json(teams, o) for o in o["divisions"]]
        calendar = Calendar.from_json(o["calendar"])
        return cls(name=o["name"], start=date.fromisoformat(o["start"]), end=date.fromisoformat(o["end"]), divisions=divisions, calendar=calendar)

    @cached_property
    def venues(self) -> frozenset[Venue]:
        return frozenset(c.venue for c in self.clubs)

    @cached_property
    def venuesWeekdays(self) -> frozenset[tuple[Venue, Weekday]]:
        return frozenset((c.venue, c.weekday) for c in self.clubs)

    @cached_property
    def clubs(self) -> frozenset[Club]:
        return frozenset(t.club for d in self.divisions for t in d.teams)

    @property
    def teams(self) -> Iterable[Team]:
        for d in self.divisions:
            for t in d.teams:
                yield t

    @property
    def fixtures(self) -> Iterable[Fixture]:
        for d in self.divisions:
            for f in d.fixtures:
                yield f

    @property
    def fixturePairs(self) -> Iterable[frozenset[Fixture]]:
        for d in self.divisions:
            for p in d.fixturePairs:
                yield p

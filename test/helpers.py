# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from __future__ import annotations

from collections.abc import Sequence
from datetime import date

import pytest

from constraints import CheckResult
from league import Calendar, Club, Division, Fixture, League, OnlyWhen, Team, Venue, Weekday
from solver_base import UnsatisfiableConstraints
from solver_pycsp3 import Constraint, Solver

SEASON_START = date(2025, 9, 1)
SEASON_END = date(2026, 5, 15)


def mk_venue(name: str, max_matches_per_day: int = 2, minimize_empty_days: bool = False, holidays: list[date] | None = None) -> Venue:
    return Venue(
        name=name,
        maxMatchesPerDay=max_matches_per_day,
        minimizeEmptyDays=minimize_empty_days,
        calendar=Calendar(holidays or []),
    )


def mk_club(
    name: str,
    venue: Venue,
    weekday: Weekday = Weekday.MONDAY,
    *,
    late_start: date | None = None,
    holidays: list[date] | None = None,
    relaxed: bool = False,
) -> Club:
    return Club(
        name=name,
        venue=venue,
        weekday=weekday,
        lateStart=late_start,
        calendar=Calendar(holidays or []),
        relaxed=relaxed,
    )


def mk_team(club: Club, name: str) -> Team:
    return Team(club=club, name=name)


def mk_fixture(home: Team, away: Team, when: date | None = None) -> Fixture:
    return Fixture(home=home, away=away, date=when)


def mk_league(
    *,
    teams: list[Team],
    fixtures: list[Fixture],
    start: date = SEASON_START,
    end: date = SEASON_END,
    only_when: list[OnlyWhen] | None = None,
    league_holidays: list[date] | None = None,
    division_name: str = "D1",
) -> League:
    division = Division(name=division_name, teams=teams, fixtures=fixtures)
    return League(
        name="Test League",
        start=start,
        end=end,
        divisions=[division],
        onlyWhen=only_when or [],
        calendar=Calendar(league_holidays or []),
    )

def assert_sat(league: League, constraints: Sequence[Constraint]) -> None:
    solver = Solver(league=league, constraints=constraints, solver="ACE", solverOptions="")
    solver.solve()


def assert_unsat(league: League, constraints: Sequence[Constraint]) -> None:
    with pytest.raises((UnsatisfiableConstraints, SystemExit, AssertionError)):
        solver = Solver(league=league, constraints=constraints, solver="ACE", solverOptions="")
        solver.solve()


def assert_all_fixtures_assigned(league: League) -> None:
    for fixture in league.fixtures:
        assert fixture.date is not None, f"Fixture {fixture.name} was not assigned a date"


def assert_check_score(
    constraint: Constraint,
    league: League,
    *,
    expected: float | None = None,
    min_score: float | None = None,
    max_score: float | None = None,
) -> CheckResult:
    result = constraint.check(league)
    if expected is not None:
        assert result.score == expected
    if min_score is not None:
        assert result.score >= min_score
    if max_score is not None:
        assert result.score <= max_score
    if result.score == 1.0:
        assert result.reasons == []
    else:
        assert len(result.reasons) > 0
    return result

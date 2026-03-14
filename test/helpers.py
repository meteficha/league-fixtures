# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any

import pytest
import pycsp3.functions as pycsp3f

from league import Calendar, Club, Division, Fixture, League, OnlyWhen, Team, Venue, Weekday
from solver_base import UnsatisfiableConstraints
from solver_pycsp3 import Constraint, ConstraintContext, Solver

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


def mk_fixture(home: Team, away: Team, when: date) -> Fixture:
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


class _ObjectiveGuardConstraint(Constraint):
    def apply(self, ctx: ConstraintContext) -> None:
        any_var = next(iter(ctx.vars.values()), None)
        if any_var is not None:
            pycsp3f.satisfy(any_var >= 0)  # type: ignore[operator]

    def objective_term(self, ctx: ConstraintContext) -> Any:
        return pycsp3f.Sum(ctx.vars[f] for f in ctx.solver.league.fixtures)


def _with_objective_guard(constraints: Sequence[Constraint]) -> list[Constraint]:
    return [*constraints, _ObjectiveGuardConstraint()]


def assert_sat(league: League, constraints: Sequence[Constraint]) -> None:
    solver = Solver(league=league, constraints=_with_objective_guard(constraints), solver="ACE", solverOptions="")
    solver.solve()


def assert_unsat(league: League, constraints: Sequence[Constraint]) -> None:
    with pytest.raises((UnsatisfiableConstraints, SystemExit, AssertionError)):
        solver = Solver(league=league, constraints=_with_objective_guard(constraints), solver="ACE", solverOptions="")
        solver.solve()

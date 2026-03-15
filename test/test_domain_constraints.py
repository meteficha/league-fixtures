from __future__ import annotations

from datetime import date

from constraints import (
    ClubHolidayDomainConstraint,
    ClubLateStartDomainConstraint,
    FixedDateDomainConstraint,
    FixtureWeekdayDomainConstraint,
    LeagueHolidayDomainConstraint,
    SameClubDeadlineDomainConstraint,
    SingleFixtureDomainConstraint,
    TeamHolidayDomainConstraint,
    VenueHolidayDomainConstraint,
)
from solver_pycsp3 import ConstraintContext, Solver

from .helpers import mk_club, mk_fixture, mk_league, mk_team, mk_venue

SEASON_START = date(2026, 1, 5)
SEASON_END = date(2026, 2, 10)

MONDAY_1 = date(2026, 1, 5)
MONDAY_2 = date(2026, 1, 12)
MONDAY_3 = date(2026, 1, 19)
MONDAY_4 = date(2026, 1, 26)
MONDAY_5 = date(2026, 2, 2)


def _league_for_fixture(
    *,
    league_holidays: list[date] | None = None,
    venue_holidays: list[date] | None = None,
    home_club_holidays: list[date] | None = None,
    away_club_holidays: list[date] | None = None,
    home_team_holidays: list[date] | None = None,
    away_team_holidays: list[date] | None = None,
    home_late_start: date | None = None,
    away_late_start: date | None = None,
    fixed_date: date | None = None,
) -> tuple[Solver, ConstraintContext, object]:
    v1 = mk_venue("V1", holidays=venue_holidays)
    v2 = mk_venue("V2")
    c1 = mk_club("C1", v1, late_start=home_late_start, holidays=home_club_holidays)
    c2 = mk_club("C2", v2, late_start=away_late_start, holidays=away_club_holidays)
    t1 = mk_team(c1, "C1_1")
    t2 = mk_team(c2, "C2_1")
    t1.calendar = t1.calendar.__class__(home_team_holidays or [])
    t2.calendar = t2.calendar.__class__(away_team_holidays or [])

    fixture = mk_fixture(t1, t2, fixed_date)
    league = mk_league(teams=[t1, t2], fixtures=[fixture], start=SEASON_START, end=SEASON_END, league_holidays=league_holidays)
    solver = Solver(league=league, constraints=[], solver="ACE", solverOptions="")
    return solver, ConstraintContext(solver=solver), fixture


def _league_for_same_club_fixture(
    *,
    league_holidays: list[date] | None = None,
    venue_holidays: list[date] | None = None,
    club_holidays: list[date] | None = None,
    home_team_holidays: list[date] | None = None,
    away_team_holidays: list[date] | None = None,
    late_start: date | None = None,
    fixed_date: date | None = None,
) -> tuple[Solver, ConstraintContext, object]:
    v1 = mk_venue("V1", holidays=venue_holidays)
    c1 = mk_club("C1", v1, late_start=late_start, holidays=club_holidays)
    t1 = mk_team(c1, "C1_1")
    t2 = mk_team(c1, "C1_2")
    t1.calendar = t1.calendar.__class__(home_team_holidays or [])
    t2.calendar = t2.calendar.__class__(away_team_holidays or [])

    fixture = mk_fixture(t1, t2, fixed_date)
    league = mk_league(teams=[t1, t2], fixtures=[fixture], start=SEASON_START, end=SEASON_END, league_holidays=league_holidays)
    solver = Solver(league=league, constraints=[], solver="ACE", solverOptions="")
    return solver, ConstraintContext(solver=solver), fixture


def _apply_rule(rule: object, ctx: ConstraintContext, fixture: object, *, full_season: bool = False) -> set[date]:
    if full_season:
        domain = set(range(ctx.solver.dateToInt(ctx.solver.league.end)))
    else:
        domain = set(ctx.solver.possibleDays(fixture.weekday))
    filtered = rule.apply_to_fixture_domain(ctx, fixture, domain)
    return {ctx.solver.intToDate(day) for day in filtered}


def test_fixture_weekday_domain_constraint() -> None:
    solver, ctx, fixture = _league_for_fixture()

    actual = _apply_rule(FixtureWeekdayDomainConstraint(), ctx, fixture, full_season=True)

    assert actual == {MONDAY_1, MONDAY_2, MONDAY_3, MONDAY_4, MONDAY_5}


def test_club_late_start_domain_constraint() -> None:
    solver, ctx, fixture = _league_for_fixture(home_late_start=MONDAY_3)
    del solver

    actual = _apply_rule(ClubLateStartDomainConstraint(), ctx, fixture)

    assert actual == {MONDAY_3, MONDAY_4, MONDAY_5}


def test_league_holiday_domain_constraint() -> None:
    solver, ctx, fixture = _league_for_fixture(league_holidays=[MONDAY_2])
    del solver

    actual = _apply_rule(LeagueHolidayDomainConstraint(), ctx, fixture)

    assert actual == {MONDAY_1, MONDAY_3, MONDAY_4, MONDAY_5}


def test_venue_holiday_domain_constraint() -> None:
    solver, ctx, fixture = _league_for_fixture(venue_holidays=[MONDAY_3])
    del solver

    actual = _apply_rule(VenueHolidayDomainConstraint(), ctx, fixture)

    assert actual == {MONDAY_1, MONDAY_2, MONDAY_4, MONDAY_5}


def test_club_holiday_domain_constraint() -> None:
    solver, ctx, fixture = _league_for_fixture(home_club_holidays=[MONDAY_2], away_club_holidays=[MONDAY_4])
    del solver

    actual = _apply_rule(ClubHolidayDomainConstraint(), ctx, fixture)

    assert actual == {MONDAY_1, MONDAY_3, MONDAY_5}


def test_team_holiday_domain_constraint() -> None:
    solver, ctx, fixture = _league_for_fixture(home_team_holidays=[MONDAY_2], away_team_holidays=[MONDAY_5])
    del solver

    actual = _apply_rule(TeamHolidayDomainConstraint(), ctx, fixture)

    assert actual == {MONDAY_1, MONDAY_3, MONDAY_4}


def test_same_club_deadline_domain_constraint() -> None:
    solver, ctx, fixture = _league_for_same_club_fixture()
    del solver

    actual = _apply_rule(SameClubDeadlineDomainConstraint(), ctx, fixture)

    assert actual == {MONDAY_1, MONDAY_2, MONDAY_3, MONDAY_4}


def test_fixed_date_domain_constraint() -> None:
    solver, ctx, fixture = _league_for_fixture(fixed_date=MONDAY_3)
    del solver

    actual = _apply_rule(FixedDateDomainConstraint(), ctx, fixture)

    assert actual == {MONDAY_3}


def test_single_fixture_domain_constraint_uses_all_domain_constraints() -> None:
    solver, ctx, fixture = _league_for_same_club_fixture(
        league_holidays=[MONDAY_3],
        venue_holidays=[MONDAY_4],
        club_holidays=[MONDAY_1],
        away_team_holidays=[MONDAY_5],
        late_start=MONDAY_2,
        fixed_date=MONDAY_2,
    )
    del solver

    actual = SingleFixtureDomainConstraint().fixture_domain(ctx, fixture)
    actual_dates = {ctx.solver.intToDate(day) for day in actual}

    assert actual_dates == {MONDAY_2}

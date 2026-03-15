from __future__ import annotations

from datetime import date

from constraints import SingleFixtureDomainConstraint, VenueDailyCapacityConstraint

from .helpers import assert_all_fixtures_assigned, assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def _league_for_capacity(d1: date, d2: date):
    shared = mk_venue("Shared", max_matches_per_day=1)
    vx = mk_venue("VX")
    vy = mk_venue("VY")

    ca = mk_club("A", shared)
    cb = mk_club("B", shared)
    cx = mk_club("X", vx)
    cy = mk_club("Y", vy)

    ta = mk_team(ca, "A1")
    tb = mk_team(cb, "B1")
    tx = mk_team(cx, "X1")
    ty = mk_team(cy, "Y1")

    f1 = mk_fixture(ta, tx, d1)
    f2 = mk_fixture(tb, ty, d2)
    f3 = mk_fixture(tx, ty, date(2025, 10, 6))
    f4 = mk_fixture(ty, ta, date(2025, 10, 13))
    return mk_league(teams=[ta, tb, tx, ty], fixtures=[f1, f2, f3, f4])


def test_venue_daily_capacity_sat() -> None:
    league = _league_for_capacity(date(2025, 9, 1), date(2025, 9, 8))
    constraints = [SingleFixtureDomainConstraint(), VenueDailyCapacityConstraint()]
    assert_sat(league, constraints)


def test_venue_daily_capacity_unsat() -> None:
    league = _league_for_capacity(date(2025, 9, 1), date(2025, 9, 1))
    constraints = [SingleFixtureDomainConstraint(), VenueDailyCapacityConstraint()]
    assert_unsat(league, constraints)


def test_venue_daily_capacity_solver_dates_sat() -> None:
    """Two shared-venue fixtures with no fixed dates can be split across Mondays to satisfy capacity."""
    shared = mk_venue("Shared", max_matches_per_day=1)
    vc = mk_venue("VC")

    ca = mk_club("A", shared)
    cb = mk_club("B", shared)
    cc = mk_club("C", vc)

    ta = mk_team(ca, "A1")
    tb = mk_team(cb, "B1")
    tc = mk_team(cc, "C1")

    f1 = mk_fixture(ta, tc)
    f2 = mk_fixture(tb, tc)
    f3 = mk_fixture(tc, ta)
    league = mk_league(
        teams=[ta, tb, tc],
        fixtures=[f1, f2, f3],
        start=date(2025, 9, 1),
        end=date(2025, 9, 29),
    )

    constraints = [SingleFixtureDomainConstraint(), VenueDailyCapacityConstraint()]
    assert_sat(league, constraints)
    assert_all_fixtures_assigned(league)
    assert f1.date != f2.date


def test_venue_daily_capacity_solver_dates_unsat() -> None:
    """Three shared-venue fixtures cannot fit into two Mondays when venue capacity is one match per day."""
    shared = mk_venue("Shared", max_matches_per_day=1)
    vc = mk_venue("VC")

    ca = mk_club("A", shared)
    cb = mk_club("B", shared)
    cd = mk_club("D", shared)
    cc = mk_club("C", vc)

    ta = mk_team(ca, "A1")
    tb = mk_team(cb, "B1")
    td = mk_team(cd, "D1")
    tc = mk_team(cc, "C1")

    league = mk_league(
        teams=[ta, tb, td, tc],
        fixtures=[mk_fixture(ta, tc), mk_fixture(tb, tc), mk_fixture(td, tc), mk_fixture(tc, ta)],
        start=date(2025, 9, 1),
        end=date(2025, 9, 15),
    )

    constraints = [SingleFixtureDomainConstraint(), VenueDailyCapacityConstraint()]
    assert_unsat(league, constraints)

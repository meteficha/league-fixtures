from __future__ import annotations

from datetime import date

from constraints import (
    SingleFixtureDomainConstraint,
    TeamNoOverlapAndSpacingConstraint,
    VenueMinimizeEmptyDaysObjectiveConstraint,
)

from .helpers import assert_all_fixtures_assigned, assert_check_score, assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def _sat_league():
    va = mk_venue("VA", minimize_empty_days=True)
    vb = mk_venue("VB")
    vc = mk_venue("VC")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)
    a1 = mk_team(ca, "A1")
    b1 = mk_team(cb, "B1")
    c1 = mk_team(cc, "C1")

    f1 = mk_fixture(a1, b1, date(2025, 9, 1))
    f2 = mk_fixture(a1, c1, date(2025, 9, 8))
    f3 = mk_fixture(b1, c1, date(2025, 10, 6))
    f4 = mk_fixture(c1, b1, date(2025, 10, 13))
    return mk_league(teams=[a1, b1, c1], fixtures=[f1, f2, f3, f4])


def _unsat_league():
    va = mk_venue("VA", minimize_empty_days=True)
    vb = mk_venue("VB")
    vc = mk_venue("VC")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)
    a1 = mk_team(ca, "A1")
    b1 = mk_team(cb, "B1")
    c1 = mk_team(cc, "C1")

    f1 = mk_fixture(a1, b1, date(2025, 9, 1))
    f2 = mk_fixture(c1, a1, date(2025, 9, 1))
    f3 = mk_fixture(b1, c1, date(2025, 10, 6))
    return mk_league(teams=[a1, b1, c1], fixtures=[f1, f2, f3])


def test_venue_minimize_empty_days_objective_sat() -> None:
    constraints = [SingleFixtureDomainConstraint(), VenueMinimizeEmptyDaysObjectiveConstraint()]
    league = _sat_league()
    assert_sat(league, constraints)
    assert_check_score(constraints[1], league, min_score=0.0, max_score=1.0)


def test_venue_minimize_empty_days_objective_unsat_with_hard_constraint() -> None:
    constraints = [
        SingleFixtureDomainConstraint(),
        TeamNoOverlapAndSpacingConstraint(strictMatchSpaceOut=5),
        VenueMinimizeEmptyDaysObjectiveConstraint(),
    ]
    assert_unsat(_unsat_league(), constraints)


def test_venue_minimize_empty_days_objective_solver_dates_sat() -> None:
    """With unassigned dates, minimize-empty-days objective can cluster a venue's home matches."""
    va = mk_venue("VA", minimize_empty_days=True)
    vb = mk_venue("VB", minimize_empty_days=True)
    vc = mk_venue("VC", minimize_empty_days=True)
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)
    a1 = mk_team(ca, "A1")
    b1 = mk_team(cb, "B1")
    c1 = mk_team(cc, "C1")

    f1 = mk_fixture(a1, b1)
    f2 = mk_fixture(a1, c1)
    league = mk_league(
        teams=[a1, b1, c1],
        fixtures=[
            f1,
            f2,
            mk_fixture(b1, a1),
            mk_fixture(b1, c1),
            mk_fixture(c1, a1),
            mk_fixture(c1, b1),
        ],
    )

    constraints = [SingleFixtureDomainConstraint(), VenueMinimizeEmptyDaysObjectiveConstraint()]
    assert_sat(league, constraints)
    assert_all_fixtures_assigned(league)
    assert f1.date is not None
    assert f2.date is not None
    assert f1.date == f2.date
    assert_check_score(constraints[1], league, min_score=0.0, max_score=1.0)


def test_venue_minimize_empty_days_objective_solver_dates_unsat_with_hard_constraint() -> None:
    """Hard spacing infeasibility remains unsat even when an objective prefers clustering."""
    va = mk_venue("VA", minimize_empty_days=True)
    vb = mk_venue("VB")
    vc = mk_venue("VC")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)
    a1 = mk_team(ca, "A1")
    b1 = mk_team(cb, "B1")
    c1 = mk_team(cc, "C1")

    league = mk_league(
        teams=[a1, b1, c1],
        fixtures=[mk_fixture(a1, b1), mk_fixture(c1, a1), mk_fixture(b1, c1)],
        start=date(2025, 9, 1),
        end=date(2025, 9, 15),
    )

    constraints = [
        SingleFixtureDomainConstraint(),
        TeamNoOverlapAndSpacingConstraint(strictMatchSpaceOut=5),
        VenueMinimizeEmptyDaysObjectiveConstraint(),
    ]
    assert_unsat(league, constraints)


def test_venue_minimize_empty_days_objective_check_partial_score() -> None:
    """A minimize-empty-days venue using more than one date yields a partial compactness score."""
    league = _sat_league()
    result = VenueMinimizeEmptyDaysObjectiveConstraint().check(league)
    assert 0.0 < result.score < 1.0

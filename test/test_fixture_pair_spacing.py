from __future__ import annotations

from datetime import date

from constraints import FixturePairSpacingConstraint, SingleFixtureDomainConstraint

from .helpers import assert_all_fixtures_assigned, assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def _league_for_pair_spacing(d1: date, d2: date):
    va = mk_venue("VA")
    vb = mk_venue("VB")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    a1 = mk_team(ca, "A1")
    b1 = mk_team(cb, "B1")

    f1 = mk_fixture(a1, b1, d1)
    f2 = mk_fixture(b1, a1, d2)
    return mk_league(teams=[a1, b1], fixtures=[f1, f2])


def test_fixture_pair_spacing_sat() -> None:
    league = _league_for_pair_spacing(date(2025, 9, 1), date(2025, 9, 22))
    constraints = [SingleFixtureDomainConstraint(), FixturePairSpacingConstraint(strictFixturePairSpacing=2)]
    assert_sat(league, constraints)


def test_fixture_pair_spacing_unsat() -> None:
    league = _league_for_pair_spacing(date(2025, 9, 1), date(2025, 9, 8))
    constraints = [SingleFixtureDomainConstraint(), FixturePairSpacingConstraint(strictFixturePairSpacing=2)]
    assert_unsat(league, constraints)


def test_fixture_pair_spacing_solver_dates_sat() -> None:
    """Two-leg fixtures with no preset dates can still be spaced by at least 2 weeks."""
    va = mk_venue("VA")
    vb = mk_venue("VB")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    a1 = mk_team(ca, "A1")
    b1 = mk_team(cb, "B1")

    f1 = mk_fixture(a1, b1)
    f2 = mk_fixture(b1, a1)
    league = mk_league(
        teams=[a1, b1],
        fixtures=[f1, f2],
        start=date(2025, 9, 1),
        end=date(2025, 10, 13),
    )

    constraints = [SingleFixtureDomainConstraint(), FixturePairSpacingConstraint(strictFixturePairSpacing=2)]
    assert_sat(league, constraints)
    assert_all_fixtures_assigned(league)
    assert f1.date is not None
    assert f2.date is not None
    assert abs((f1.date - f2.date).days) >= 14


def test_fixture_pair_spacing_solver_dates_unsat() -> None:
    """If the season only has two Mondays 7 days apart, a 2-week spacing requirement is impossible."""
    va = mk_venue("VA")
    vb = mk_venue("VB")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    a1 = mk_team(ca, "A1")
    b1 = mk_team(cb, "B1")

    league = mk_league(
        teams=[a1, b1],
        fixtures=[mk_fixture(a1, b1), mk_fixture(b1, a1)],
        start=date(2025, 9, 1),
        end=date(2025, 9, 15),
    )

    constraints = [SingleFixtureDomainConstraint(), FixturePairSpacingConstraint(strictFixturePairSpacing=2)]
    assert_unsat(league, constraints)

from __future__ import annotations

from datetime import date

from constraints import SingleFixtureDomainConstraint, TeamNoOverlapAndSpacingConstraint

from .helpers import assert_all_fixtures_assigned, assert_check_score, assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def _league_for_spacing(d1: date, d2: date):
    va = mk_venue("VA")
    vb = mk_venue("VB")
    vc = mk_venue("VC")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)
    ta = mk_team(ca, "A1")
    tb = mk_team(cb, "B1")
    tc = mk_team(cc, "C1")

    f1 = mk_fixture(ta, tb, d1)
    f2 = mk_fixture(tc, ta, d2)
    f3 = mk_fixture(tb, tc, date(2025, 10, 6))
    return mk_league(teams=[ta, tb, tc], fixtures=[f1, f2, f3])


def test_team_no_overlap_spacing_sat() -> None:
    league = _league_for_spacing(date(2025, 9, 1), date(2025, 9, 8))
    constraints = [SingleFixtureDomainConstraint(), TeamNoOverlapAndSpacingConstraint(strictMatchSpaceOut=5)]
    assert_sat(league, constraints)
    assert_check_score(constraints[1], league, expected=1.0)


def test_team_no_overlap_spacing_unsat() -> None:
    league = _league_for_spacing(date(2025, 9, 1), date(2025, 9, 1))
    constraints = [SingleFixtureDomainConstraint(), TeamNoOverlapAndSpacingConstraint(strictMatchSpaceOut=5)]
    assert_unsat(league, constraints)


def test_team_no_overlap_spacing_solver_dates_sat() -> None:
    """With several Mondays available, the solver can keep each team's fixtures at least 5 days apart."""
    va = mk_venue("VA")
    vb = mk_venue("VB")
    vc = mk_venue("VC")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)
    ta = mk_team(ca, "A1")
    tb = mk_team(cb, "B1")
    tc = mk_team(cc, "C1")

    f1 = mk_fixture(ta, tb)
    f2 = mk_fixture(tc, ta)
    f3 = mk_fixture(tb, tc)
    league = mk_league(
        teams=[ta, tb, tc],
        fixtures=[f1, f2, f3],
        start=date(2025, 9, 1),
        end=date(2025, 9, 29),
    )

    constraints = [SingleFixtureDomainConstraint(), TeamNoOverlapAndSpacingConstraint(strictMatchSpaceOut=5)]
    assert_sat(league, constraints)
    assert_all_fixtures_assigned(league)
    assert_check_score(constraints[1], league, expected=1.0)


def test_team_no_overlap_spacing_solver_dates_unsat() -> None:
    """If only two Mondays exist, requiring 8 days spacing makes a two-fixture team unschedulable."""
    va = mk_venue("VA")
    vb = mk_venue("VB")
    vc = mk_venue("VC")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)
    ta = mk_team(ca, "A1")
    tb = mk_team(cb, "B1")
    tc = mk_team(cc, "C1")

    league = mk_league(
        teams=[ta, tb, tc],
        fixtures=[mk_fixture(ta, tb), mk_fixture(tc, ta), mk_fixture(tb, tc)],
        start=date(2025, 9, 1),
        end=date(2025, 9, 15),
    )

    constraints = [SingleFixtureDomainConstraint(), TeamNoOverlapAndSpacingConstraint(strictMatchSpaceOut=8)]
    assert_unsat(league, constraints)


def test_team_no_overlap_spacing_check_partial_score() -> None:
    """One adjacent gap satisfies spacing and one does not, so score is partial."""
    va = mk_venue("VA")
    vb = mk_venue("VB")
    vc = mk_venue("VC")
    vd = mk_venue("VD")
    ca = mk_club("A", va)
    cb = mk_club("B", vb)
    cc = mk_club("C", vc)
    cd = mk_club("D", vd)
    ta = mk_team(ca, "A1")
    tb = mk_team(cb, "B1")
    tc = mk_team(cc, "C1")
    td = mk_team(cd, "D1")

    league = mk_league(
        teams=[ta, tb, tc, td],
        fixtures=[
            mk_fixture(ta, tb, date(2025, 9, 1)),
            mk_fixture(tc, ta, date(2025, 9, 8)),
            mk_fixture(td, ta, date(2025, 9, 10)),
        ],
    )

    result = TeamNoOverlapAndSpacingConstraint(strictMatchSpaceOut=5).check(league)
    assert 0.0 < result.score < 1.0

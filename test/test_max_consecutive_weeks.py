from __future__ import annotations

from datetime import date

from constraints import MaxConsecutiveWeeksConstraint, SingleFixtureDomainConstraint

from .helpers import assert_all_fixtures_assigned, assert_check_score, assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def _league_for_consecutive_weeks(dates: tuple[date, date, date]):
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

    f1 = mk_fixture(ta, tb, dates[0])
    f2 = mk_fixture(tc, ta, dates[1])
    f3 = mk_fixture(ta, td, dates[2])
    f4 = mk_fixture(tb, tc, date(2025, 10, 6))
    f5 = mk_fixture(td, tb, date(2025, 10, 13))
    return mk_league(teams=[ta, tb, tc, td], fixtures=[f1, f2, f3, f4, f5])


def test_max_consecutive_weeks_sat() -> None:
    league = _league_for_consecutive_weeks((date(2025, 9, 1), date(2025, 9, 8), date(2025, 9, 22)))
    constraints = [SingleFixtureDomainConstraint(), MaxConsecutiveWeeksConstraint(strictMaxNoWeeksWithMatches=2)]
    assert_sat(league, constraints)
    assert_check_score(constraints[1], league, expected=1.0)


def test_max_consecutive_weeks_unsat() -> None:
    league = _league_for_consecutive_weeks((date(2025, 9, 1), date(2025, 9, 8), date(2025, 9, 15)))
    constraints = [SingleFixtureDomainConstraint(), MaxConsecutiveWeeksConstraint(strictMaxNoWeeksWithMatches=2)]
    assert_unsat(league, constraints)


def test_max_consecutive_weeks_solver_dates_sat() -> None:
    """With enough Mondays, the solver can insert a break week and avoid 3 consecutive weeks for a team."""
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

    fixtures = [
        mk_fixture(ta, tb),
        mk_fixture(tc, ta),
        mk_fixture(ta, td),
        mk_fixture(tb, tc),
        mk_fixture(td, tb),
    ]
    league = mk_league(
        teams=[ta, tb, tc, td],
        fixtures=fixtures,
        start=date(2025, 9, 1),
        end=date(2025, 10, 20),
    )

    constraints = [SingleFixtureDomainConstraint(), MaxConsecutiveWeeksConstraint(strictMaxNoWeeksWithMatches=2)]
    assert_sat(league, constraints)
    assert_all_fixtures_assigned(league)
    assert_check_score(constraints[1], league, expected=1.0)


def test_max_consecutive_weeks_solver_dates_unsat() -> None:
    """When 3 fixtures must be placed within a 3-Monday horizon, one team exceeds max consecutive weeks."""
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
            mk_fixture(ta, tb),
            mk_fixture(tc, ta),
            mk_fixture(ta, td),
            mk_fixture(tb, tc),
            mk_fixture(td, tb),
        ],
        start=date(2025, 9, 1),
        end=date(2025, 9, 22),
    )

    constraints = [SingleFixtureDomainConstraint(), MaxConsecutiveWeeksConstraint(strictMaxNoWeeksWithMatches=2)]
    assert_unsat(league, constraints)


def test_max_consecutive_weeks_check_partial_score() -> None:
    """Some sliding windows satisfy max-consecutive-weeks and some violate it."""
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
            mk_fixture(ta, td, date(2025, 9, 15)),
            mk_fixture(tb, ta, date(2025, 10, 6)),
        ],
    )

    result = MaxConsecutiveWeeksConstraint(strictMaxNoWeeksWithMatches=2).check(league)
    assert 0.0 < result.score < 1.0

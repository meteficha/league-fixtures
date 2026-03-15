from __future__ import annotations

from datetime import date

from constraints import FirstMatchSameClubConstraint, SingleFixtureDomainConstraint

from .helpers import assert_all_fixtures_assigned, assert_sat, assert_unsat, mk_club, mk_fixture, mk_league, mk_team, mk_venue


def _league_for_first_match(same_club_date: date, other_date: date):
    v_main = mk_venue("Main")
    v_other = mk_venue("Other")

    c = mk_club("C", v_main)
    o = mk_club("O", v_other)

    c1 = mk_team(c, "C1")
    c2 = mk_team(c, "C2")
    o1 = mk_team(o, "O1")

    f_same = mk_fixture(c1, c2, same_club_date)
    f_other = mk_fixture(c1, o1, other_date)
    f_balanced = mk_fixture(o1, c1, date(2025, 10, 6))
    f_c2_home = mk_fixture(c2, o1, date(2025, 10, 13))
    return mk_league(teams=[c1, c2, o1], fixtures=[f_same, f_other, f_balanced, f_c2_home])


def test_first_match_same_club_sat() -> None:
    league = _league_for_first_match(date(2025, 9, 1), date(2025, 9, 8))
    constraints = [SingleFixtureDomainConstraint(), FirstMatchSameClubConstraint()]
    assert_sat(league, constraints)


def test_first_match_same_club_unsat() -> None:
    league = _league_for_first_match(date(2025, 9, 8), date(2025, 9, 1))
    constraints = [SingleFixtureDomainConstraint(), FirstMatchSameClubConstraint()]
    assert_unsat(league, constraints)


def test_first_match_same_club_solver_dates_sat() -> None:
    """The solver can assign the intra-club fixture as the earliest fixture for both teams."""
    v_main = mk_venue("Main")
    v_other = mk_venue("Other")

    c = mk_club("C", v_main)
    o = mk_club("O", v_other)

    c1 = mk_team(c, "C1")
    c2 = mk_team(c, "C2")
    o1 = mk_team(o, "O1")

    f_same = mk_fixture(c1, c2)
    f_other = mk_fixture(c1, o1)
    f_balanced = mk_fixture(o1, c1)
    f_c2_home = mk_fixture(c2, o1)
    league = mk_league(teams=[c1, c2, o1], fixtures=[f_same, f_other, f_balanced, f_c2_home])

    constraints = [SingleFixtureDomainConstraint(), FirstMatchSameClubConstraint()]
    assert_sat(league, constraints)
    assert_all_fixtures_assigned(league)
    assert f_same.date is not None
    assert f_other.date is not None
    assert f_balanced.date is not None
    assert f_c2_home.date is not None
    assert f_same.date < f_other.date
    assert f_same.date < f_balanced.date
    assert f_same.date < f_c2_home.date


def test_first_match_same_club_solver_dates_unsat() -> None:
    """A fixed early away match plus a late-start home club forces the intra-club first match to be too late."""
    v_main = mk_venue("Main")
    v_other = mk_venue("Other")

    c = mk_club("C", v_main, late_start=date(2025, 9, 8))
    o = mk_club("O", v_other)

    c1 = mk_team(c, "C1")
    c2 = mk_team(c, "C2")
    o1 = mk_team(o, "O1")

    f_same = mk_fixture(c1, c2)
    f_other = mk_fixture(c1, o1)
    f_balanced = mk_fixture(o1, c1, date(2025, 9, 1))
    f_c2_home = mk_fixture(c2, o1)
    league = mk_league(
        teams=[c1, c2, o1],
        fixtures=[f_same, f_other, f_balanced, f_c2_home],
        start=date(2025, 9, 1),
        end=date(2025, 10, 13),
    )

    constraints = [SingleFixtureDomainConstraint(), FirstMatchSameClubConstraint()]
    assert_unsat(league, constraints)

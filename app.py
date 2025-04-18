# Generate league fixtures for the Nottingham Chess League.
#
# Constraints:
#
#   - League rules constraints: <https://www.nottinghamshirechess.org/league-rules/>
#
#       - (B1) League runs from 1 Sep to 15 May
#
#       - (B4) If two or more teams from the same club play in the same division,
#         the first match(es) of the club's teams in that division shall be between them(selves).
#         Matches between teams from the same club must be played by 31st January.
#
#   - Venues can only host 2 games per day by default.
#
# Desirable properties:
#
#   - Teams alternate between playing at home and away.

from z3 import z3



s = z3.Solver()
x = z3.Real('x')
s.add(0 == x**2 + 2*x - 1, x != - (1 + z3.Sqrt(2)))
print(s)
print(s.check())
print(s.model())

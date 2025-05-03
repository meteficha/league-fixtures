"""Generate league fixtures for the Nottingham Chess League.

Constraints:

    - League rules constraints: <https://www.nottinghamshirechess.org/league-rules/>

        - (B1) League runs from 1 Sep to 15 May

        - (B4) If two or more teams from the same club play in the same division,
          the first match(es) of the club's teams in that division shall be between them(selves).
          Matches between teams from the same club must be played by 31st January.

    - Venues can only host 2 games per day by default.

Desirable properties:

    - Last fixture should be scheduled at least 5 weeks away from league end.

    - Teams alternate between playing at home and away.
"""

from notts import season202425
import solver_pycsp3 as solver
# import solver_z3 as solver
from report import Report


print("Creating league data...")
league = season202425()
print("Creating solver...")
solver = solver.Solver(league)
print("Solving...")
solver.solve()
# print(league)
print("Generating report...")
Report(league).saveTo("report.html")

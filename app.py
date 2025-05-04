'''Generate league fixtures for the Nottingham Chess League.

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
'''

import click
import json

from league import League
from report import Report


# print('Creating league data...')
# league = season202425()
# print('Creating solver...')
# solver = solver.Solver(league)
# print('Solving...')
# solver.solve()
# # print(league)
# print('Generating report...')
# Report(league).saveTo('report.html')

@click.group()
def cli():
    pass

@cli.command()
@click.option('--example', default='notts_season202425', help='The example league to save')
@click.argument('output')
def save(example: str, output: str) -> None:
    '''Save a hardcoded league example as a JSON file.'''
    league = None
    match example:
        case 'notts_season202425':
            import notts
            league = notts.season202425()
        case _:
            raise Exception("Unknown example " + example)
    print('Saving example league file')
    with open(output, "w") as f:
        json.dump(league.to_json(), f, sort_keys=True, indent=4, separators=(',', ': '))

@cli.command()
@click.option('--output', help='Output to a different file, instead of overwriting input')
@click.argument('input')
def solve(input: str, output: str | None) -> None:
    '''Solve any fixtures without dates from the input file.'''
    output = input if output is None else output

    print('Loading data')
    league = None
    with open(input, "r") as f:
        league = League.from_json(json.load(f))

    print('Creating solver')
    from solver_pycsp3 import Solver
    solver = Solver(league)

    print('Solving')
    solver.solve()

    print('Saving solved league file')
    with open(output, "w") as f:
        json.dump(league.to_json(), f, sort_keys=True, indent=4, separators=(',', ': '))

@cli.command()
@click.option('--output', help='Output to a different file, instead of just adding an .html suffix')
@click.argument('input')
def report(input: str, output: str | None) -> None:
    '''Generate an HTML report from a league file.'''
    output = input + '.html' if output is None else output

    print('Loading data')
    league = None
    with open(input, "r") as f:
        league = League.from_json(json.load(f))

    print('Saving report')
    Report(league).saveTo(output)

if __name__ == '__main__':
    cli()

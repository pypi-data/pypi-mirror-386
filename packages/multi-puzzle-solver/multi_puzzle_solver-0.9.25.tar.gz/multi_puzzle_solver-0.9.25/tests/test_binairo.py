import numpy as np

from puzzle_solver import binairo_solver as solver
from puzzle_solver.core.utils import get_pos


def test_easy():
  # 6x6 easy
  # https://www.puzzle-binairo.com/binairo-6x6-easy/?e=MDoxLDkxMSwwMzg=
  board = np.array([
    ['B', ' ', ' ', ' ', 'B', ' '],
    ['B', 'W', ' ', 'W', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', 'B'],
    [' ', ' ', ' ', ' ', ' ', ' '],
    [' ', 'W', ' ', ' ', 'B', 'B'],
    [' ', ' ', 'B', 'B', ' ', ' ']
  ])
  binst = solver.Board(board=board)
  solutions = binst.solve_and_print()
  assert len(solutions) == 1, f'unique solutions != 1, == {len(solutions)}'
  solution = solutions[0].assignment
  ground = np.array([
    ['B', 'B', ' ', ' ', 'B', ' '],
    ['B', ' ', 'B', ' ', 'B', ' '],
    [' ', 'B', ' ', 'B', ' ', 'B'],
    ['B', 'B', ' ', 'B', ' ', ' '],
    [' ', ' ', 'B', ' ', 'B', 'B'],
    [' ', ' ', 'B', 'B', ' ', 'B'],
  ])
  ground_assignment = {get_pos(x=x, y=y): 1 if ground[y][x] == 'B' else 0 for x in range(ground.shape[1]) for y in range(ground.shape[0])}
  assert set(solution.keys()) == set(ground_assignment.keys()), f'solution keys != ground assignment keys, {set(solution.keys()) ^ set(ground_assignment.keys())} \n\n\n{solution} \n\n\n{ground_assignment}'
  for pos in solution.keys():
    assert solution[pos] == ground_assignment[pos], f'solution[{pos}] != ground_assignment[{pos}], {solution[pos]} != {ground_assignment[pos]}'



def test_easy_2():
  # 6x6 easy 2
  # https://www.puzzle-binairo.com/binairo-6x6-easy/?e=MDo1LDE2MCw3NDg=
  board = np.array([
    [' ', ' ', 'W', ' ', ' ', 'W'],
    [' ', ' ', ' ', ' ', ' ', 'B'],
    [' ', ' ', 'W', 'W', ' ', ' '],
    ['W', ' ', 'W', 'W', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', 'W'],
    [' ', ' ', ' ', ' ', 'B', ' ']
  ])
  binst = solver.Board(board=board)
  solutions = binst.solve_and_print()
  assert len(solutions) == 1, f'unique solutions != 1, == {len(solutions)}'
  solution = solutions[0].assignment
  ground = np.array([
    ['B', 'B', ' ', 'B', ' ', ' '],
    [' ', ' ', 'B', 'B', ' ', 'B'],
    ['B', 'B', ' ', ' ', 'B', ' '],
    [' ', 'B', ' ', ' ', 'B', 'B'],
    ['B', ' ', 'B', 'B', ' ', ' '],
    [' ', ' ', 'B', ' ', 'B', 'B'],
  ])
  ground_assignment = {get_pos(x=x, y=y): 1 if ground[y][x] == 'B' else 0 for x in range(ground.shape[1]) for y in range(ground.shape[0])}
  assert set(solution.keys()) == set(ground_assignment.keys()), f'solution keys != ground assignment keys, {set(solution.keys()) ^ set(ground_assignment.keys())} \n\n\n{solution} \n\n\n{ground_assignment}'
  for pos in solution.keys():
    assert solution[pos] == ground_assignment[pos], f'solution[{pos}] != ground_assignment[{pos}], {solution[pos]} != {ground_assignment[pos]}'


def test_ground():
  # 20 x 20 hard
  # https://www.puzzle-binairo.com/binairo-20x20-hard/?e=OTozLDY2MSw3MjE=
  board = np.array([
    [' ', ' ', ' ', ' ', 'W', ' ', ' ', ' ', 'W', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'B', ' ', ' ', 'W'],
    [' ', 'W', ' ', ' ', 'B', ' ', ' ', ' ', ' ', ' ', ' ', 'W', ' ', ' ', 'B', ' ', ' ', ' ', 'B', ' '],
    [' ', 'W', ' ', ' ', ' ', 'W', ' ', 'W', 'W', ' ', ' ', ' ', 'B', ' ', ' ', 'W', ' ', ' ', ' ', ' '],
    ['B', ' ', ' ', 'W', ' ', ' ', 'B', ' ', ' ', ' ', ' ', ' ', 'B', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    ['B', ' ', ' ', ' ', 'W', ' ', ' ', ' ', ' ', 'B', ' ', 'W', ' ', ' ', ' ', 'B', ' ', ' ', ' ', 'W'],
    [' ', ' ', 'W', ' ', ' ', 'W', ' ', ' ', ' ', ' ', 'W', ' ', ' ', ' ', ' ', ' ', ' ', 'W', ' ', ' '],
    ['W', ' ', ' ', ' ', ' ', ' ', 'B', ' ', ' ', 'B', ' ', ' ', 'B', 'B', ' ', ' ', 'W', ' ', 'B', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'B', ' ', ' ', ' ', ' ', ' ', 'W', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', 'W', ' ', 'B', ' ', 'W', ' ', ' ', ' ', 'B', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', 'W', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'W', ' ', ' ', ' ', 'W', 'W', ' ', ' ', ' '],
    [' ', ' ', 'B', ' ', ' ', ' ', 'B', ' ', 'B', ' ', ' ', ' ', 'B', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', 'W', 'B', ' ', 'W', ' ', 'B', ' ', ' ', ' ', ' ', ' ', 'W', 'W', ' ', 'B', ' ', ' ', 'B', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'B', ' ', ' ', ' ', 'B', 'B'],
    [' ', 'B', ' ', ' ', ' ', ' ', 'W', ' ', 'W', 'W', ' ', ' ', 'W', ' ', ' ', ' ', 'W', ' ', ' ', ' '],
    [' ', ' ', 'W', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'W', 'W', ' ', ' ', 'W', 'W', ' '],
    [' ', 'B', ' ', 'B', 'W', ' ', ' ', ' ', ' ', ' ', ' ', 'B', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', 'B', ' ', ' ', ' ', 'W', ' ', ' ', ' ', 'W', ' ', ' ', 'B', ' ', 'B', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'B', ' ', ' ', ' ', ' ', ' ', ' ', 'W', ' ', ' ', ' ', 'W'],
    [' ', ' ', ' ', 'B', 'B', ' ', ' ', 'W', ' ', 'W', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'B', ' ', ' '],
    ['B', ' ', 'B', 'B', ' ', ' ', ' ', ' ', ' ', 'W', ' ', 'B', ' ', ' ', 'B', ' ', ' ', ' ', ' ', ' ']
  ])
  binst = solver.Board(board=board)
  solutions = binst.solve_and_print()
  assert len(solutions) == 1, f'unique solutions != 1, == {len(solutions)}'
  solution = solutions[0].assignment
  ground = np.array([
    ['B', 'B', ' ', 'B', ' ', 'B', ' ', 'B', ' ', ' ', 'B', ' ', ' ', 'B', ' ', 'B', 'B', ' ', 'B', ' ' ],
    [ ' ', ' ', 'B', ' ', 'B', 'B', ' ', 'B', 'B', ' ', 'B', ' ', ' ', 'B', 'B', ' ', ' ', 'B', 'B', ' ' ],
    [ ' ', ' ', 'B', 'B', ' ', ' ', 'B', ' ', ' ', 'B', ' ', 'B', 'B', ' ', 'B', ' ', 'B', 'B', ' ', 'B' ],
    [ 'B', 'B', ' ', ' ', 'B', ' ', 'B', ' ', 'B', ' ', ' ', 'B', 'B', ' ', ' ', 'B', ' ', ' ', 'B', 'B' ],
    [ 'B', ' ', 'B', ' ', ' ', 'B', ' ', 'B', ' ', 'B', 'B', ' ', ' ', 'B', ' ', 'B', ' ', 'B', 'B', ' ' ],
    [ ' ', 'B', ' ', 'B', 'B', ' ', ' ', 'B', 'B', ' ', ' ', 'B', 'B', ' ', 'B', ' ', 'B', ' ', ' ', 'B' ],
    [ ' ', 'B', ' ', ' ', 'B', ' ', 'B', ' ', ' ', 'B', 'B', ' ', 'B', 'B', ' ', 'B', ' ', 'B', 'B', ' ' ],
    [ 'B', ' ', 'B', ' ', ' ', 'B', ' ', 'B', 'B', ' ', 'B', 'B', ' ', ' ', 'B', ' ', ' ', 'B', ' ', 'B' ],
    [ ' ', 'B', ' ', 'B', ' ', 'B', 'B', ' ', ' ', 'B', ' ', 'B', 'B', ' ', ' ', 'B', 'B', ' ', 'B', ' ' ],
    [ 'B', ' ', ' ', 'B', 'B', ' ', ' ', 'B', ' ', 'B', 'B', ' ', ' ', 'B', 'B', ' ', ' ', 'B', ' ', 'B' ],
    [ ' ', 'B', 'B', ' ', 'B', ' ', 'B', ' ', 'B', ' ', 'B', ' ', 'B', 'B', ' ', ' ', 'B', 'B', ' ', ' ' ],
    [ 'B', ' ', 'B', ' ', ' ', 'B', 'B', ' ', 'B', 'B', ' ', 'B', ' ', ' ', 'B', 'B', ' ', ' ', 'B', ' ' ],
    [ 'B', ' ', ' ', 'B', 'B', ' ', ' ', 'B', ' ', 'B', ' ', ' ', 'B', ' ', 'B', ' ', 'B', ' ', 'B', 'B' ],
    [ ' ', 'B', 'B', ' ', 'B', 'B', ' ', 'B', ' ', ' ', 'B', 'B', ' ', 'B', ' ', 'B', ' ', 'B', ' ', ' ' ],
    [ 'B', ' ', ' ', 'B', ' ', 'B', 'B', ' ', 'B', 'B', ' ', ' ', 'B', ' ', ' ', 'B', 'B', ' ', ' ', 'B' ],
    [ ' ', 'B', ' ', 'B', ' ', ' ', 'B', ' ', 'B', 'B', ' ', 'B', ' ', 'B', 'B', ' ', 'B', ' ', 'B', ' ' ],
    [ ' ', 'B', 'B', ' ', 'B', ' ', ' ', 'B', ' ', ' ', 'B', ' ', 'B', ' ', 'B', 'B', ' ', 'B', ' ', 'B' ],
    [ 'B', ' ', 'B', ' ', ' ', 'B', 'B', ' ', 'B', 'B', ' ', ' ', 'B', 'B', ' ', ' ', 'B', ' ', 'B', ' ' ],
    [ ' ', 'B', ' ', 'B', 'B', ' ', 'B', ' ', 'B', ' ', ' ', 'B', ' ', 'B', ' ', 'B', ' ', 'B', ' ', 'B' ],
    [ 'B', ' ', 'B', 'B', ' ', 'B', ' ', 'B', ' ', ' ', 'B', 'B', ' ', ' ', 'B', ' ', 'B', ' ', ' ', 'B' ],
  ])
  ground_assignment = {get_pos(x=x, y=y): 1 if ground[y][x] == 'B' else 0 for x in range(ground.shape[1]) for y in range(ground.shape[0])}
  assert set(solution.keys()) == set(ground_assignment.keys()), f'solution keys != ground assignment keys, {set(solution.keys()) ^ set(ground_assignment.keys())} \n\n\n{solution} \n\n\n{ground_assignment}'
  for pos in solution.keys():
    assert solution[pos] == ground_assignment[pos], f'solution[{pos}] != ground_assignment[{pos}], {solution[pos]} != {ground_assignment[pos]}'


if __name__ == '__main__':
  test_easy()
  test_easy_2()
  test_ground()

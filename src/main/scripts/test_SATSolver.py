from pulsar.SATSolver import SATSolver

from pulsar.tools import get_actions_from_question
from pulsar.Solver import Solver

test_puzzle_rank_3 = [
    [1, None, 5, None, None, None, 9, 8, None],
    [None, None, None, 3, None, None, None, 1, None],
    [None, 7, 6, None, None, 9, 4, None, None],
    [4, None, 1, 6, 9, 3, None, 2, 7],
    [8, 6, 2, None, 1, 5, None, 9, 4],
    [None, None, None, 8, None, None, None, 6, 5],
    [None, 1, 8, 4, 3, None, None, None, None],
    [7, None, None, None, None, None, 6, None, None],
    [None, None, None, None, 7, 1, None, 4, None],
]


def puzzle_valid(grid):

    size = len(grid)
    rank = int(size**0.5)

    for x in range(size):
        for y in range(size):
            if len(grid[x][y]) == 1:
                grid[x][y] = grid[x][y][0]
            else:
                grid[x][y] = None

    for row in grid:
        row = [x for x in row if x is not None]
        if len(row) != len(set(row)):
            return False

    seen = [{-1} for _ in range(size)]  # Create a set for each column

    for row in grid:
        for col_index, value in enumerate(row):
            if value in seen[col_index]:
                return False  # Duplicate found in column
            if value:
                seen[col_index].add(value)

    for i in range(0, size, rank):
        for j in range(0, size, rank):
            sub_grid = set()  # Create a set for each subgrid
            for x in range(i, i + rank):
                for y in range(j, j + rank):
                    value = grid[x][y]
                    if value in sub_grid:
                        return False  # Duplicate found in subgrid
                    if value:
                        sub_grid.add(value)

    return True


grid1, actions = get_actions_from_question(test_puzzle_rank_3)
test = Solver(grid1, [])


solver = SATSolver(test_puzzle_rank_3)
solution = solver.solve()
test.print_solution(solution)

if puzzle_valid(solution):
    print("Valid")
else:
    print("Invalid")

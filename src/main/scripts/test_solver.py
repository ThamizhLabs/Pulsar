from pulsar.tools import simple_solve, apply_backtracking, sequential_solver
from copy import deepcopy
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

test_puzzle_rank_4 = [[None, None, 11, None, None, 6, 14, 2, None, None, 3, None, 12, None, 9, None], [10, 7, None, None, 12, None, None, 3, None, None, None, None, 16, 1, None, 2], [None, None, None, None, None, 10, None, None, 12, None, None, None, None, None, None, None], [None, None, 3, 15, None, None, 9, 5, 16, None, None, 6, None, None, 13, 14], [13, None, 2, 5, 8, 9, None, 16, None, None, None, None, 6, None, 7, None], [None, None, None, None, None, None, 5, 14, None, None, 4, None, None, None, 11, 1], [None, None, 12, None, 7, 15, None, 10, 14, 16, None, None, None, None, None, None], [4, 9, None, 3, None, None, 1, 13, None, 15, 7, None, None, None, None, None], [None, None, None, None, None, 3, 15, None, 13, 12, None, None, 4, None, 1, 8], [None, None, None, None, None, None, 6, 9, 2, None, 14, 8, None, 3, None, None], [3, 13, None, None, None, 8, None, None, 1, 9, None, None, None, None, None, None], [None, 10, None, 2, None, None, None, None, 11, None, 16, 5, 15, 6, None, 12], [11, 6, None, None, 3, None, None, 7, 4, 2, None, None, 1, 8, None, None], [None, None, None, None, None, None, None, 6, None, None, 1, None, None, None, None, None], [2, None, 7, 8, None, None, None, None, 3, None, None, 13, None, None, 4, 10], [None, 4, None, 10, None, 14, None, None, 9, 7, 8, None, None, 15, None, None]]


def puzzle_valid(grid):

    grid = deepcopy(grid)
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

    seen = [set([-1]) for _ in range(size)]  # Create a set for each column

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


solver = sequential_solver(test_puzzle_rank_4)

if solver.state_invalid:
    print("Invalid puzzle!")

if solver.state_solved:
    print("Solved")
    solver.print_solution()
else:
    # solver.print_solution()
    print("Simple Solve not enough, applying backtracking")

    solver = apply_backtracking(solver.grid, depth=4)
    if not solver.state_solved:
        print("Could not find solution")
    else:
        print("Solved")
        solver.print_solution()
        del solver

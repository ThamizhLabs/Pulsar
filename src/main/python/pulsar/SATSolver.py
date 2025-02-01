from pysat.solvers import Glucose3
from pulsar.useful_tools import flatten_index_equal_depth, get_index_equal_depth


check_all_solutions = True


class SATSolver:
    def __init__(self, puzzle):
        self.sudoku = Glucose3()
        self.size = len(puzzle)
        self.rank = int(self.size**0.5)
        self.puzzle = puzzle

        self.define_sudoku_rules()

    def var(self, *args):
        return flatten_index_equal_depth(self.size, *args)

    def decode_var(self, x):
        return get_index_equal_depth(3, self.size, x)

    def define_sudoku_rules(self):

        # Rule 1:
        # Every cell needs to have at least one true flag on the third dimension
        for i in range(self.size):
            for j in range(self.size):
                self.sudoku.add_clause([self.var(i, j, k) for k in range(self.size)])

        # Rule 2: Uniqueness on depth
        # Every cell needs to have only one true flag on the third dimension
        for i in range(self.size):
            for j in range(self.size):
                for k1 in range(self.size):
                    for k2 in range(k1 + 1, self.size):
                        self.sudoku.add_clause([-self.var(i, j, k1), -self.var(i, j, k2)])

        # Rule 3: Uniqueness on row and column
        # Every row in its third dimension should have only one true flag, so should the column
        for x in range(self.size):
            for k in range(self.size):
                for y1 in range(self.size):
                    for y2 in range(y1 + 1, self.size):
                        self.sudoku.add_clause([-self.var(x, y1, k), -self.var(x, y2, k)])
                        self.sudoku.add_clause([-self.var(y1, x, k), -self.var(y2, x, k)])

        # Rule 4: Uniqueness on Subgrid
        # Every subgrid in its third dimension should have only one true flag
        for i in range(0, self.size, self.rank):
            for j in range(0, self.size, self.rank):
                for k in range(self.size):
                    for i1 in range(i, i + self.rank):
                        for j1 in range(j, j + self.rank):
                            impacted_cells = [self.var(i1, j1, k)]
                            for i2 in range(i, i + self.rank):
                                for j2 in range(j, j + self.rank):
                                    if (i2 != i1) and (j2 != j1):
                                        impacted_cells.append(self.var(i2, j2, k))

                            for idx in range(len(impacted_cells)):
                                for idx1 in range(idx + 1, len(impacted_cells)):
                                    self.sudoku.add_clause([-impacted_cells[idx], -impacted_cells[idx1]])

    def solve(self):

        # Apply Hints
        for i in range(self.size):
            for j in range(self.size):
                if self.puzzle[i][j]:
                    # print(i, j, self.puzzle[i][j])
                    self.sudoku.add_clause([self.var(i, j, self.puzzle[i][j] - 1)])

        # Solve
        status = self.sudoku.solve()

        if status:
            print("Solved!")

            solver_solution = self.sudoku.get_model()

            solutions = []
            while solver_solution and len(solutions) <= 5:
                solution = [[[] for _ in range(self.size)] for _ in range(self.size)]
                for var in solver_solution:
                    if var >= 0:
                        (i, j, k) = self.decode_var(var)
                        solution[i][j] = [k + 1]
                solutions.append(solution)

                self.rate_difficulty()
                solver_solution = self.check_next_solution(solution)

            print(f"No of possible solutions: {len(solutions)}")

            return solution

        print("No Solution exists!")
        return None

    def check_next_solution(self, prev_solution):
        # Add a negation clause to block the first solution
        negation_clause = []
        for i in range(self.size):
            for j in range(self.size):
                k = prev_solution[i][j][0] - 1
                negation_clause.append(-self.var(i, j, k))

        self.sudoku.add_clause(negation_clause)

        if self.sudoku.solve():
            return self.sudoku.get_model()

        return None

    def rate_difficulty(self):
        stats = self.sudoku.accum_stats()

        # Extract relevant statistics
        num_clauses = stats.get("clauses", 0)
        num_conflicts = stats.get("conflicts", 0)
        num_decisions = stats.get("decisions", 0)
        num_propagations = stats.get("propagations", 0)

        # Basic formula to estimate difficulty (adjust weights as needed)
        difficulty_score = (
                (num_clauses / 100) +
                (num_conflicts * 2) +
                (num_decisions / 50) +
                (num_propagations / 500)
        )

        # Classify difficulty based on the score
        print(f"Difficulty Score: {difficulty_score}")
        print(stats)
        if difficulty_score < 10:
            return "Easy"
        elif difficulty_score < 20:
            return "Medium"
        elif difficulty_score < 35:
            return "Hard"
        else:
            return "Very Hard"
        
class Solver:
    def __init__(self, grid, actions=[]):
        super().__init__()

        self.size = len(grid)
        self.rank = int(self.size**0.5)
        self.grid = grid

        self.state_invalid = False
        self.state_solved = False
        self.invalid_index = (-1, -1)
        self.actions = actions

        # self.ui_obj = ui_obj

    def solve(self):
        if len(self.actions) > 0:
            self.apply_actions(self.actions)

        self.apply_distinctive_iteration()

    def apply_actions(self, actions):
        for action in actions:
            if self.state_invalid:
                break
            else:
                self.setval(action)

    def is_valid(self, action):
        (i, j) = action['idx']
        val = action['val']
        for it in range(self.size):
            if (len(self.grid[i][it]) <= 1) and (self.grid[i][it][0] == val) and (it != j):
                return False
            if (len(self.grid[it][j]) <= 1) and (self.grid[it][j][0] == val) and (it != i):
                return False
        it = i//self.rank
        jt = j//self.rank
        for i1 in range(it * self.rank, it * self.rank + self.rank):
            for j1 in range(jt * self.rank, jt * self.rank + self.rank):
                if ((len(self.grid[i1][j1]) <= 1) and
                        (self.grid[i1][j1][0] == val) and (i1 != i) and (j1 != j)):
                    return False
        return True

    def setval(self, action):
        (x, y) = action['idx']
        no = action['val']

        if not self.is_valid(action):
            self.state_invalid = True
            if self.invalid_index == (-1, -1):
                self.invalid_index = (x, y)
            return

        self.grid[x][y] = [no]

        relative_cells = self.getrelative_cells(x, y)

        for t in relative_cells:
            (i, j) = t
            if len(self.grid[i][j]) > 2:
                if self.grid[i][j].count(no) > 0:
                    self.grid[i][j].remove(no)
            elif len(self.grid[i][j]) == 2:
                if self.grid[i][j].count(no) > 0:
                    self.grid[i][j].remove(no)
                    self.setval({'idx': (i, j), 'val': self.grid[i][j][0]})

    def apply_distinctive_iteration(self):

        itercnt = 0
        restart_iteration = True
        while restart_iteration and (not self.state_invalid):
            itercnt += 1

            restart_iteration = False
            for i in range(self.size):
                for j in range(self.size):
                    if len(self.grid[i][j]) > 1:
                        for k in self.grid[i][j]:
                            restart_iteration = self.unique_in_relative_cells(k, i, j)
                            if restart_iteration:
                                self.setval({'idx': (i, j), 'val': k})
                                break
                    if restart_iteration:
                        break
                if restart_iteration:
                    break

        self.state_solved = True
        for i in range(self.size):
            for j in range(self.size):
                if len(self.grid[i][j]) > 1:
                    self.state_solved = False

    def unique_in_relative_cells(self, val, x, y):
        relative_cells = self.getrelative_cells(x, y)
        relative_row_cells = []
        relative_col_cells = []
        relative_blk_cells = []

        flag1, flag2, flag3 = True, True, True

        for t in relative_cells:
            (i, j) = t

            if (i == x) and (self.grid[i][j].count(val) > 0):
                flag1 = False

            if (j == y) and (self.grid[i][j].count(val) > 0):
                flag2 = False

            if (int(x - x % self.rank) <= i <= int(x - x % self.size + self.size - 1) and
                    int(y - y % self.size) <= j <= int(y - y % self.size + self.size - 1)):
                if self.grid[i][j].count(val) > 0:
                    flag3 = False

        # for t in relative_row_cells:
        #     i, j = t
        #     if self.grid[i][j].count(val) > 0:
        #         flag1 = False
        #
        # for t in relative_col_cells:
        #     i, j = t
        #     if self.grid[i][j].count(val) > 0:
        #         flag2 = False
        #
        # for t in relative_blk_cells:
        #     i, j = t
        #     if self.grid[i][j].count(val) > 0:
        #         flag3 = False

        return flag1 | flag2 | flag3

    def getrelative_cells(self, x, y):

        out = []
        for t in range(self.size):
            if t != x:
                temp = (t, y)
                out.append(temp)
            if t != y:
                temp = (x, t)
                out.append(temp)

        x1, y1 = x - (x % self.rank), y - (y % self.rank)

        for i in range(x1, x1 + self.rank):
            for j in range(y1, y1 + self.rank):
                if i != x and j != y:
                    temp = (i, j)
                    out.append(temp)

        return out

    def print_solution(self, grid=None):
        if grid:
            size = len(grid)
        else:
            grid = self.grid
            size = self.size
        print("Printing Grid..")
        fill_count = 0
        for i in range(size):
            row = grid[i]
            row_str = ''
            for x in row:
                if len(x) <= 1:
                    fill_count += 1
                    row_str = row_str + ',' + str(x[0])
                else:
                    row_str = row_str + ',' + '_'
            print(row_str)

        print(f"Elements filled = {fill_count}")

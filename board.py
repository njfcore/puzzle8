"""Board: representation of an n x n sliding puzzle board."""


class Board:
    def __init__(self, tiles):
        """Build a board from a 2D list of tiles. 0 means the blank square."""
        n = len(tiles)
        if n < 2 or any(len(row) != n for row in tiles):
            raise ValueError("tiles must be an n x n array with n >= 2")

        # tuple of tuples: immutable, so the board can never change after creation
        self._tiles = tuple(tuple(row) for row in tiles)
        self._n = n

        values = sorted(v for row in self._tiles for v in row)
        if values != list(range(n * n)):
            raise ValueError("tiles must contain each of 0..n^2-1 exactly once")

        # position of the blank square, found once
        self._blank = next(
            (i, j)
            for i in range(n)
            for j in range(n)
            if self._tiles[i][j] == 0
        )

        # cache: the board is immutable, so this value never changes
        self._manhattan = self._compute_manhattan()
            
    def size(self):
        """Side length of the board (3 for the 8-puzzle)."""
        return self._n

    def tile_at(self, row, col):
        """Value at (row, col), zero-based. 0 is the blank square."""
        if not (0 <= row < self._n and 0 <= col < self._n):
            raise IndexError(f"({row}, {col}) is outside the board")
        return self._tiles[row][col]

    def __str__(self):
        """First line: size. Then one line per row."""
        width = len(str(self._n ** 2 - 1))  # widest number, for alignment
        lines = [" ".join(f"{v:>{width}}" for v in row) for row in self._tiles]
        return f"{self._n}\n" + "\n".join(lines)

    def hamming(self):
        """Number of non-blank tiles that are not in their goal position."""
        count = 0
        for i in range(self._n):
            for j in range(self._n):
                v = self._tiles[i][j]
                if v != 0 and v != i * self._n + j + 1:
                    count += 1
        return count

    def _compute_manhattan(self):
        """Sum of |row diff| + |col diff| from each tile to its goal cell."""
        total = 0
        for i in range(self._n):
            for j in range(self._n):
                v = self._tiles[i][j]
                if v != 0:
                    goal_row, goal_col = divmod(v - 1, self._n)
                    total += abs(i - goal_row) + abs(j - goal_col)
        return total

    def manhattan(self):
        """Cached Manhattan distance (computed once in the constructor)."""
        return self._manhattan

    def is_goal(self):
        """True if every tile is in place (the blank is then forced to the last cell)."""
        return self.hamming() == 0

    def __eq__(self, other):
        """Boards are equal if they have the same size and the same tiles."""
        if not isinstance(other, Board):
            return NotImplemented
        return self._tiles == other._tiles

    def __hash__(self):
        """Needed so boards can be stored in sets and dict keys."""
        return hash(self._tiles)

    def blank_pos(self):
        """(row, col) of the blank square."""
        return self._blank

    def neighbors(self):
        """All boards reachable with one legal move. Self is never modified."""
        bi, bj = self._blank
        result = []
        # up, down, left, right (relative to the blank square)
        for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ni, nj = bi + di, bj + dj  # the tile that would slide into the blank
            if 0 <= ni < self._n and 0 <= nj < self._n:
                grid = [list(row) for row in self._tiles]  # mutable copy
                grid[bi][bj], grid[ni][nj] = grid[ni][nj], 0
                result.append(Board(grid))
        return result
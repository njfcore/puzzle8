"""Board: representation of an n x n sliding puzzle board."""

# lets the program also read files typed with Persian digits (copied from the PDF)
_PERSIAN_DIGITS = str.maketrans("??????????", "0123456789")
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

    @staticmethod
    def from_file(path):
        """Read a board: first the size n, then n rows of n numbers (0 = blank)."""
        with open(path, encoding="utf-8-sig") as f:   # utf-8-sig skips the Notepad BOM
            text = f.read().translate(_PERSIAN_DIGITS)
        numbers = [int(x) for x in text.split()]
        if not numbers:
            raise ValueError("the input file is empty")
        n = numbers[0]
        if n < 2 or len(numbers) != 1 + n * n:
            raise ValueError(f"expected the size {n} followed by {n * n} numbers, "
                             f"found {len(numbers) - 1} numbers")
        return Board([numbers[1 + i * n: 1 + (i + 1) * n] for i in range(n)])

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

    def inversions(self):
        """Number of pairs of tiles in row-major order where the larger comes first.
        The blank square is ignored."""
        flat = [v for row in self._tiles for v in row if v != 0]
        count = 0
        for a in range(len(flat)):
            for b in range(a + 1, len(flat)):
                if flat[a] > flat[b]:
                    count += 1
        return count

    def is_solvable(self):
        """True if the goal board can be reached from this board."""
        inv = self.inversions()
        if self._n % 2 == 1:
            return inv % 2 == 0
        return (inv + self._blank[0]) % 2 == 1

def _expect_error(error_type, func, *args):
    """Helper for tests: func(*args) must raise error_type."""
    try:
        func(*args)
    except error_type:
        return
    raise AssertionError(f"expected {error_type.__name__} from {func.__name__}{args}")


def main():
    """Direct tests of the public Board methods."""
    b = Board([[8, 1, 3], [4, 0, 2], [7, 6, 5]])  # the example board from the PDF

    # construction, size, tile_at, __str__
    assert b.size() == 3
    assert b.tile_at(0, 0) == 8
    assert b.tile_at(1, 1) == 0
    assert str(b) == "3\n8 1 3\n4 0 2\n7 6 5"
    _expect_error(IndexError, b.tile_at, 3, 0)
    _expect_error(IndexError, b.tile_at, 0, -1)

    # invalid boards are rejected
    _expect_error(ValueError, Board, [[1, 2], [3]])          # not square
    _expect_error(ValueError, Board, [[1, 1], [2, 3]])       # duplicate tile
    _expect_error(ValueError, Board, [[1, 2], [3, 4]])       # no blank, 4 out of range

    # distances (values given in the PDF)
    assert b.hamming() == 5
    assert b.manhattan() == 10

    # goal
    goal = Board([[1, 2, 3], [4, 5, 6], [7, 8, 0]])
    assert goal.is_goal() and goal.hamming() == 0 and goal.manhattan() == 0
    assert not b.is_goal()

    # equality and hashing
    same = Board([[8, 1, 3], [4, 0, 2], [7, 6, 5]])
    other = Board([[1, 8, 3], [4, 0, 2], [7, 6, 5]])
    assert b == same and b is not same
    assert b != other
    assert b != "not a board"
    assert len({b, same, other}) == 2

    # neighbors: 2 in a corner, 3 on an edge, 4 in the center
    corner = Board([[0, 1, 3], [4, 2, 5], [7, 8, 6]])
    edge = Board([[1, 0, 3], [4, 2, 5], [7, 8, 6]])
    center = Board([[1, 2, 3], [4, 0, 5], [7, 8, 6]])
    assert len(corner.neighbors()) == 2
    assert len(edge.neighbors()) == 3
    assert len(center.neighbors()) == 4
    expected = {
        Board([[0, 1, 3], [4, 2, 5], [7, 8, 6]]),
        Board([[1, 2, 3], [4, 0, 5], [7, 8, 6]]),
        Board([[1, 3, 0], [4, 2, 5], [7, 8, 6]]),
    }
    assert set(edge.neighbors()) == expected
    assert str(edge) == "3\n1 0 3\n4 2 5\n7 8 6"           # original not modified

    # solvability
    assert corner.is_solvable()                              # 4 inversions
    assert not Board([[1, 2, 3], [4, 5, 6], [8, 7, 0]]).is_solvable()
    assert not Board([[1, 2, 3], [0, 4, 6], [8, 5, 7]]).is_solvable()  # 3 inversions
    assert goal.is_solvable()
    g4 = Board([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 0]])
    bad4 = Board([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 15, 14, 0]])
    assert g4.is_solvable() and not bad4.is_solvable()
    # one legal move never changes solvability
    for board in (b, corner, edge, g4):
        assert all(n.is_solvable() == board.is_solvable() for n in board.neighbors())

    print(b)
    print("All Board tests passed.")


if __name__ == "__main__":
    main()    
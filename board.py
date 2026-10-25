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
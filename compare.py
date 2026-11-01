"""Compare the search algorithms on a few boards (moves, cost, expanded nodes, time)."""
import time

from board import Board
from solver import Solver

BOARDS = [
    ("easy   (4 moves)", [[0, 1, 3], [4, 2, 5], [7, 8, 6]]),
    ("medium (14 moves)", [[8, 1, 3], [4, 0, 2], [7, 6, 5]]),
    ("harder (20 moves)", [[1, 2, 6], [4, 0, 7], [3, 5, 8]]),
]
RUNS = [
    ("bfs", "manhattan"),
    ("dfs", "manhattan"),
    ("ucs", "manhattan"),
    ("astar", "hamming"),
    ("astar", "manhattan"),
]


def label(algorithm, heuristic):
    return f"A* ({heuristic})" if algorithm == "astar" else algorithm.upper()


def main():
    for name, tiles in BOARDS:
        print(f"\n{name}")
        print(f"  {'algorithm':<16}{'moves':>7}{'cost':>9}{'expanded':>10}{'time(s)':>9}")
        for algorithm, heuristic in RUNS:
            start = time.perf_counter()
            solver = Solver(Board(tiles), algorithm, heuristic)
            elapsed = time.perf_counter() - start
            print(f"  {label(algorithm, heuristic):<16}{solver.moves():>7}"
                  f"{solver.tile_cost():>9}{solver.expanded:>10}{elapsed:>9.2f}")


if __name__ == "__main__":
    main()
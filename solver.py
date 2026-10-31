"""Solver: finds a shortest sequence of boards from an initial board to the goal."""
from collections import deque


class Node:
    """A search node: a board, how many moves it took to get here, and where we came from."""
    __slots__ = ("board", "moves", "prev")

    def __init__(self, board, moves=0, prev=None):
        self.board = board
        self.moves = moves
        self.prev = prev


class Solver:
    def __init__(self, initial, algorithm="bfs"):
        if algorithm != "bfs":
            raise ValueError("only 'bfs' is implemented so far")
        self.initial = initial
        self.algorithm = algorithm
        self.expanded = 0          # how many nodes we expanded (for comparing algorithms later)
        self._goal_node = None
        self._solvable = initial.is_solvable()
        if self._solvable:         # never start an expensive search on an unsolvable board
            self._goal_node = self._bfs()

    def is_solvable(self):
        return self._solvable

    def moves(self):
        """Number of moves in the solution, or -1 if the board is unsolvable."""
        return self._goal_node.moves if self._goal_node else -1

    def solution(self):
        """List of boards from the initial board to the goal, or None if unsolvable."""
        if self._goal_node is None:
            return None
        path = []
        node = self._goal_node
        while node is not None:        # walk back from the goal to the start
            path.append(node.board)
            node = node.prev
        path.reverse()                 # we built it backwards
        return path

    def _bfs(self):
        start = Node(self.initial)
        if self.initial.is_goal():
            return start
        frontier = deque([start])      # FIFO queue
        seen = {self.initial}
        while frontier:
            node = frontier.popleft()  # take from the front
            self.expanded += 1
            for nb in node.board.neighbors():
                if nb in seen:
                    continue
                child = Node(nb, node.moves + 1, node)
                if nb.is_goal():       # first time we reach the goal is the shortest path
                    return child
                seen.add(nb)
                frontier.append(child) # add at the back
        return None
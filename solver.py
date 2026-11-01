"""Solver: finds a shortest sequence of boards from an initial board to the goal."""
import heapq
from collections import deque


class Node:
    """A search node: a board, moves so far, where we came from, and its priority."""
    __slots__ = ("board", "moves", "prev", "priority")

    def __init__(self, board, moves=0, prev=None, priority=0):
        self.board = board
        self.moves = moves
        self.prev = prev
        self.priority = priority


class Solver:
    ALGORITHMS = ("bfs", "dfs", "astar")
    HEURISTICS = ("manhattan", "hamming")

    def __init__(self, initial, algorithm="bfs", heuristic="manhattan"):
        if algorithm not in self.ALGORITHMS:
            raise ValueError(f"algorithm must be one of {self.ALGORITHMS}")
        if heuristic not in self.HEURISTICS:
            raise ValueError(f"heuristic must be one of {self.HEURISTICS}")
        self.initial = initial
        self.algorithm = algorithm
        self.heuristic = heuristic
        self.expanded = 0
        self._goal_node = None
        self._solvable = initial.is_solvable()
        if self._solvable:
            if algorithm == "astar":
                self._goal_node = self._astar()
            else:
                self._goal_node = self._uninformed()

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

    def _uninformed(self):
        """BFS or DFS: the same code, only the end we take from differs."""
        start = Node(self.initial)
        if self.initial.is_goal():
            return start
        frontier = deque([start])
        # BFS: take from the front (queue). DFS: take from the back (stack).
        take = frontier.popleft if self.algorithm == "bfs" else frontier.pop
        seen = {self.initial}
        while frontier:
            node = take()
            self.expanded += 1
            for nb in node.board.neighbors():
                if nb in seen:
                    continue
                child = Node(nb, node.moves + 1, node)
                if nb.is_goal():
                    return child
                seen.add(nb)
                frontier.append(child)
        return None

    def _h(self, board):
        """The heuristic estimate of the remaining cost."""
        if self.heuristic == "manhattan":
            return board.manhattan()
        return board.hamming()

    def _astar(self):
        counter = 0                       # tie-breaker: older nodes first
        start = Node(self.initial, 0, None, self._h(self.initial))
        heap = [(start.priority, counter, start)]
        best_g = {self.initial: 0}        # cheapest g known for each board
        closed = set()                    # boards we have fully expanded
        while heap:
            _, _, node = heapq.heappop(heap)      # smallest f = g + h
            if node.board in closed:              # stale duplicate, skip
                continue
            if node.board.is_goal():              # test when POPPED, not when created
                return node
            closed.add(node.board)
            self.expanded += 1
            g = node.moves + 1                    # cost of every child
            for nb in node.board.neighbors():
                if nb in closed or g >= best_g.get(nb, float("inf")):
                    continue                      # not better than what we have
                best_g[nb] = g
                counter += 1
                child = Node(nb, g, node, g + self._h(nb))
                heapq.heappush(heap, (child.priority, counter, child))
        return None
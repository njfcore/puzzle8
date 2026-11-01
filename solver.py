"""Solver: finds a shortest sequence of boards from an initial board to the goal."""
import heapq
from collections import deque


class Node:
    """A search node: a board, moves so far, where we came from, priority and cost."""
    __slots__ = ("board", "moves", "prev", "priority", "cost")

    def __init__(self, board, moves=0, prev=None, priority=0, cost=0):
        self.board = board
        self.moves = moves
        self.prev = prev
        self.priority = priority
        self.cost = cost


class Solver:
    ALGORITHMS = ("bfs", "dfs", "astar", "ucs")
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
            if algorithm in ("ucs", "astar"):
                self._goal_node = self._best_first()
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
            for nb in self._children(node):
                if nb in seen:
                    continue
                child = Node(nb, node.moves + 1, node)
                if nb.is_goal():
                    return child
                seen.add(nb)
                frontier.append(child)
        return None

    def _children(self, node):
        """Neighbors of node's board, skipping the board we just came from."""
        prev_board = node.prev.board if node.prev else None
        return [nb for nb in node.board.neighbors() if nb != prev_board]

    def _h(self, board):
        """The heuristic estimate of the remaining cost."""
        if self.heuristic == "manhattan":
            return board.manhattan()
        return board.hamming()

    def tile_cost(self):
        """Sum of the numbers of the tiles moved along the solution (the UCS cost)."""
        path = self.solution()
        if path is None:
            return -1
        # the tile that moved is the one that used to sit where the new blank is
        return sum(a.tile_at(*b.blank_pos()) for a, b in zip(path, path[1:]))

    def _best_first(self):
        """UCS: priority = g.  A*: priority = g + h.  Everything else is shared."""
        use_h = self.algorithm == "astar"
        counter = 0
        h0 = self._h(self.initial) if use_h else 0
        start = Node(self.initial, 0, None, h0, 0)
        heap = [(start.priority, counter, start)]
        best_g = {self.initial: 0}
        closed = set()
        while heap:
            _, _, node = heapq.heappop(heap)
            if node.board in closed:
                continue
            if node.board.is_goal():              # test when popped
                return node
            closed.add(node.board)
            self.expanded += 1
            for nb in node.board.neighbors():
                if nb in closed:
                    continue
                moved = node.board.tile_at(*nb.blank_pos())
                step = moved if self.algorithm == "ucs" else 1   # cost of this move
                g = node.cost + step
                if g >= best_g.get(nb, float("inf")):
                    continue
                best_g[nb] = g
                counter += 1
                priority = g + (self._h(nb) if use_h else 0)
                child = Node(nb, node.moves + 1, node, priority, g)
                heapq.heappush(heap, (child.priority, counter, child))
        return None
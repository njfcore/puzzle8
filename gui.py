"""gui.py: a Tkinter viewer that animates the solution of the sliding puzzle.

Run:  python gui.py
"""
import random
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from board import Board
from solver import Solver

SIZE = 420                 # canvas side in pixels
GAP = 5                    # gap between tiles
FRAME_MS = 25              # delay between two animation frames
BG = "#f4f1ea"
TILE = "#3b6fb6"           # tile that is not in its goal cell
TILE_OK = "#3f9b5f"        # tile that is already in its goal cell
TILE_MOVING = "#e08a1e"    # the tile that is sliding right now
FONT = "Segoe UI"


def positions(board):
    """Map every tile value to its (row, col)."""
    n = board.size()
    return {board.tile_at(r, c): (r, c) for r in range(n) for c in range(n)}


def goal_board(n):
    return Board([[(r * n + c + 1) % (n * n) for c in range(n)] for r in range(n)])


class App:
    def __init__(self, root):
        self.root = root
        root.title("Sliding Puzzle Solver")
        root.resizable(False, False)
        self.board = Board([[8, 1, 3], [4, 0, 2], [7, 6, 5]])  # the initial board
        self.path = [self.board]    # boards shown on screen (filled by Solve)
        self.index = 0              # which board of the path is on screen
        self.playing = False
        self.animating = False      # a tile is sliding right now
        self.busy = False           # the solver thread is running
        self._syncing = False       # True while we move the slider ourselves
        self._build()
        self._show_current()

    # ---------------------------------------------------------------- widgets
    def _build(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")
        ttk.Button(top, text="Open file...", command=self.open_file).pack(side="left")
        ttk.Button(top, text="Random", command=self.randomize).pack(side="left", padx=4)

        self.algorithm = tk.StringVar(value="astar")
        self.heuristic = tk.StringVar(value="manhattan")
        algo_box = ttk.Combobox(top, textvariable=self.algorithm, values=Solver.ALGORITHMS,
                                width=7, state="readonly")
        algo_box.pack(side="left", padx=(12, 4))
        algo_box.bind("<<ComboboxSelected>>", self._algorithm_changed)
        self.heur_box = ttk.Combobox(top, textvariable=self.heuristic, values=Solver.HEURISTICS,
                                     width=10, state="readonly")
        self.heur_box.pack(side="left")
        self.solve_button = ttk.Button(top, text="Solve", command=self.solve)
        self.solve_button.pack(side="left", padx=8)

        self.canvas = tk.Canvas(self.root, width=SIZE, height=SIZE, bg=BG, highlightthickness=0)
        self.canvas.pack(padx=8)

        self.info = tk.StringVar()
        self.summary = tk.StringVar()
        ttk.Label(self.root, textvariable=self.info, font=(FONT, 11)).pack(pady=(8, 0))
        ttk.Label(self.root, textvariable=self.summary, wraplength=SIZE).pack()

        self.step_scale = tk.Scale(self.root, from_=0, to=1, orient="horizontal", length=SIZE,
                                   showvalue=False, command=self._scale_moved)
        self.step_scale.pack(padx=8)

        controls = ttk.Frame(self.root, padding=8)
        controls.pack()
        ttk.Button(controls, text="|<", width=4, command=lambda: self.goto(0)).pack(side="left")
        ttk.Button(controls, text="<", width=4, command=lambda: self.move(-1)).pack(side="left")
        self.play_button = ttk.Button(controls, text="Play", width=8, command=self.toggle_play)
        self.play_button.pack(side="left", padx=4)
        ttk.Button(controls, text=">", width=4, command=lambda: self.move(1)).pack(side="left")
        ttk.Button(controls, text=">|", width=4,
                   command=lambda: self.goto(len(self.path) - 1)).pack(side="left")
        ttk.Label(controls, text="  Speed").pack(side="left")
        self.speed = tk.IntVar(value=5)
        tk.Scale(controls, variable=self.speed, from_=1, to=10, orient="horizontal",
                 showvalue=False, length=110).pack(side="left")

        self.root.bind("<space>", lambda e: self.toggle_play())
        self.root.bind("<Left>", lambda e: self.move(-1))
        self.root.bind("<Right>", lambda e: self.move(1))

    def _algorithm_changed(self, event=None):
        # the heuristic only matters for A*
        self.heur_box.config(state="readonly" if self.algorithm.get() == "astar" else "disabled")

    # ---------------------------------------------------------------- drawing
    def _rounded(self, x0, y0, x1, y1, r, **options):
        points = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1,
                  x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
        self.canvas.create_polygon(points, smooth=True, **options)

    def draw(self, board, moving=None):
        """Draw a board. moving = (tile, (r0, c0), (r1, c1), t) draws one tile part-way."""
        self.canvas.delete("all")
        n = board.size()
        cell = SIZE / n
        for tile, (row, col) in positions(board).items():
            if tile == 0:
                continue
            color = TILE_OK if (row, col) == divmod(tile - 1, n) else TILE
            if moving and moving[0] == tile:
                (r0, c0), (r1, c1), t = moving[1:]
                row, col = r0 + (r1 - r0) * t, c0 + (c1 - c0) * t
                color = TILE_MOVING
            x, y = col * cell, row * cell
            self._rounded(x + GAP, y + GAP, x + cell - GAP, y + cell - GAP, cell * 0.12,
                          fill=color, outline="")
            self.canvas.create_text(x + cell / 2, y + cell / 2, text=str(tile), fill="white",
                                    font=(FONT, -int(cell * 0.38), "bold"))

    def _show_current(self):
        board = self.path[self.index]
        last = len(self.path) - 1
        self.draw(board)
        self.info.set(f"Step {self.index}/{last}     Hamming = {board.hamming()}"
                      f"     Manhattan = {board.manhattan()}")
        self._syncing = True
        self.step_scale.config(from_=0, to=max(last, 1))
        self.step_scale.set(self.index)
        self._syncing = False

    # -------------------------------------------------------------- navigation
    def _scale_moved(self, value):
        if self._syncing or self.animating:
            return
        i = min(int(float(value)), len(self.path) - 1)
        if i != self.index:
            self.index = i
            self._show_current()

    def goto(self, i):
        if self.animating or self.busy:
            return
        self.set_playing(False)
        self.index = i
        self._show_current()

    def move(self, direction):
        """Slide one tile to the next (+1) or previous (-1) board. False if not possible."""
        j = self.index + direction
        if self.animating or self.busy or not 0 <= j < len(self.path):
            return False
        a, b = self.path[self.index], self.path[j]
        pa, pb = positions(a), positions(b)
        tile = a.tile_at(*b.blank_pos())     # the tile that sat where the new blank is
        frames = max(1, (1000 // self.speed.get()) // FRAME_MS)
        self.animating = True

        def tick(k):
            self.draw(b, moving=(tile, pa[tile], pb[tile], k / frames))
            if k < frames:
                self.root.after(FRAME_MS, tick, k + 1)
            else:
                self._arrived(j)

        tick(1)
        return True

    def _arrived(self, j):
        self.animating = False
        self.index = j
        self._show_current()
        if self.playing:
            self.root.after(60, self._auto)

    def _auto(self):
        if not self.playing or self.animating:
            return
        if not self.move(1):               # reached the end
            self.set_playing(False)

    def set_playing(self, flag):
        self.playing = flag
        self.play_button.config(text="Pause" if flag else "Play")

    def toggle_play(self):
        if self.playing:
            self.set_playing(False)
            return
        if self.busy:
            return
        if self.index == len(self.path) - 1:   # at the end: start again
            self.index = 0
            self._show_current()
        self.set_playing(True)
        self._auto()

    # ----------------------------------------------------------- board sources
    def set_board(self, board):
        if self.busy or self.animating:
            return
        self.set_playing(False)
        self.board = board
        self.path = [board]
        self.index = 0
        self.summary.set("Board loaded. Press Solve.")
        self._show_current()

    def open_file(self):
        name = filedialog.askopenfilename(title="Open puzzle file",
                                          filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not name:
            return
        try:
            self.set_board(Board.from_file(name))
        except (OSError, ValueError) as error:
            messagebox.showerror("Cannot open file", str(error))

    def randomize(self):
        board = goal_board(self.board.size())
        for _ in range(100):               # random legal moves from the goal: always solvable
            board = random.choice(board.neighbors())
        self.set_board(board)

    # ------------------------------------------------------------------ solving
    def solve(self):
        if self.busy or self.animating:
            return
        self.set_playing(False)
        self.busy = True
        self.solve_button.config(state="disabled")
        self.summary.set("Solving...")
        algorithm, heuristic = self.algorithm.get(), self.heuristic.get()
        result = {}

        def work():                        # runs in a background thread so the window stays alive
            try:
                result["solver"] = Solver(self.board, algorithm, heuristic)
            except Exception as error:
                result["error"] = error

        thread = threading.Thread(target=work, daemon=True)
        thread.start()
        self.root.after(100, self._poll, thread, result, algorithm, heuristic)

    def _poll(self, thread, result, algorithm, heuristic):
        if thread.is_alive():
            self.root.after(100, self._poll, thread, result, algorithm, heuristic)
            return
        self.busy = False
        self.solve_button.config(state="normal")
        if "error" in result:
            self.summary.set("")
            messagebox.showerror("Error", str(result["error"]))
            return
        solver = result["solver"]
        if not solver.is_solvable():
            self.path = [self.board]
            self.summary.set("Unsolvable puzzle: no sequence of moves reaches the goal.")
        else:
            self.path = solver.solution()
            name = f"A* ({heuristic})" if algorithm == "astar" else algorithm.upper()
            text = (f"{name}: {solver.moves()} moves, cost {solver.tile_cost()}, "
                    f"{solver.expanded} nodes expanded.")
            if algorithm == "dfs":
                text += " DFS paths are very long: drag the slider."
            self.summary.set(text)
        self.index = 0
        self._show_current()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()

import tkinter as tk
from tkinter import messagebox

class PegGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Peg Solitaire")
        self.root.config(bg="#0A0F0D")
        self.root.geometry("500x600")
        self.root.resizable(False, False)

        # Colors
        self.BG_COLOR = "#0A0F0D"
        self.PEG_COLOR = "#00ff88"
        self.EMPTY_COLOR = "#2d2d44"
        self.SELECTED_COLOR = "#ffcc00"

        # Game variables
        self.rows = 5
        self.pegs = []
        self.selected = None

        # Create title
        title = tk.Label(
            root, text="🐍 Peg Solitaire",
            font=("Arial", 24, "bold"),
            bg=self.BG_COLOR, fg=self.PEG_COLOR
        )
        title.pack(pady=20)

        # Create canvas
        self.canvas = tk.Canvas(root, width=500, height=450, bg=self.BG_COLOR, highlightthickness=0)
        self.canvas.pack()

        # Restart button
        restart_btn = tk.Button(
            root, text="🔄 Restart Game",
            font=("Arial", 14, "bold"),
            bg="#145A32", fg="white",
            activebackground="#1E8449",
            width=20, height=2,
            command=self.reset_game
        )
        restart_btn.pack(pady=20)

        # Setup board
        self.create_board()
        self.canvas.bind("<Button-1>", self.handle_click)

    # ---------------- Setup ---------------- #
    def create_board(self):
        """Create a triangular peg layout (classic style)."""
        self.pegs.clear()
        spacing = 80
        center_x = 250
        start_y = 80

        for r in range(self.rows):
            row_pegs = []
            for c in range(r + 1):
                x = center_x - (r * spacing / 2) + c * spacing
                y = start_y + r * spacing
                peg = {
                    "x": x, "y": y,
                    "filled": True if not (r == 0 and c == 0) else False,  # center empty
                    "circle": None
                }
                row_pegs.append(peg)
            self.pegs.append(row_pegs)

        self.draw_pegs()

    # ---------------- Draw ---------------- #
    def draw_pegs(self):
        """Render all pegs on canvas."""
        self.canvas.delete("all")
        for r, row in enumerate(self.pegs):
            for c, peg in enumerate(row):
                color = self.PEG_COLOR if peg["filled"] else self.EMPTY_COLOR
                outline = "#1E8449"
                if self.selected == (r, c):
                    color = self.SELECTED_COLOR
                    outline = "#2ECC71"
                peg["circle"] = self.canvas.create_oval(
                    peg["x"] - 20, peg["y"] - 20, peg["x"] + 20, peg["y"] + 20,
                    fill=color, outline=outline, width=2
                )

    # ---------------- Interaction ---------------- #
    def handle_click(self, event):
        """Handle peg selection and movement."""
        for r, row in enumerate(self.pegs):
            for c, peg in enumerate(row):
                if ((peg["x"] - event.x)**2 + (peg["y"] - event.y)**2) <= 400:  # click within circle
                    if self.selected is None:
                        if peg["filled"]:
                            self.selected = (r, c)
                            self.draw_pegs()
                    else:
                        if self.try_move(self.selected, (r, c)):
                            self.selected = None
                            self.draw_pegs()
                            if self.check_win():
                                messagebox.showinfo("You Win!", "🎉 Only one peg left!")
                        else:
                            self.selected = None
                            self.draw_pegs()
                    return

    # ---------------- Game Logic ---------------- #
    def try_move(self, src, dst):
        """Try to move peg if valid (jump over one)."""
        sr, sc = src
        dr, dc = dst
        if not self.valid_index(sr, sc) or not self.valid_index(dr, dc):
            return False
        if not self.pegs[sr][sc]["filled"] or self.pegs[dr][dc]["filled"]:
            return False

        # Compute direction
        row_diff = dr - sr
        col_diff = dc - sc

        # Check for valid jumps
        if abs(row_diff) == 2 and abs(col_diff) == 0:
            mid = (sr + dr)//2, (sc + dc)//2
        elif abs(row_diff) == 2 and abs(col_diff) == 2:
            mid = (sr + dr)//2, (sc + dc)//2
        elif abs(row_diff) == 0 and abs(col_diff) == 2:
            mid = (sr + dr)//2, (sc + dc)//2
        else:
            return False

        if not self.valid_index(*mid):
            return False

        if self.pegs[mid[0]][mid[1]]["filled"]:
            self.pegs[sr][sc]["filled"] = False
            self.pegs[mid[0]][mid[1]]["filled"] = False
            self.pegs[dr][dc]["filled"] = True
            return True
        return False

    def valid_index(self, r, c):
        """Check if peg index exists."""
        return 0 <= r < len(self.pegs) and 0 <= c < len(self.pegs[r])

    def check_win(self):
        """Check if only one peg remains."""
        count = sum(peg["filled"] for row in self.pegs for peg in row)
        return count == 1

    # ---------------- Reset ---------------- #
    def reset_game(self):
        self.selected = None
        self.create_board()
        self.draw_pegs()


# ---------------- Run the Game ---------------- #
def peg_game():
    root = tk.Tk()
    game = PegGame(root)
    root.mainloop()

import tkinter as tk
import random
import time


class ClickADot:
    def __init__(self, root):
        self.root = root
        self.root.title("Click-a-dot")
        self.root.resizable(False, False)
        self.root.configure(bg="#000000")

        self.canvas = tk.Canvas(root, width=800, height=600, bg="#111111", highlightthickness=0)
        self.canvas.pack()

        self.score = 0
        self.time_left = 30  # total game time in seconds

        # --- Colors ---
        self.ball_color = "#00FFFF"  # cyan
        self.text_color = "#00FF00"
        self.border_color = "#444444"

        # Frame border
        self.canvas.create_rectangle(5, 5, 795, 595, outline=self.border_color, width=3)

        # --- UI Elements ---
        self.score_label = tk.Label(root, text=f"Score: {self.score}", font=("Consolas", 16, "bold"),
                                    fg=self.text_color, bg="#000000")
        self.score_label.pack()

        self.timer_label = tk.Label(root, text=f"Time Left: {self.time_left}", font=("Consolas", 16, "bold"),
                                    fg="#FFD700", bg="#000000")
        self.timer_label.pack()

        restart_btn = tk.Button(root, text="Restart", command=self.reset_game, font=("Consolas", 14),
                                bg="#222222", fg="#00FF00", activebackground="#333333", activeforeground="#00FF00")
        restart_btn.pack(pady=8)

        self.ball = None
        self.ball_size = 40
        self.game_running = True

        # Start timers
        self.spawn_ball()
        self.update_timer()

    def spawn_ball(self):
        """Randomly spawns a new ball on canvas."""
        if not self.game_running:
            return

        if self.ball:
            self.canvas.delete(self.ball)

        x = random.randint(50, 750 - self.ball_size)
        y = random.randint(50, 550 - self.ball_size)

        self.ball = self.canvas.create_oval(
            x, y, x + self.ball_size, y + self.ball_size,
            fill=self.ball_color, outline=""
        )

        # Bind click event
        self.canvas.tag_bind(self.ball, "<Button-1>", self.hit_ball)

        # Ball disappears after random short delay
        self.root.after(random.randint(700, 1200), self.spawn_ball)

    def hit_ball(self, event):
        """Triggered when ball is clicked."""
        if not self.game_running:
            return
        self.score += 1
        self.score_label.config(text=f"Score: {self.score}")
        self.canvas.delete(self.ball)
        self.ball = None

    def update_timer(self):
        """Countdown timer."""
        if not self.game_running:
            return

        if self.time_left > 0:
            self.time_left -= 1
            self.timer_label.config(text=f"Time Left: {self.time_left}")
            self.root.after(1000, self.update_timer)
        else:
            self.end_game()

    def end_game(self):
        """Stop game and display result."""
        self.game_running = False
        self.canvas.delete("all")
        self.canvas.create_text(
            400, 250,
            text="TIME'S UP!",
            fill="#FF0000",
            font=("Consolas", 40, "bold")
        )
        self.canvas.create_text(
            400, 320,
            text=f"Your Final Score: {self.score}",
            fill="#00FF00",
            font=("Consolas", 28, "bold")
        )

    def reset_game(self):
        """Restart the entire game."""
        self.canvas.delete("all")
        self.score = 0
        self.time_left = 30
        self.game_running = True

        # Recreate border
        self.canvas.create_rectangle(5, 5, 795, 595, outline=self.border_color, width=3)

        self.score_label.config(text=f"Score: {self.score}")
        self.timer_label.config(text=f"Time Left: {self.time_left}")

        self.spawn_ball()
        self.update_timer()


def click_a_dot():
    root = tk.Tk()
    game = ClickADot(root)
    root.mainloop()

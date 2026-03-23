import tkinter as tk
from tkinter import font
import time

# ── Colour palette ──────────────────────────────────────────────────────────
BG        = "#0d0d0d"
CARD      = "#1a1a1a"
BORDER    = "#2a2a2a"
NEON      = "#39ff14"
NEON_DIM  = "#27b30d"
TEXT      = "#e0e0e0"
SUBTEXT   = "#888888"
ERROR_CLR = "#ff4444"
SUCCESS   = "#39ff14"

# ── Credentials ─────────────────────────────────────────────────────────────
VALID_USER = "admin"
VALID_PASS = "1234"


class LoginApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Editor Login")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._alpha = 0.0
        self._build_fonts()
        self._build_ui()
        self._center_window(420, 560)
        self._fade_in()

    # ── Fonts ────────────────────────────────────────────────────────────────
    def _build_fonts(self):
        self.f_title   = font.Font(family="Segoe UI", size=20, weight="bold")
        self.f_sub     = font.Font(family="Segoe UI", size=9)
        self.f_label   = font.Font(family="Segoe UI", size=10)
        self.f_entry   = font.Font(family="Segoe UI", size=11)
        self.f_btn     = font.Font(family="Segoe UI", size=11, weight="bold")
        self.f_link    = font.Font(family="Segoe UI", size=9, underline=True)

    # ── Layout ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Card frame
        card = tk.Frame(self, bg=CARD, bd=0, highlightthickness=1,
                        highlightbackground=BORDER)
        card.grid(row=0, column=0, padx=40, pady=40, sticky="nsew")
        card.columnconfigure(0, weight=1)

        # ── Title ────────────────────────────────────────────────────────────
        tk.Label(card, text="⬡", font=font.Font(size=28),
                 bg=CARD, fg=NEON).grid(row=0, column=0, pady=(36, 4))

        tk.Label(card, text="Image Editor Login",
                 font=self.f_title, bg=CARD, fg=TEXT).grid(row=1, column=0)

        tk.Label(card, text="Sign in to continue",
                 font=self.f_sub, bg=CARD, fg=SUBTEXT).grid(row=2, column=0, pady=(2, 24))

        # ── Username ─────────────────────────────────────────────────────────
        self._field_label(card, "USERNAME", row=3)
        self.username_var = tk.StringVar()
        self.username_entry = self._styled_entry(card, self.username_var, row=4)

        # ── Password ─────────────────────────────────────────────────────────
        self._field_label(card, "PASSWORD", row=5)
        self.password_var = tk.StringVar()
        self.show_pass    = tk.BooleanVar(value=False)

        pass_frame = tk.Frame(card, bg=CARD)
        pass_frame.grid(row=6, column=0, sticky="ew", padx=32, pady=(0, 4))
        pass_frame.columnconfigure(0, weight=1)

        self.password_entry = self._styled_entry(pass_frame, self.password_var,
                                                  row=0, show="●", container=pass_frame)

        toggle_btn = tk.Label(pass_frame, text="Show", font=self.f_link,
                              bg=CARD, fg=SUBTEXT, cursor="hand2")
        toggle_btn.grid(row=0, column=1, padx=(6, 0))
        toggle_btn.bind("<Button-1>", lambda e: self._toggle_password(toggle_btn))

        # ── Message label ────────────────────────────────────────────────────
        self.msg_var = tk.StringVar()
        self.msg_lbl = tk.Label(card, textvariable=self.msg_var,
                                font=self.f_sub, bg=CARD, fg=ERROR_CLR,
                                wraplength=320)
        self.msg_lbl.grid(row=7, column=0, pady=(4, 0))

        # ── Login button ─────────────────────────────────────────────────────
        self.login_btn = self._neon_button(card, "LOGIN", self._on_login, row=8)

        # ── Divider ──────────────────────────────────────────────────────────
        div = tk.Frame(card, bg=BORDER, height=1)
        div.grid(row=9, column=0, sticky="ew", padx=32, pady=16)

        # ── Register button ──────────────────────────────────────────────────
        self._ghost_button(card, "CREATE AN ACCOUNT", self._on_register, row=10)

        tk.Label(card, text="", bg=CARD).grid(row=11, pady=8)   # bottom spacer

    # ── Widget helpers ───────────────────────────────────────────────────────
    def _field_label(self, parent, text, row):
        tk.Label(parent, text=text, font=self.f_label,
                 bg=CARD, fg=SUBTEXT, anchor="w").grid(
            row=row, column=0, sticky="w", padx=32, pady=(10, 2))

    def _styled_entry(self, parent, var, row, show="", container=None):
        host = container if container else parent
        e = tk.Entry(host,
                     textvariable=var,
                     show=show,
                     font=self.f_entry,
                     bg="#252525", fg=TEXT,
                     insertbackground=NEON,
                     relief="flat",
                     bd=0,
                     highlightthickness=1,
                     highlightbackground=BORDER,
                     highlightcolor=NEON)
        e.grid(row=row, column=0, sticky="ew",
               padx=(0 if container else 32), ipady=8)
        e.bind("<FocusIn>",  lambda ev, w=e: w.config(highlightbackground=NEON))
        e.bind("<FocusOut>", lambda ev, w=e: w.config(highlightbackground=BORDER))
        return e

    def _neon_button(self, parent, text, cmd, row):
        btn = tk.Button(parent, text=text, command=cmd,
                        font=self.f_btn,
                        bg=NEON, fg=BG,
                        activebackground=NEON_DIM, activeforeground=BG,
                        relief="flat", bd=0, cursor="hand2",
                        pady=10)
        btn.grid(row=row, column=0, sticky="ew", padx=32, pady=(16, 4))
        btn.bind("<Enter>", lambda e: btn.config(bg=NEON_DIM))
        btn.bind("<Leave>", lambda e: btn.config(bg=NEON))
        return btn

    def _ghost_button(self, parent, text, cmd, row):
        btn = tk.Button(parent, text=text, command=cmd,
                        font=self.f_btn,
                        bg=CARD, fg=NEON,
                        activebackground=BORDER, activeforeground=NEON,
                        relief="flat", bd=0, cursor="hand2",
                        pady=10,
                        highlightthickness=1,
                        highlightbackground=NEON,
                        highlightcolor=NEON)
        btn.grid(row=row, column=0, sticky="ew", padx=32, pady=(0, 4))
        btn.bind("<Enter>", lambda e: btn.config(bg=BORDER))
        btn.bind("<Leave>", lambda e: btn.config(bg=CARD))
        return btn

    # ── Logic ────────────────────────────────────────────────────────────────
    def _toggle_password(self, toggle_lbl):
        if self.show_pass.get():
            self.show_pass.set(False)
            self.password_entry.config(show="●")
            toggle_lbl.config(text="Show")
        else:
            self.show_pass.set(True)
            self.password_entry.config(show="")
            toggle_lbl.config(text="Hide")

    def _on_login(self):
        user = self.username_var.get().strip()
        pwd  = self.password_var.get().strip()

        if not user or not pwd:
            self._set_message("Fields cannot be empty.", ERROR_CLR)
            self._shake(self.login_btn)
            return

        if user == VALID_USER and pwd == VALID_PASS:
            self._set_message("✓  Login successful! Welcome, admin.", SUCCESS)
        else:
            self._set_message("✗  Invalid username or password.", ERROR_CLR)
            self._shake(self.login_btn)

    def _on_register(self):
        self._set_message("Registration coming soon.", SUBTEXT)

    def _set_message(self, text, color):
        self.msg_var.set(text)
        self.msg_lbl.config(fg=color)

    # ── Animations ───────────────────────────────────────────────────────────
    def _fade_in(self):
        """Gradually increase window opacity from 0 → 1."""
        self.attributes("-alpha", self._alpha)
        if self._alpha < 1.0:
            self._alpha = min(self._alpha + 0.05, 1.0)
            self.after(20, self._fade_in)

    def _shake(self, widget, count=6, delta=6):
        """Horizontal shake animation on the given widget."""
        if count == 0:
            widget.grid_configure(padx=32)
            return
        direction = delta if count % 2 == 0 else -delta
        widget.grid_configure(padx=(32 + direction, 32 - direction))
        self.after(40, lambda: self._shake(widget, count - 1, delta))

    # ── Centering ────────────────────────────────────────────────────────────
    def _center_window(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - w) // 2
        y  = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(360, 520)


if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()

import tkinter as tk
from tkinter import font, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import random
import math
import shutil
import os
import db

try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

# ── Colour palette ──────────────────────────────────────────────────────────
BG        = "#0d0d0d"
CARD      = "#1a1a1a"
BORDER    = "#2a2a2a"
NEON      = "#39ff14"
NEON_DIM  = "#27b30d"
NEON_DARK = "#0d3d05"
TEXT      = "#e0e0e0"
SUBTEXT   = "#888888"
ERROR_CLR = "#ff4444"
SUCCESS   = "#39ff14"
PREVIEW_W = 340
PREVIEW_H = 280
NUM_PARTICLES = 38


class LoginApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Background Remover")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._alpha = 0.0
        self._current_user = None
        self._orig_image   = None
        self._result_image = None
        self._history      = []
        self._particles    = []
        self._logo_pulse   = 0
        self._logo_growing = True
        self._subtitle_idx = 0
        self._subtitle_texts = [
            "Remove backgrounds instantly ✨",
            "Fast. Clean. Precise. 🎯",
            "Sign in to get started →",
        ]
        self._build_fonts()
        self._build_auth_ui()
        self._center_window(480, 660)
        self._fade_in()
        self._init_db()

    def _init_db(self):
        try:
            db.init_db()
        except Exception as e:
            self._set_message(self.login_msg_var, self.login_msg_lbl,
                              f"DB error: {e}", ERROR_CLR)

    def _build_fonts(self):
        self.f_title      = font.Font(family="Segoe UI", size=22, weight="bold")
        self.f_sub        = font.Font(family="Segoe UI", size=9)
        self.f_label      = font.Font(family="Segoe UI", size=10, weight="bold")
        self.f_entry      = font.Font(family="Segoe UI", size=11)
        self.f_btn        = font.Font(family="Segoe UI", size=11, weight="bold")
        self.f_link       = font.Font(family="Segoe UI", size=9, underline=True)
        self.f_dash_title = font.Font(family="Segoe UI", size=18, weight="bold")
        self.f_dash_sub   = font.Font(family="Segoe UI", size=10)
        self.f_card_title = font.Font(family="Segoe UI", size=12, weight="bold")
        self.f_logo       = font.Font(family="Segoe UI", size=18, weight="bold")
        self.f_subtitle   = font.Font(family="Segoe UI", size=10)

    # ════════════════════════════════════════════════════════════════════════
    # AUTH UI
    # ════════════════════════════════════════════════════════════════════════
    def _build_auth_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.auth_root = tk.Frame(self, bg=BG)
        self.auth_root.grid(row=0, column=0, sticky="nsew")
        self.auth_root.columnconfigure(0, weight=1)
        self.auth_root.rowconfigure(0, weight=1)

        self.bg_canvas = tk.Canvas(self.auth_root, bg=BG, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        self.card_frame = tk.Frame(self.auth_root, bg=CARD, bd=0,
                                   highlightthickness=1, highlightbackground=NEON_DIM)
        self.card_frame.columnconfigure(0, weight=1)
        self.after(50, self._place_card)

        self.login_frame  = tk.Frame(self.card_frame, bg=CARD)
        self.signup_frame = tk.Frame(self.card_frame, bg=CARD)
        for f in (self.login_frame, self.signup_frame):
            f.grid(row=0, column=0, sticky="nsew")
            f.columnconfigure(0, weight=1)

        self._build_login_frame()
        self._build_signup_frame()
        self.login_frame.tkraise()

        self.after(100, self._init_particles)
        self.auth_root.bind("<Configure>", self._on_auth_resize)

    def _place_card(self):
        self.auth_root.update_idletasks()
        w = self.auth_root.winfo_width()  or 480
        h = self.auth_root.winfo_height() or 660
        cw, ch = 380, min(h - 60, 600)
        x = (w - cw) // 2
        y = (h - ch) // 2
        self.card_frame.place(x=x, y=y, width=cw, height=ch)

    def _on_auth_resize(self, event):
        self._place_card()

    def _init_particles(self):
        w = self.bg_canvas.winfo_width()  or 480
        h = self.bg_canvas.winfo_height() or 660
        self._particles = []
        for _ in range(NUM_PARTICLES):
            self._particles.append({
                "x": random.uniform(0, w),
                "y": random.uniform(0, h),
                "r": random.uniform(1.5, 4),
                "vx": random.uniform(-0.4, 0.4),
                "vy": random.uniform(-0.6, -0.1),
                "alpha": random.uniform(0.3, 1.0),
                "fade": random.choice([-1, 1]) * random.uniform(0.005, 0.015),
            })
        self._animate_particles()
        self._animate_logo_pulse()
        self._animate_subtitle()

    def _animate_particles(self):
        c = self.bg_canvas
        c.delete("particle")
        w = c.winfo_width()  or 480
        h = c.winfo_height() or 660
        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["alpha"] += p["fade"]
            if p["alpha"] <= 0.1 or p["alpha"] >= 1.0:
                p["fade"] *= -1
            if p["y"] < -10:
                p["y"] = h + 5
                p["x"] = random.uniform(0, w)
            if p["x"] < -10 or p["x"] > w + 10:
                p["x"] = random.uniform(0, w)
            r = p["r"]
            x, y = p["x"], p["y"]
            intensity = int(p["alpha"] * 255)
            col = f"#{0:02x}{intensity:02x}{0:02x}"
            c.create_oval(x-r, y-r, x+r, y+r, fill=col, outline="", tags="particle")
            c.create_oval(x-r*2.5, y-r*2.5, x+r*2.5, y+r*2.5,
                          outline=col, width=1, tags="particle")
        for gx in range(0, w, 60):
            c.create_line(gx, 0, gx, h, fill="#1a1a1a", width=1, tags="particle")
        for gy in range(0, h, 60):
            c.create_line(0, gy, w, gy, fill="#1a1a1a", width=1, tags="particle")
        self.after(30, self._animate_particles)

    def _animate_logo_pulse(self):
        if not hasattr(self, "_logo_lbl"):
            self.after(100, self._animate_logo_pulse)
            return
        step = 0.04
        if self._logo_growing:
            self._logo_pulse += step
            if self._logo_pulse >= 1.0:
                self._logo_growing = False
        else:
            self._logo_pulse -= step
            if self._logo_pulse <= 0.0:
                self._logo_growing = True
        t = (math.sin(self._logo_pulse * math.pi) + 1) / 2
        r = int(0x27 + (0x39 - 0x27) * t)
        g = int(0xb3 + (0xff - 0xb3) * t)
        b = int(0x0d + (0x14 - 0x0d) * t)
        self._logo_lbl.config(fg=f"#{r:02x}{g:02x}{b:02x}")
        self.after(40, self._animate_logo_pulse)

    def _animate_subtitle(self):
        if not hasattr(self, "_subtitle_lbl"):
            self.after(200, self._animate_subtitle)
            return
        self._subtitle_idx = (self._subtitle_idx + 1) % len(self._subtitle_texts)
        self._type_text(self._subtitle_texts[self._subtitle_idx], 0)

    def _type_text(self, text, idx):
        if not hasattr(self, "_subtitle_lbl"):
            return
        if idx <= len(text):
            self._subtitle_lbl.config(text=text[:idx])
            self.after(45, self._type_text, text, idx + 1)
        else:
            self.after(2800, self._animate_subtitle)

    def _build_login_frame(self):
        p = self.login_frame
        tk.Frame(p, bg=NEON, height=3).grid(row=0, column=0, sticky="ew")
        self._logo_lbl = tk.Label(p, text="⬡ Image Background Remover",
                                   font=self.f_logo, bg=CARD, fg=NEON)
        self._logo_lbl.grid(row=1, column=0, pady=(28, 2))
        self._subtitle_lbl = tk.Label(p, text="", font=self.f_subtitle,
                                       bg=CARD, fg=NEON_DIM)
        self._subtitle_lbl.grid(row=2, column=0, pady=(0, 6))
        tk.Label(p, text="Sign in to your account", font=self.f_sub,
                 bg=CARD, fg=SUBTEXT).grid(row=3, column=0, pady=(0, 20))
        self._divider(p, row=4)
        self._field_label(p, "👤  USERNAME", row=5)
        self.login_user_var = tk.StringVar()
        self._styled_entry(p, self.login_user_var, row=6)
        self._field_label(p, "🔒  PASSWORD", row=7)
        self.login_pass_var  = tk.StringVar()
        self.show_login_pass = tk.BooleanVar(value=False)
        pf = tk.Frame(p, bg=CARD)
        pf.grid(row=8, column=0, sticky="ew", padx=32, pady=(0, 4))
        pf.columnconfigure(0, weight=1)
        self.login_pass_entry = self._styled_entry(pf, self.login_pass_var, row=0, show="●", container=pf)
        tog = tk.Label(pf, text="👁", font=self.f_link, bg=CARD, fg=SUBTEXT, cursor="hand2")
        tog.grid(row=0, column=1, padx=(6, 0))
        tog.bind("<Button-1>", lambda e: self._toggle_pass(tog, self.login_pass_entry, self.show_login_pass))
        self.login_msg_var = tk.StringVar()
        self.login_msg_lbl = tk.Label(p, textvariable=self.login_msg_var,
                                      font=self.f_sub, bg=CARD, fg=ERROR_CLR, wraplength=340)
        self.login_msg_lbl.grid(row=9, column=0, pady=(4, 0))
        self.login_btn = self._neon_button(p, "✦  LOGIN", self._on_login, row=10)
        self._divider(p, row=11)
        self._ghost_button(p, "CREATE AN ACCOUNT →", lambda: self._switch_to("signup"), row=12)
        tk.Label(p, text="", bg=CARD).grid(row=13, pady=6)

    def _build_signup_frame(self):
        p = self.signup_frame
        tk.Frame(p, bg=NEON, height=3).grid(row=0, column=0, sticky="ew")
        tk.Label(p, text="⬡ Image Background Remover", font=self.f_logo,
                 bg=CARD, fg=NEON).grid(row=1, column=0, pady=(28, 2))
        tk.Label(p, text="Create your account", font=self.f_subtitle,
                 bg=CARD, fg=NEON_DIM).grid(row=2, column=0, pady=(0, 6))
        tk.Label(p, text="Fill in the details below", font=self.f_sub,
                 bg=CARD, fg=SUBTEXT).grid(row=3, column=0, pady=(0, 20))
        self._divider(p, row=4)
        self._field_label(p, "👤  USERNAME", row=5)
        self.signup_user_var = tk.StringVar()
        self._styled_entry(p, self.signup_user_var, row=6)
        self._field_label(p, "🔒  PASSWORD", row=7)
        self.signup_pass_var  = tk.StringVar()
        self.show_signup_pass = tk.BooleanVar(value=False)
        pf = tk.Frame(p, bg=CARD)
        pf.grid(row=8, column=0, sticky="ew", padx=32, pady=(0, 4))
        pf.columnconfigure(0, weight=1)
        self.signup_pass_entry = self._styled_entry(pf, self.signup_pass_var, row=0, show="●", container=pf)
        tog = tk.Label(pf, text="👁", font=self.f_link, bg=CARD, fg=SUBTEXT, cursor="hand2")
        tog.grid(row=0, column=1, padx=(6, 0))
        tog.bind("<Button-1>", lambda e: self._toggle_pass(tog, self.signup_pass_entry, self.show_signup_pass))
        self.signup_msg_var = tk.StringVar()
        self.signup_msg_lbl = tk.Label(p, textvariable=self.signup_msg_var,
                                       font=self.f_sub, bg=CARD, fg=ERROR_CLR, wraplength=340)
        self.signup_msg_lbl.grid(row=9, column=0, pady=(4, 0))
        self.signup_btn = self._neon_button(p, "✦  SIGN UP", self._on_signup, row=10)
        self._divider(p, row=11)
        self._ghost_button(p, "← BACK TO LOGIN", lambda: self._switch_to("login"), row=12)
        tk.Label(p, text="", bg=CARD).grid(row=13, pady=6)

    def _divider(self, parent, row):
        tk.Frame(parent, bg=BORDER, height=1).grid(
            row=row, column=0, sticky="ew", padx=32, pady=10)


    # ════════════════════════════════════════════════════════════════════════
    # DASHBOARD
    # ════════════════════════════════════════════════════════════════════════
    def _show_dashboard(self, username):
        self._current_user = username
        self.auth_root.grid_remove()
        self._center_window(980, 680)
        self.minsize(800, 560)
        if not hasattr(self, "dash_root"):
            self._build_dashboard()
        else:
            self.dash_greeting.config(text=f"Welcome back, {username} 👋")
        self.dash_root.grid(row=0, column=0, sticky="nsew")

    def _build_dashboard(self):
        self.dash_root = tk.Frame(self, bg=BG)
        self.dash_root.grid(row=0, column=0, sticky="nsew")
        self.dash_root.columnconfigure(0, weight=1)
        self.dash_root.rowconfigure(1, weight=1)

        nav = tk.Frame(self.dash_root, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        nav.grid(row=0, column=0, sticky="ew")
        nav.columnconfigure(1, weight=1)
        tk.Label(nav, text="⬡  Image Background Remover",
                 font=self.f_dash_title, bg=CARD, fg=NEON, padx=20, pady=12).grid(row=0, column=0, sticky="w")
        self.dash_greeting = tk.Label(nav, text=f"Welcome back, {self._current_user} 👋",
                                      font=self.f_dash_sub, bg=CARD, fg=SUBTEXT, padx=20)
        self.dash_greeting.grid(row=0, column=1, sticky="e")
        lb = tk.Button(nav, text="Logout", font=self.f_dash_sub, bg=CARD, fg=NEON,
                       activebackground=BORDER, activeforeground=NEON,
                       relief="flat", bd=0, cursor="hand2", padx=20, pady=12,
                       highlightthickness=0, command=self._on_logout)
        lb.grid(row=0, column=2, sticky="e")
        lb.bind("<Enter>", lambda e: lb.config(bg=BORDER))
        lb.bind("<Leave>", lambda e: lb.config(bg=CARD))

        body = tk.Frame(self.dash_root, bg=BG)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_sidebar(body)
        self._build_editor(body)
        self._dash_body = body

        self.status_var = tk.StringVar(value="Ready — select an image to get started.")
        tk.Label(self.dash_root, textvariable=self.status_var,
                 font=self.f_sub, bg=CARD, fg=SUBTEXT,
                 anchor="w", padx=16, pady=5,
                 highlightthickness=1, highlightbackground=BORDER
                 ).grid(row=2, column=0, sticky="ew")

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=CARD, width=200,
                      highlightthickness=1, highlightbackground=BORDER)
        sb.grid(row=0, column=0, sticky="ns")
        sb.pack_propagate(False)
        sb.columnconfigure(0, weight=1)
        tk.Label(sb, text="Tools", font=self.f_card_title,
                 bg=CARD, fg=TEXT, anchor="w", padx=16, pady=16).pack(fill="x")
        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x")
        tools = [
            ("🖼️  Remove BG",  self._on_remove_bg),
            ("📁  Batch",       self._on_batch),
            ("🕓  History",     self._on_history),
        ]
        for label, cmd in tools:
            b = tk.Button(sb, text=label, command=cmd,
                          font=self.f_dash_sub, bg=CARD, fg=TEXT,
                          activebackground=BORDER, activeforeground=NEON,
                          relief="flat", bd=0, cursor="hand2",
                          anchor="w", padx=16, pady=12)
            b.pack(fill="x")
            b.bind("<Enter>", lambda e, w=b: w.config(bg=BORDER, fg=NEON))
            b.bind("<Leave>", lambda e, w=b: w.config(bg=CARD, fg=TEXT))

    def _build_editor(self, parent):
        self._editor_frame = tk.Frame(parent, bg=BG)
        ed = self._editor_frame
        ed.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        ed.columnconfigure((0, 1), weight=1)
        ed.rowconfigure(1, weight=1)

        tk.Label(ed, text="Original", font=self.f_card_title,
                 bg=BG, fg=SUBTEXT).grid(row=0, column=0, pady=(0, 6))
        tk.Label(ed, text="Result", font=self.f_card_title,
                 bg=BG, fg=SUBTEXT).grid(row=0, column=1, pady=(0, 6))

        self.canvas_orig = tk.Canvas(ed, bg=CARD, bd=0,
                                     highlightthickness=1, highlightbackground=BORDER,
                                     width=PREVIEW_W, height=PREVIEW_H)
        self.canvas_orig.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        self.canvas_result = tk.Canvas(ed, bg=CARD, bd=0,
                                       highlightthickness=1, highlightbackground=BORDER,
                                       width=PREVIEW_W, height=PREVIEW_H)
        self.canvas_result.grid(row=1, column=1, sticky="nsew", padx=(10, 0))

        self._draw_placeholder(self.canvas_orig,  "Click 'Remove BG' or drop image")
        self._draw_placeholder(self.canvas_result, "Result will appear here")

        btn_row = tk.Frame(ed, bg=BG)
        btn_row.grid(row=2, column=0, columnspan=2, pady=(14, 0), sticky="ew")
        btn_row.columnconfigure((0, 1, 2), weight=1)

        self.open_btn    = self._neon_btn_small(btn_row, "📂  Open Image", self._on_remove_bg, col=0)
        self.process_btn = self._neon_btn_small(btn_row, "✨  Remove Background", self._run_remove_bg, col=1)
        self.save_btn    = self._neon_btn_small(btn_row, "💾  Save Result", self._on_save, col=2)
        self.process_btn.config(state="disabled")
        self.save_btn.config(state="disabled")

        self.progress_frame = tk.Frame(ed, bg=BG)
        self.progress_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.progress_frame.columnconfigure(0, weight=1)
        self.progress_bar_bg = tk.Frame(self.progress_frame, bg=BORDER, height=4)
        self.progress_bar_bg.grid(row=0, column=0, sticky="ew")
        self.progress_bar_fill = tk.Frame(self.progress_bar_bg, bg=NEON, height=4, width=0)
        self.progress_bar_fill.place(x=0, y=0, relheight=1.0, relwidth=0)
        self.progress_frame.grid_remove()

    def _show_editor_panel(self):
        if hasattr(self, "_batch_frame") and self._batch_frame.winfo_exists():
            self._batch_frame.grid_remove()
        if hasattr(self, "_history_frame") and self._history_frame.winfo_exists():
            self._history_frame.grid_remove()
        self._editor_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    # ════════════════════════════════════════════════════════════════════════
    # BACKGROUND REMOVAL LOGIC
    # ════════════════════════════════════════════════════════════════════════
    def _on_remove_bg(self):
        self._show_editor_panel()
        if not REMBG_AVAILABLE:
            messagebox.showerror("Missing library",
                                 "rembg is not installed.\n\nRun:\n  pip install rembg pillow",
                                 parent=self)
            return
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.bmp")])
        if not path:
            return
        self._orig_path    = path
        self._result_image = None
        self._orig_image   = Image.open(path).convert("RGBA")
        self._show_preview(self.canvas_orig, self._orig_image)
        self._draw_placeholder(self.canvas_result, "Click 'Remove Background'")
        self.process_btn.config(state="normal")
        self.save_btn.config(state="disabled")
        self.status_var.set(f"Loaded: {os.path.basename(path)}  ({self._orig_image.width}×{self._orig_image.height})")

    def _run_remove_bg(self):
        if self._orig_image is None:
            return
        self.process_btn.config(state="disabled")
        self.open_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        self.status_var.set("Removing background…  please wait")
        self.progress_frame.grid()
        self._animate_progress(0)
        threading.Thread(target=self._bg_remove_thread, daemon=True).start()

    def _bg_remove_thread(self):
        try:
            result = rembg_remove(self._orig_image)
            self.after(0, self._on_remove_done, result)
        except Exception as e:
            self.after(0, self._on_remove_error, str(e))

    def _on_remove_done(self, result_img):
        self._result_image = result_img
        self._stop_progress = True
        self.progress_bar_fill.place(relwidth=1.0)
        self.after(400, self.progress_frame.grid_remove)
        self._show_preview(self.canvas_result, result_img, checkerboard=True)
        self.process_btn.config(state="normal")
        self.open_btn.config(state="normal")
        self.save_btn.config(state="normal")
        name = os.path.basename(self._orig_path)
        self.status_var.set(f"✓  Background removed: {name}")
        self._history.append((name, None))
        db.add_history(self._current_user, self._orig_path, None)

    def _on_remove_error(self, err):
        self._stop_progress = True
        self.progress_frame.grid_remove()
        self.process_btn.config(state="normal")
        self.open_btn.config(state="normal")
        self.status_var.set(f"✗  Error: {err}")
        messagebox.showerror("Error", f"Background removal failed:\n{err}", parent=self)

    def _on_save(self):
        if self._result_image is None:
            return
        default = os.path.splitext(os.path.basename(self._orig_path))[0] + "_nobg.png"
        out = filedialog.asksaveasfilename(
            title="Save Result",
            initialfile=default,
            defaultextension=".png",
            filetypes=[("PNG (transparent)", "*.png"), ("All files", "*.*")])
        if not out:
            return
        self._result_image.save(out)
        if self._history:
            name, _ = self._history[-1]
            self._history[-1] = (name, out)
        self.status_var.set(f"✓  Saved: {out}")
        db.add_history(self._current_user, getattr(self, "_orig_path", ""), out)


    # ════════════════════════════════════════════════════════════════════════
    # BATCH PROCESSING
    # ════════════════════════════════════════════════════════════════════════
    def _on_batch(self):
        if not REMBG_AVAILABLE:
            messagebox.showerror("Missing library",
                                 "rembg is not installed.\n\nRun:\n  pip install rembg pillow",
                                 parent=self)
            return
        paths = filedialog.askopenfilenames(
            title="Select Images for Batch (max 5)",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.bmp")])
        if not paths:
            return
        if len(paths) > 5:
            messagebox.showwarning("Too many images",
                                   f"Batch mode supports a maximum of 5 images.\nYou selected {len(paths)}.",
                                   parent=self)
            return
        self._show_batch_panel(list(paths))

    def _show_batch_panel(self, paths):
        self._editor_frame.grid_remove()
        if hasattr(self, "_history_frame") and self._history_frame.winfo_exists():
            self._history_frame.grid_remove()
        if hasattr(self, "_batch_frame") and self._batch_frame.winfo_exists():
            self._batch_frame.destroy()

        n = len(paths)
        THUMB = 160
        self._batch_thumb_refs = []

        self._batch_frame = tk.Frame(self._dash_body, bg=BG)
        self._batch_frame.grid(row=0, column=1, sticky="nsew")
        self._batch_frame.columnconfigure(0, weight=1)
        self._batch_frame.rowconfigure(2, weight=1)

        # Top bar
        top = tk.Frame(self._batch_frame, bg=CARD,
                       highlightthickness=1, highlightbackground=BORDER)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)
        tk.Label(top, text=f"📁  Batch — {n} image{'s' if n>1 else ''}",
                 font=self.f_card_title, bg=CARD, fg=NEON,
                 padx=16, pady=10).grid(row=0, column=0, sticky="w")
        self._batch_status_var = tk.StringVar(value="Click 'Process All' to start.")
        tk.Label(top, textvariable=self._batch_status_var,
                 font=self.f_sub, bg=CARD, fg=SUBTEXT,
                 padx=10).grid(row=0, column=1, sticky="w")
        tk.Button(top, text="✕  Back", font=self.f_sub, bg=CARD, fg=SUBTEXT,
                  relief="flat", bd=0, cursor="hand2", padx=16, pady=10,
                  command=self._show_editor_panel).grid(row=0, column=2, sticky="e")

        # Progress bar
        pb_bg = tk.Frame(self._batch_frame, bg=BORDER, height=3)
        pb_bg.grid(row=1, column=0, sticky="ew")
        self._batch_pb = tk.Frame(pb_bg, bg=NEON, height=3)
        self._batch_pb.place(x=0, y=0, relheight=1.0, relwidth=0)

        # Scrollable content
        outer = tk.Frame(self._batch_frame, bg=BG)
        outer.grid(row=2, column=0, sticky="nsew", padx=12, pady=8)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        cv = tk.Canvas(outer, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(outer, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        cv.grid(row=0, column=0, sticky="nsew")

        inner = tk.Frame(cv, bg=BG)
        win_id = cv.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfig(win_id, width=e.width))

        col_w = THUMB + 24

        # Column headers
        hdr = tk.Frame(inner, bg=BG)
        hdr.pack(fill="x", pady=(4, 2))
        tk.Label(hdr, text="", bg=BG, width=5).pack(side="left")
        for i in range(n):
            tk.Label(hdr, text=f"Image {i+1}", font=self.f_sub,
                     bg=BG, fg=SUBTEXT, width=col_w//7).pack(side="left", padx=4)

        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=2)

        # INPUT ROW
        in_row = tk.Frame(inner, bg=BG)
        in_row.pack(fill="x", pady=6)
        tk.Label(in_row, text="IN", font=self.f_label,
                 bg=BG, fg=NEON_DIM, width=5).pack(side="left", padx=(4, 0))
        for fpath in paths:
            cell = tk.Frame(in_row, bg=CARD, highlightthickness=1,
                            highlightbackground=BORDER, width=col_w, height=THUMB+36)
            cell.pack(side="left", padx=4)
            cell.pack_propagate(False)
            try:
                img = Image.open(fpath).convert("RGBA")
                t = img.copy(); t.thumbnail((THUMB, THUMB), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(t)
                self._batch_thumb_refs.append(tk_img)
                tk.Label(cell, image=tk_img, bg=CARD).pack(pady=(6, 2))
            except Exception:
                tk.Label(cell, text="⚠", bg=CARD, fg=ERROR_CLR).pack(expand=True)
            tk.Label(cell, text=os.path.basename(fpath), font=self.f_sub,
                     bg=CARD, fg=SUBTEXT, wraplength=col_w-8).pack()

        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=2)

        # OUTPUT ROW
        out_row = tk.Frame(inner, bg=BG)
        out_row.pack(fill="x", pady=6)
        tk.Label(out_row, text="OUT", font=self.f_label,
                 bg=BG, fg=NEON_DIM, width=5).pack(side="left", padx=(4, 0))

        output_cells = []
        for i in range(n):
            cell = tk.Frame(out_row, bg=CARD, highlightthickness=1,
                            highlightbackground=BORDER, width=col_w, height=THUMB+60)
            cell.pack(side="left", padx=4)
            cell.pack_propagate(False)
            lbl = tk.Label(cell, text="⏳ Pending", font=self.f_sub, bg=CARD, fg=SUBTEXT)
            lbl.pack(expand=True)
            output_cells.append((cell, lbl))

        # Bottom buttons
        tk.Frame(self._batch_frame, bg=BORDER, height=1).grid(row=3, column=0, sticky="ew")
        btn_row = tk.Frame(self._batch_frame, bg=BG)
        btn_row.grid(row=4, column=0, sticky="ew", padx=16, pady=10)

        process_btn = tk.Button(btn_row, text="✨  Process All",
                                font=self.f_btn, bg=NEON, fg=BG,
                                activebackground=NEON_DIM, relief="flat",
                                bd=0, cursor="hand2", padx=20, pady=8)
        process_btn.pack(side="left", padx=(0, 10))

        def _start():
            process_btn.config(state="disabled")
            self._batch_status_var.set("Processing…")
            threading.Thread(
                target=self._batch_panel_thread,
                args=(paths, output_cells, THUMB),
                daemon=True
            ).start()

        process_btn.config(command=_start)

    def _batch_panel_thread(self, paths, output_cells, THUMB):
        total = len(paths)
        out_dir = os.path.join(os.path.dirname(paths[0]), "nobg_output")
        os.makedirs(out_dir, exist_ok=True)
        for i, fpath in enumerate(paths):
            fname = os.path.basename(fpath)
            cell, lbl = output_cells[i]
            self.after(0, lbl.config, {"text": "⚙ Processing…", "fg": NEON_DIM})
            try:
                img = Image.open(fpath).convert("RGBA")
                result = rembg_remove(img)
                out_name = os.path.splitext(fname)[0] + "_nobg.png"
                out_path = os.path.join(out_dir, out_name)
                result.save(out_path)
                self._history.append((fname, out_path))
                db.add_history(self._current_user, fpath, out_path)
                progress = (i + 1) / total
                self.after(0, lambda p=progress: self._batch_pb.place(relwidth=p))
                self.after(0, self._batch_status_var.set, f"Done {i+1}/{total} — {fname}")
                self.after(0, self._update_output_cell, cell, lbl, result, out_path, THUMB)
            except Exception as e:
                self.after(0, lbl.config, {"text": "✗ Error", "fg": ERROR_CLR})
        self.after(0, self._batch_status_var.set,
                   f"✓  All {total} images processed — saved to nobg_output/")
        self.after(0, self.status_var.set, f"✓  Batch complete — {total} images saved.")

    def _update_output_cell(self, cell, lbl, result_img, out_path, THUMB):
        for w in cell.winfo_children():
            w.destroy()
        checker = self._make_checker(THUMB, THUMB)
        thumb = result_img.copy()
        thumb.thumbnail((THUMB, THUMB), Image.LANCZOS)
        checker.paste(thumb, ((THUMB - thumb.width)//2, (THUMB - thumb.height)//2),
                      mask=thumb.split()[3])
        tk_img = ImageTk.PhotoImage(checker)
        self._batch_thumb_refs.append(tk_img)
        tk.Label(cell, image=tk_img, bg=CARD).pack(pady=(6, 2))
        tk.Label(cell, text=os.path.basename(out_path), font=self.f_sub,
                 bg=CARD, fg=SUBTEXT, wraplength=THUMB).pack()

        def _download(path=out_path, name=os.path.basename(out_path)):
            dest = filedialog.asksaveasfilename(
                title="Save Image", initialfile=name,
                defaultextension=".png", filetypes=[("PNG", "*.png")])
            if dest:
                shutil.copy2(path, dest)
                self.status_var.set(f"✓  Saved: {dest}")

        tk.Button(cell, text="💾 Download", command=_download,
                  font=self.f_sub, bg=NEON, fg=BG,
                  activebackground=NEON_DIM, relief="flat",
                  bd=0, cursor="hand2", pady=4).pack(fill="x", padx=6, pady=(2, 6))


    # ════════════════════════════════════════════════════════════════════════
    # HISTORY
    # ════════════════════════════════════════════════════════════════════════
    def _on_history(self):
        self._show_editor_panel()
        rows = db.get_history(self._current_user)
        if not rows:
            messagebox.showinfo("History", "No processing history yet.", parent=self)
            return

        self._editor_frame.grid_remove()
        if hasattr(self, "_history_frame") and self._history_frame.winfo_exists():
            self._history_frame.destroy()

        THUMB = 120
        self._hist_thumb_refs = []

        self._history_frame = tk.Frame(self._dash_body, bg=BG)
        self._history_frame.grid(row=0, column=1, sticky="nsew")
        self._history_frame.columnconfigure(0, weight=1)
        self._history_frame.rowconfigure(1, weight=1)

        # Top bar
        top = tk.Frame(self._history_frame, bg=CARD,
                       highlightthickness=1, highlightbackground=BORDER)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)
        tk.Label(top, text=f"🕓  History — {len(rows)} record{'s' if len(rows)>1 else ''}",
                 font=self.f_card_title, bg=CARD, fg=NEON,
                 padx=16, pady=10).grid(row=0, column=0, sticky="w")
        tk.Button(top, text="✕  Back", font=self.f_sub, bg=CARD, fg=SUBTEXT,
                  relief="flat", bd=0, cursor="hand2", padx=16, pady=10,
                  command=self._close_history_panel).grid(row=0, column=1, sticky="e")

        # Scrollable content
        outer = tk.Frame(self._history_frame, bg=BG)
        outer.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        cv = tk.Canvas(outer, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(outer, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        cv.grid(row=0, column=0, sticky="nsew")

        inner = tk.Frame(cv, bg=BG)
        win_id = cv.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfig(win_id, width=e.width))

        # Column headers
        hdr = tk.Frame(inner, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        hdr.pack(fill="x", pady=(0, 4))
        hdr.columnconfigure(1, weight=1)
        hdr.columnconfigure(2, weight=1)
        tk.Label(hdr, text="#",      font=self.f_label, bg=CARD, fg=SUBTEXT,
                 width=4, anchor="center", pady=8).grid(row=0, column=0, padx=8)
        tk.Label(hdr, text="INPUT",  font=self.f_label, bg=CARD, fg=SUBTEXT,
                 anchor="w", pady=8).grid(row=0, column=1, sticky="ew", padx=8)
        tk.Label(hdr, text="OUTPUT", font=self.f_label, bg=CARD, fg=SUBTEXT,
                 anchor="w", pady=8).grid(row=0, column=2, sticky="ew", padx=8)
        tk.Label(hdr, text="DATE",   font=self.f_label, bg=CARD, fg=SUBTEXT,
                 width=16, anchor="center", pady=8).grid(row=0, column=3, padx=8)

        for idx, (rid, inp, outp, created_at) in enumerate(rows):
            row_bg = CARD if idx % 2 == 0 else "#1f1f1f"
            rf = tk.Frame(inner, bg=row_bg,
                          highlightthickness=1, highlightbackground=BORDER)
            rf.pack(fill="x", pady=2)
            rf.columnconfigure(1, weight=1)
            rf.columnconfigure(2, weight=1)

            tk.Label(rf, text=str(idx+1), font=self.f_sub,
                     bg=row_bg, fg=SUBTEXT, width=4,
                     anchor="center", pady=6).grid(row=0, column=0, padx=8)

            in_cell = tk.Frame(rf, bg=row_bg)
            in_cell.grid(row=0, column=1, sticky="ew", padx=8, pady=6)
            self._hist_thumb(in_cell, inp, THUMB, row_bg, checkerboard=False)

            out_cell = tk.Frame(rf, bg=row_bg)
            out_cell.grid(row=0, column=2, sticky="ew", padx=8, pady=6)
            if outp and os.path.exists(outp):
                self._hist_thumb(out_cell, outp, THUMB, row_bg, checkerboard=True)
                def _dl(p=outp):
                    dest = filedialog.asksaveasfilename(
                        title="Save", initialfile=os.path.basename(p),
                        defaultextension=".png", filetypes=[("PNG", "*.png")])
                    if dest:
                        shutil.copy2(p, dest)
                        self.status_var.set(f"✓  Saved: {dest}")
                tk.Button(out_cell, text="💾", command=_dl,
                          font=self.f_sub, bg=NEON, fg=BG,
                          relief="flat", bd=0, cursor="hand2",
                          padx=6, pady=2).pack(side="left", padx=(4, 0))
            else:
                tk.Label(out_cell, text="—", font=self.f_sub,
                         bg=row_bg, fg=SUBTEXT).pack(side="left")

            dt = str(created_at)[:16] if created_at else "—"
            tk.Label(rf, text=dt, font=self.f_sub,
                     bg=row_bg, fg=SUBTEXT, width=16,
                     anchor="center").grid(row=0, column=3, padx=8)

    def _hist_thumb(self, parent, path, size, bg_col, checkerboard=False):
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((size, size), Image.LANCZOS)
            if checkerboard:
                checker = self._make_checker(img.width, img.height, size=8)
                checker.paste(img, mask=img.split()[3])
                img = checker
            tk_img = ImageTk.PhotoImage(img)
            self._hist_thumb_refs.append(tk_img)
            tk.Label(parent, image=tk_img, bg=bg_col).pack(side="left")
            tk.Label(parent, text=os.path.basename(path), font=self.f_sub,
                     bg=bg_col, fg=SUBTEXT, wraplength=160,
                     anchor="w").pack(side="left", padx=(6, 0))
        except Exception:
            tk.Label(parent, text=os.path.basename(path) if path else "—",
                     font=self.f_sub, bg=bg_col, fg=SUBTEXT).pack(side="left")

    def _close_history_panel(self):
        if hasattr(self, "_history_frame") and self._history_frame.winfo_exists():
            self._history_frame.grid_remove()
        self._editor_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    # ════════════════════════════════════════════════════════════════════════
    # PREVIEW HELPERS
    # ════════════════════════════════════════════════════════════════════════
    def _show_preview(self, canvas, img, checkerboard=False):
        canvas.update_idletasks()
        cw = canvas.winfo_width()  or PREVIEW_W
        ch = canvas.winfo_height() or PREVIEW_H
        thumb = img.copy()
        thumb.thumbnail((cw, ch), Image.LANCZOS)
        if checkerboard and thumb.mode == "RGBA":
            bg = self._make_checker(thumb.width, thumb.height)
            bg.paste(thumb, mask=thumb.split()[3])
            thumb = bg
        tk_img = ImageTk.PhotoImage(thumb)
        canvas.delete("all")
        canvas.image = tk_img
        canvas.create_image(cw//2, ch//2, anchor="center", image=tk_img)

    def _make_checker(self, w, h, size=12):
        img = Image.new("RGB", (w, h))
        c1, c2 = (200, 200, 200), (150, 150, 150)
        for row in range(0, h, size):
            for col in range(0, w, size):
                color = c1 if (row // size + col // size) % 2 == 0 else c2
                for y in range(row, min(row + size, h)):
                    for x in range(col, min(col + size, w)):
                        img.putpixel((x, y), color)
        return img

    def _draw_placeholder(self, canvas, text):
        canvas.delete("all")
        canvas.update_idletasks()
        cw = canvas.winfo_width()  or PREVIEW_W
        ch = canvas.winfo_height() or PREVIEW_H
        canvas.create_text(cw//2, ch//2, text=text,
                           fill=SUBTEXT, font=self.f_sub, justify="center")

    def _animate_progress(self, pos):
        if getattr(self, "_stop_progress", False):
            return
        pos = (pos + 0.015) % 1.0
        fill = 0.3 + 0.3 * abs(pos * 2 - 1)
        self.progress_bar_fill.place(relwidth=fill)
        self.after(30, self._animate_progress, pos)

    # ════════════════════════════════════════════════════════════════════════
    # WIDGET HELPERS
    # ════════════════════════════════════════════════════════════════════════
    def _neon_btn_small(self, parent, text, cmd, col):
        btn = tk.Button(parent, text=text, command=cmd,
                        font=self.f_dash_sub, bg=NEON, fg=BG,
                        activebackground=NEON_DIM, activeforeground=BG,
                        relief="flat", bd=0, cursor="hand2", pady=8, padx=10)
        btn.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 8, 0))
        btn.bind("<Enter>", lambda e: btn.config(bg=NEON_DIM))
        btn.bind("<Leave>", lambda e: btn.config(bg=NEON))
        return btn

    def _field_label(self, parent, text, row):
        tk.Label(parent, text=text, font=self.f_label,
                 bg=CARD, fg=NEON_DIM, anchor="w").grid(
            row=row, column=0, sticky="w", padx=32, pady=(12, 2))

    def _styled_entry(self, parent, var, row, show="", container=None):
        host = container if container else parent
        e = tk.Entry(host, textvariable=var, show=show,
                     font=self.f_entry, bg="#1f1f1f", fg=TEXT,
                     insertbackground=NEON, relief="flat", bd=0,
                     highlightthickness=2, highlightbackground=BORDER,
                     highlightcolor=NEON)
        e.grid(row=row, column=0, sticky="ew",
               padx=(0 if container else 32), ipady=10)
        e.bind("<FocusIn>",  lambda ev, w=e: w.config(highlightbackground=NEON))
        e.bind("<FocusOut>", lambda ev, w=e: w.config(highlightbackground=BORDER))
        return e

    def _neon_button(self, parent, text, cmd, row):
        btn = tk.Button(parent, text=text, command=cmd,
                        font=self.f_btn, bg=NEON, fg=BG,
                        activebackground=NEON_DIM, activeforeground=BG,
                        relief="flat", bd=0, cursor="hand2", pady=12)
        btn.grid(row=row, column=0, sticky="ew", padx=32, pady=(16, 4))
        btn.bind("<Enter>", lambda e: btn.config(bg=NEON_DIM))
        btn.bind("<Leave>", lambda e: btn.config(bg=NEON))
        return btn

    def _ghost_button(self, parent, text, cmd, row):
        btn = tk.Button(parent, text=text, command=cmd,
                        font=self.f_btn, bg=CARD, fg=NEON,
                        activebackground=NEON_DARK, activeforeground=NEON,
                        relief="flat", bd=0, cursor="hand2", pady=10,
                        highlightthickness=1, highlightbackground=NEON_DIM)
        btn.grid(row=row, column=0, sticky="ew", padx=32, pady=(0, 4))
        btn.bind("<Enter>", lambda e: btn.config(bg=NEON_DARK, highlightbackground=NEON))
        btn.bind("<Leave>", lambda e: btn.config(bg=CARD, highlightbackground=NEON_DIM))
        return btn

    def _toggle_pass(self, lbl, entry, var):
        if var.get():
            var.set(False); entry.config(show="●"); lbl.config(text="👁")
        else:
            var.set(True);  entry.config(show="");  lbl.config(text="👁\u200d🗨️")

    def _switch_to(self, view):
        if view == "signup":
            self.login_msg_var.set("")
            self.signup_user_var.set(""); self.signup_pass_var.set("")
            self.signup_msg_var.set("")
            self.signup_frame.tkraise()
        else:
            self.signup_msg_var.set("")
            self.login_user_var.set(""); self.login_pass_var.set("")
            self.login_msg_var.set("")
            self.login_frame.tkraise()

    # ════════════════════════════════════════════════════════════════════════
    # AUTH LOGIC
    # ════════════════════════════════════════════════════════════════════════
    def _on_login(self):
        user = self.login_user_var.get().strip()
        pwd  = self.login_pass_var.get().strip()
        if not user or not pwd:
            self._set_message(self.login_msg_var, self.login_msg_lbl,
                              "⚠  Fields cannot be empty.", ERROR_CLR)
            self._shake(self.login_btn); return
        try:
            if db.validate_user(user, pwd):
                self._show_dashboard(user)
            else:
                self._set_message(self.login_msg_var, self.login_msg_lbl,
                                  "✗  Invalid username or password.", ERROR_CLR)
                self._shake(self.login_btn)
        except ConnectionError as e:
            self._set_message(self.login_msg_var, self.login_msg_lbl, str(e), ERROR_CLR)

    def _on_signup(self):
        user = self.signup_user_var.get().strip()
        pwd  = self.signup_pass_var.get().strip()
        ok, msg = db.register_user(user, pwd)
        self._set_message(self.signup_msg_var, self.signup_msg_lbl,
                          msg, SUCCESS if ok else ERROR_CLR)
        if ok:
            self.after(800, lambda: self._switch_to("login"))

    def _on_logout(self):
        self._current_user = None
        self._orig_image   = None
        self._result_image = None
        if hasattr(self, 'dash_root'):
            self.dash_root.grid_remove()
        self._center_window(480, 660)
        self.minsize(360, 560)
        self.auth_root.grid(row=0, column=0, sticky="nsew")
        self._switch_to("login")

    def _set_message(self, var, lbl, text, color):
        var.set(text); lbl.config(fg=color)

    def _fade_in(self):
        self.attributes("-alpha", self._alpha)
        if self._alpha < 1.0:
            self._alpha = min(self._alpha + 0.05, 1.0)
            self.after(20, self._fade_in)

    def _shake(self, widget, count=6, delta=6):
        if count == 0:
            widget.grid_configure(padx=32); return
        d = delta if count % 2 == 0 else -delta
        widget.grid_configure(padx=(32 + d, 32 - d))
        self.after(40, lambda: self._shake(widget, count - 1, delta))

    def _center_window(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")


if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()

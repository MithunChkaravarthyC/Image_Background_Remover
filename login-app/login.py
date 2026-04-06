import tkinter as tk
from tkinter import font, filedialog, messagebox
from PIL import Image, ImageTk
import threading, random, math, shutil, os, db

try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

BG, CARD, BORDER, NEON, NEON_DIM, NEON_DARK = "#0d0d0d", "#1a1a1a", "#2a2a2a", "#39ff14", "#27b30d", "#0d3d05"
TEXT, SUBTEXT, ERROR_CLR, SUCCESS = "#e0e0e0", "#888888", "#ff4444", "#39ff14"
PREVIEW_W, PREVIEW_H, NUM_PARTICLES = 340, 280, 38

class LoginApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Background Remover"); self.configure(bg=BG); self.resizable(True, True)
        self._alpha, self._current_user, self._orig_image, self._result_image = 0.0, None, None, None
        self._history, self._particles, self._logo_pulse, self._logo_growing = [], [], 0, True
        self._subtitle_idx, self._subtitle_texts = 0, ["Remove backgrounds instantly ✨", "Fast. Clean. Precise. 🎯", "Sign in to get started →"]
        self._build_fonts(); self._build_auth_ui(); self._center_window(480, 660); self._fade_in()
        try: db.init_db()
        except Exception as e: messagebox.showerror("DB Error", str(e))

    def _build_fonts(self):
        self.f_title = font.Font(family="Segoe UI", size=22, weight="bold")
        self.f_sub = font.Font(family="Segoe UI", size=9)
        self.f_label = font.Font(family="Segoe UI", size=10, weight="bold")
        self.f_entry = font.Font(family="Segoe UI", size=11)
        self.f_btn = font.Font(family="Segoe UI", size=11, weight="bold")
        self.f_dash_title = font.Font(family="Segoe UI", size=18, weight="bold")
        self.f_dash_sub = font.Font(family="Segoe UI", size=10)
        self.f_card_title = font.Font(family="Segoe UI", size=12, weight="bold")

    def _build_auth_ui(self):
        self.columnconfigure(0, weight=1); self.rowconfigure(0, weight=1)
        self.auth_root = tk.Frame(self, bg=BG)
        self.auth_root.grid(row=0, column=0, sticky="nsew")
        self.auth_root.columnconfigure(0, weight=1); self.auth_root.rowconfigure(0, weight=1)
        self.bg_canvas = tk.Canvas(self.auth_root, bg=BG, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self.card_frame = tk.Frame(self.auth_root, bg=CARD, bd=0, highlightthickness=1, highlightbackground=NEON_DIM)
        self.card_frame.columnconfigure(0, weight=1)
        self.after(50, self._place_card)
        self.login_frame, self.signup_frame = tk.Frame(self.card_frame, bg=CARD), tk.Frame(self.card_frame, bg=CARD)
        for f in (self.login_frame, self.signup_frame):
            f.grid(row=0, column=0, sticky="nsew"); f.columnconfigure(0, weight=1)
        self._build_login_frame(); self._build_signup_frame()
        self.login_frame.tkraise()
        self.after(100, self._init_particles)
        self.auth_root.bind("<Configure>", lambda e: self._place_card())

    def _place_card(self):
        self.auth_root.update_idletasks()
        w, h = self.auth_root.winfo_width() or 480, self.auth_root.winfo_height() or 660
        cw, ch = 380, min(h - 60, 600)
        self.card_frame.place(x=(w-cw)//2, y=(h-ch)//2, width=cw, height=ch)

    def _init_particles(self):
        w, h = self.bg_canvas.winfo_width() or 480, self.bg_canvas.winfo_height() or 660
        self._particles = [{"x": random.uniform(0, w), "y": random.uniform(0, h), "r": 2.5, "vx": random.uniform(-0.4, 0.4), "vy": -0.3, "alpha": 0.6}
                          for _ in range(NUM_PARTICLES)]
        self._animate_particles(); self._animate_logo(); self._subtitle_lbl.config(text=self._subtitle_texts[0]) if hasattr(self, "_subtitle_lbl") else None

    def _animate_particles(self):
        c = self.bg_canvas; c.delete("particle")
        w, h = c.winfo_width() or 480, c.winfo_height() or 660
        for p in self._particles:
            p["x"] += p["vx"]; p["y"] += p["vy"]
            if p["y"] < -10: p["y"], p["x"] = h + 5, random.uniform(0, w)
            c.create_oval(p["x"]-2, p["y"]-2, p["x"]+2, p["y"]+2, fill="#00ff0060", outline="", tags="particle")
        self.after(40, self._animate_particles)

    def _animate_logo(self):
        if not hasattr(self, "_logo_lbl"): self.after(100, self._animate_logo); return
        self._logo_pulse += 0.04 if self._logo_growing else -0.04
        if self._logo_pulse >= 1.0 or self._logo_pulse <= 0.0: self._logo_growing = not self._logo_growing
        t = (math.sin(self._logo_pulse * math.pi) + 1) / 2
        self._logo_lbl.config(fg=f"#{int(0x27+(0x39-0x27)*t):02x}{int(0xb3+(0xff-0xb3)*t):02x}{int(0x0d+(0x14-0x0d)*t):02x}")
        self.after(50, self._animate_logo)

    def _build_login_frame(self):
        p = self.login_frame
        tk.Frame(p, bg=NEON, height=3).grid(row=0, column=0, sticky="ew")
        self._logo_lbl = tk.Label(p, text="⬡ Image Background Remover", font=self.f_title, bg=CARD, fg=NEON)
        self._logo_lbl.grid(row=1, column=0, pady=(28, 2))
        self._subtitle_lbl = tk.Label(p, text="", font=self.f_sub, bg=CARD, fg=NEON_DIM)
        self._subtitle_lbl.grid(row=2, column=0, pady=(0, 20))
        self._divider(p, 3)
        self._field_label(p, "👤  USERNAME", 4)
        self.login_user_var = tk.StringVar()
        self._styled_entry(p, self.login_user_var, 5)
        self._field_label(p, "🔒  PASSWORD", 6)
        self.login_pass_var, self.show_login_pass = tk.StringVar(), tk.BooleanVar(value=False)
        pf = tk.Frame(p, bg=CARD)
        pf.grid(row=7, column=0, sticky="ew", padx=32, pady=(0, 4)); pf.columnconfigure(0, weight=1)
        self.login_pass_entry = self._styled_entry(pf, self.login_pass_var, 0, show="●", container=pf)
        tog = tk.Label(pf, text="👁", font=self.f_sub, bg=CARD, fg=SUBTEXT, cursor="hand2")
        tog.grid(row=0, column=1, padx=(6, 0))
        tog.bind("<Button-1>", lambda e: self._toggle_pass(tog, self.login_pass_entry, self.show_login_pass))
        self.login_msg_var = tk.StringVar()
        self.login_msg_lbl = tk.Label(p, textvariable=self.login_msg_var, font=self.f_sub, bg=CARD, fg=ERROR_CLR, wraplength=340)
        self.login_msg_lbl.grid(row=8, column=0, pady=(4, 0))
        self.login_btn = self._neon_button(p, "✦  LOGIN", self._on_login, 9)
        self._divider(p, 10)
        self._ghost_button(p, "CREATE AN ACCOUNT →", lambda: self._switch_to("signup"), 11)

    def _build_signup_frame(self):
        p = self.signup_frame
        tk.Frame(p, bg=NEON, height=3).grid(row=0, column=0, sticky="ew")
        tk.Label(p, text="⬡ Image Background Remover", font=self.f_title, bg=CARD, fg=NEON).grid(row=1, column=0, pady=(28, 2))
        tk.Label(p, text="Create your account", font=self.f_sub, bg=CARD, fg=NEON_DIM).grid(row=2, column=0, pady=(0, 20))
        self._divider(p, 3)
        self._field_label(p, "👤  USERNAME", 4)
        self.signup_user_var = tk.StringVar()
        self._styled_entry(p, self.signup_user_var, 5)
        self._field_label(p, "🔒  PASSWORD", 6)
        self.signup_pass_var, self.show_signup_pass = tk.StringVar(), tk.BooleanVar(value=False)
        pf = tk.Frame(p, bg=CARD)
        pf.grid(row=7, column=0, sticky="ew", padx=32, pady=(0, 4)); pf.columnconfigure(0, weight=1)
        self.signup_pass_entry = self._styled_entry(pf, self.signup_pass_var, 0, show="●", container=pf)
        tog = tk.Label(pf, text="👁", font=self.f_sub, bg=CARD, fg=SUBTEXT, cursor="hand2")
        tog.grid(row=0, column=1, padx=(6, 0))
        tog.bind("<Button-1>", lambda e: self._toggle_pass(tog, self.signup_pass_entry, self.show_signup_pass))
        self.signup_msg_var = tk.StringVar()
        self.signup_msg_lbl = tk.Label(p, textvariable=self.signup_msg_var, font=self.f_sub, bg=CARD, fg=ERROR_CLR, wraplength=340)
        self.signup_msg_lbl.grid(row=8, column=0, pady=(4, 0))
        self.signup_btn = self._neon_button(p, "✦  SIGN UP", self._on_signup, 9)
        self._divider(p, 10)
        self._ghost_button(p, "← BACK TO LOGIN", lambda: self._switch_to("login"), 11)

    def _divider(self, parent, row):
        tk.Frame(parent, bg=BORDER, height=1).grid(row=row, column=0, sticky="ew", padx=32, pady=10)

    def _show_dashboard(self, username):
        self._current_user = username
        self.auth_root.grid_remove()
        self._center_window(980, 680); self.minsize(800, 560)
        if not hasattr(self, "dash_root"): self._build_dashboard()
        else: self.dash_greeting.config(text=f"Welcome back, {username} 👋")
        self.dash_root.grid(row=0, column=0, sticky="nsew")

    def _build_dashboard(self):
        self.dash_root = tk.Frame(self, bg=BG)
        self.dash_root.grid(row=0, column=0, sticky="nsew")
        self.dash_root.columnconfigure(0, weight=1); self.dash_root.rowconfigure(1, weight=1)
        nav = tk.Frame(self.dash_root, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        nav.grid(row=0, column=0, sticky="ew"); nav.columnconfigure(1, weight=1)
        tk.Label(nav, text="⬡  Image Background Remover", font=self.f_dash_title, bg=CARD, fg=NEON, padx=20, pady=12).grid(row=0, column=0, sticky="w")
        self.dash_greeting = tk.Label(nav, text=f"Welcome back, {self._current_user} 👋", font=self.f_dash_sub, bg=CARD, fg=SUBTEXT, padx=20)
        self.dash_greeting.grid(row=0, column=1, sticky="e")
        lb = tk.Button(nav, text="Logout", font=self.f_dash_sub, bg=CARD, fg=NEON, relief="flat", bd=0, cursor="hand2", padx=20, pady=12, command=self._on_logout)
        lb.grid(row=0, column=2, sticky="e")
        lb.bind("<Enter>", lambda e: lb.config(bg=BORDER)); lb.bind("<Leave>", lambda e: lb.config(bg=CARD))
        body = tk.Frame(self.dash_root, bg=BG)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1); body.rowconfigure(0, weight=1)
        self._build_sidebar(body); self._build_editor(body)
        self._dash_body = body
        self.status_var = tk.StringVar(value="Ready — select an image to get started.")
        tk.Label(self.dash_root, textvariable=self.status_var, font=self.f_sub, bg=CARD, fg=SUBTEXT,
                 anchor="w", padx=16, pady=5, highlightthickness=1, highlightbackground=BORDER).grid(row=2, column=0, sticky="ew")

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=CARD, width=200, highlightthickness=1, highlightbackground=BORDER)
        sb.grid(row=0, column=0, sticky="ns"); sb.pack_propagate(False)
        tk.Label(sb, text="Tools", font=self.f_card_title, bg=CARD, fg=TEXT, anchor="w", padx=16, pady=16).pack(fill="x")
        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x")
        for label, cmd in [("🖼️  Remove BG", self._on_remove_bg), ("  History", self._on_history)]:
            b = tk.Button(sb, text=label, command=cmd, font=self.f_dash_sub, bg=CARD, fg=TEXT, relief="flat", bd=0, cursor="hand2", anchor="w", padx=16, pady=12)
            b.pack(fill="x")
            b.bind("<Enter>", lambda e, w=b: w.config(bg=BORDER, fg=NEON))
            b.bind("<Leave>", lambda e, w=b: w.config(bg=CARD, fg=TEXT))

    def _build_editor(self, parent):
        self._editor_frame = tk.Frame(parent, bg=BG)
        ed = self._editor_frame
        ed.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        ed.columnconfigure((0, 1), weight=1); ed.rowconfigure(1, weight=1)
        tk.Label(ed, text="Original", font=self.f_card_title, bg=BG, fg=SUBTEXT).grid(row=0, column=0, pady=(0, 6))
        tk.Label(ed, text="Result", font=self.f_card_title, bg=BG, fg=SUBTEXT).grid(row=0, column=1, pady=(0, 6))
        self.canvas_orig = tk.Canvas(ed, bg=CARD, bd=0, highlightthickness=1, highlightbackground=BORDER, width=PREVIEW_W, height=PREVIEW_H)
        self.canvas_orig.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.canvas_result = tk.Canvas(ed, bg=CARD, bd=0, highlightthickness=1, highlightbackground=BORDER, width=PREVIEW_W, height=PREVIEW_H)
        self.canvas_result.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        self._draw_placeholder(self.canvas_orig, "Click 'Remove BG'"); self._draw_placeholder(self.canvas_result, "Result will appear here")
        btn_row = tk.Frame(ed, bg=BG)
        btn_row.grid(row=2, column=0, columnspan=2, pady=(14, 0), sticky="ew"); btn_row.columnconfigure((0, 1, 2), weight=1)
        self.open_btn = self._neon_btn_small(btn_row, "📂  Open", self._on_remove_bg, 0)
        self.process_btn = self._neon_btn_small(btn_row, "✨  Remove BG", self._run_remove_bg, 1)
        self.save_btn = self._neon_btn_small(btn_row, "💾  Save", self._on_save, 2)
        self.process_btn.config(state="disabled"); self.save_btn.config(state="disabled")
        self.progress_frame = tk.Frame(ed, bg=BG)
        self.progress_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0)); self.progress_frame.columnconfigure(0, weight=1)
        self.progress_bar_bg = tk.Frame(self.progress_frame, bg=BORDER, height=4)
        self.progress_bar_bg.grid(row=0, column=0, sticky="ew")
        self.progress_bar_fill = tk.Frame(self.progress_bar_bg, bg=NEON, height=4, width=0)
        self.progress_bar_fill.place(x=0, y=0, relheight=1.0, relwidth=0); self.progress_frame.grid_remove()

    def _show_editor_panel(self):
        if hasattr(self, "_history_frame") and self._history_frame.winfo_exists(): self._history_frame.grid_remove()
        self._editor_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    def _on_remove_bg(self):
        self._show_editor_panel()
        if not REMBG_AVAILABLE: messagebox.showerror("Missing library", "rembg is not installed.\n\nRun:\n  pip install rembg pillow", parent=self); return
        path = filedialog.askopenfilename(title="Select Image", filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.bmp")])
        if not path: return
        self._orig_path, self._result_image, self._orig_image = path, None, Image.open(path).convert("RGBA")
        self._show_preview(self.canvas_orig, self._orig_image); self._draw_placeholder(self.canvas_result, "Click 'Remove Background'")
        self.process_btn.config(state="normal"); self.save_btn.config(state="disabled")
        self.status_var.set(f"Loaded: {os.path.basename(path)}  ({self._orig_image.width}×{self._orig_image.height})")

    def _run_remove_bg(self):
        if self._orig_image is None: return
        self.process_btn.config(state="disabled"); self.open_btn.config(state="disabled"); self.save_btn.config(state="disabled")
        self.status_var.set("Removing background…"); self.progress_frame.grid(); self._animate_progress(0)
        threading.Thread(target=self._bg_remove_thread, daemon=True).start()

    def _bg_remove_thread(self):
        try: result = rembg_remove(self._orig_image); self.after(0, self._on_remove_done, result)
        except Exception as e: self.after(0, self._on_remove_error, str(e))

    def _on_remove_done(self, result_img):
        self._result_image, self._stop_progress = result_img, True
        self.progress_bar_fill.place(relwidth=1.0); self.after(400, self.progress_frame.grid_remove)
        self._show_preview(self.canvas_result, result_img, checkerboard=True)
        self.process_btn.config(state="normal"); self.open_btn.config(state="normal"); self.save_btn.config(state="normal")
        name = os.path.basename(self._orig_path); self.status_var.set(f"✓  Background removed: {name}")
        self._history.append((name, None)); db.add_history(self._current_user, self._orig_path, None)

    def _on_remove_error(self, err):
        self._stop_progress = True; self.progress_frame.grid_remove()
        self.process_btn.config(state="normal"); self.open_btn.config(state="normal"); self.status_var.set(f"✗  Error: {err}")
        messagebox.showerror("Error", f"Background removal failed:\n{err}", parent=self)

    def _on_save(self):
        if self._result_image is None: return
        default = os.path.splitext(os.path.basename(self._orig_path))[0] + "_nobg.png"
        out = filedialog.asksaveasfilename(title="Save Result", initialfile=default, defaultextension=".png", filetypes=[("PNG (transparent)", "*.png"), ("All files", "*.*")])
        if not out: return
        self._result_image.save(out)
        if self._history: name, _ = self._history[-1]; self._history[-1] = (name, out)
        self.status_var.set(f"✓  Saved: {out}"); db.add_history(self._current_user, getattr(self, "_orig_path", ""), out)

    def _on_history(self):
        rows = db.get_history(self._current_user)
        if not rows: messagebox.showinfo("History", "No processing history yet.", parent=self); return
        self._editor_frame.grid_remove()
        if hasattr(self, "_history_frame") and self._history_frame.winfo_exists(): self._history_frame.destroy()
        self._hist_thumb_refs, self._history_frame = [], tk.Frame(self._dash_body, bg=BG)
        self._history_frame.grid(row=0, column=1, sticky="nsew")
        self._history_frame.columnconfigure(0, weight=1); self._history_frame.rowconfigure(1, weight=1)
        top = tk.Frame(self._history_frame, bg=CARD)
        top.grid(row=0, column=0, sticky="ew"); top.columnconfigure(0, weight=1)
        tk.Label(top, text=f"🕓  History — {len(rows)} records", font=self.f_card_title, bg=CARD, fg=NEON, padx=16, pady=10).grid(row=0, column=0, sticky="w")
        tk.Button(top, text="✕", font=self.f_sub, bg=CARD, fg=SUBTEXT, relief="flat", bd=0, cursor="hand2", padx=16, pady=10,
                  command=self._close_history_panel).grid(row=0, column=1, sticky="e")
        content = tk.Frame(self._history_frame, bg=BG)
        content.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
        for idx, (rid, inp, outp, created_at) in enumerate(rows):
            row = tk.Frame(content, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{idx+1}.", font=self.f_sub, bg=CARD, fg=SUBTEXT, width=3).pack(side="left", padx=4)
            tk.Label(row, text=os.path.basename(inp) if inp else "—", font=self.f_sub, bg=CARD, fg=TEXT, anchor="w", width=25).pack(side="left", padx=4)
            tk.Label(row, text="→", font=self.f_sub, bg=CARD, fg=NEON_DIM).pack(side="left", padx=2)
            tk.Label(row, text=os.path.basename(outp) if outp else "—", font=self.f_sub, bg=CARD, fg=TEXT, anchor="w", width=25).pack(side="left", padx=4)
            tk.Label(row, text=str(created_at)[:16] if created_at else "—", font=self.f_sub, bg=CARD, fg=SUBTEXT, width=16).pack(side="left", padx=4)
            if outp and os.path.exists(outp):
                def _dl(p=outp):
                    dest = filedialog.asksaveasfilename(title="Save", initialfile=os.path.basename(p), defaultextension=".png", filetypes=[("PNG", "*.png")])
                    if dest: shutil.copy2(p, dest); self.status_var.set(f"✓  Saved: {dest}")
                tk.Button(row, text="💾", command=_dl, font=self.f_sub, bg=NEON, fg=BG, relief="flat", bd=0, cursor="hand2", padx=6, pady=2).pack(side="left", padx=4)

    def _close_history_panel(self):
        if hasattr(self, "_history_frame") and self._history_frame.winfo_exists(): self._history_frame.grid_remove()
        self._editor_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    def _show_preview(self, canvas, img, checkerboard=False):
        canvas.update_idletasks()
        cw, ch = canvas.winfo_width() or PREVIEW_W, canvas.winfo_height() or PREVIEW_H
        thumb = img.copy(); thumb.thumbnail((cw, ch), Image.LANCZOS)
        if checkerboard and thumb.mode == "RGBA": bg = self._make_checker(thumb.width, thumb.height); bg.paste(thumb, mask=thumb.split()[3]); thumb = bg
        tk_img = ImageTk.PhotoImage(thumb)
        canvas.delete("all"); canvas.image = tk_img; canvas.create_image(cw//2, ch//2, anchor="center", image=tk_img)

    def _make_checker(self, w, h, size=12):
        img = Image.new("RGB", (w, h)); c1, c2 = (200, 200, 200), (150, 150, 150)
        for row in range(0, h, size):
            for col in range(0, w, size):
                color = c1 if (row // size + col // size) % 2 == 0 else c2
                for y in range(row, min(row + size, h)):
                    for x in range(col, min(col + size, w)): img.putpixel((x, y), color)
        return img

    def _draw_placeholder(self, canvas, text):
        canvas.delete("all"); canvas.update_idletasks()
        cw, ch = canvas.winfo_width() or PREVIEW_W, canvas.winfo_height() or PREVIEW_H
        canvas.create_text(cw//2, ch//2, text=text, fill=SUBTEXT, font=self.f_sub, justify="center")

    def _animate_progress(self, pos):
        if getattr(self, "_stop_progress", False): return
        pos = (pos + 0.015) % 1.0; fill = 0.3 + 0.3 * abs(pos * 2 - 1)
        self.progress_bar_fill.place(relwidth=fill); self.after(30, self._animate_progress, pos)

    def _neon_btn_small(self, parent, text, cmd, col):
        btn = tk.Button(parent, text=text, command=cmd, font=self.f_dash_sub, bg=NEON, fg=BG, relief="flat", bd=0, cursor="hand2", pady=8, padx=10)
        btn.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 8, 0))
        btn.bind("<Enter>", lambda e: btn.config(bg=NEON_DIM)); btn.bind("<Leave>", lambda e: btn.config(bg=NEON))
        return btn

    def _field_label(self, parent, text, row):
        tk.Label(parent, text=text, font=self.f_label, bg=CARD, fg=NEON_DIM, anchor="w").grid(row=row, column=0, sticky="w", padx=32, pady=(12, 2))

    def _styled_entry(self, parent, var, row, show="", container=None):
        host = container if container else parent
        e = tk.Entry(host, textvariable=var, show=show, font=self.f_entry, bg="#1f1f1f", fg=TEXT, insertbackground=NEON, relief="flat", bd=0, highlightthickness=2, highlightbackground=BORDER, highlightcolor=NEON)
        e.grid(row=row, column=0, sticky="ew", padx=(0 if container else 32), ipady=10)
        e.bind("<FocusIn>", lambda ev, w=e: w.config(highlightbackground=NEON)); e.bind("<FocusOut>", lambda ev, w=e: w.config(highlightbackground=BORDER))
        return e

    def _neon_button(self, parent, text, cmd, row):
        btn = tk.Button(parent, text=text, command=cmd, font=self.f_btn, bg=NEON, fg=BG, relief="flat", bd=0, cursor="hand2", pady=12)
        btn.grid(row=row, column=0, sticky="ew", padx=32, pady=(16, 4))
        btn.bind("<Enter>", lambda e: btn.config(bg=NEON_DIM)); btn.bind("<Leave>", lambda e: btn.config(bg=NEON))
        return btn

    def _ghost_button(self, parent, text, cmd, row):
        btn = tk.Button(parent, text=text, command=cmd, font=self.f_btn, bg=CARD, fg=NEON, relief="flat", bd=0, cursor="hand2", pady=10, highlightthickness=1, highlightbackground=NEON_DIM)
        btn.grid(row=row, column=0, sticky="ew", padx=32, pady=(0, 4))
        btn.bind("<Enter>", lambda e: btn.config(bg=NEON_DARK, highlightbackground=NEON)); btn.bind("<Leave>", lambda e: btn.config(bg=CARD, highlightbackground=NEON_DIM))
        return btn

    def _toggle_pass(self, lbl, entry, var):
        if var.get(): var.set(False); entry.config(show="●"); lbl.config(text="👁")
        else: var.set(True); entry.config(show=""); lbl.config(text="👁\u200d🗨️")

    def _switch_to(self, view):
        if view == "signup": self.login_msg_var.set(""); self.signup_user_var.set(""); self.signup_pass_var.set(""); self.signup_msg_var.set(""); self.signup_frame.tkraise()
        else: self.signup_msg_var.set(""); self.login_user_var.set(""); self.login_pass_var.set(""); self.login_msg_var.set(""); self.login_frame.tkraise()

    def _on_login(self):
        user, pwd = self.login_user_var.get().strip(), self.login_pass_var.get().strip()
        if not user or not pwd: self.login_msg_var.set("⚠  Fields cannot be empty."); self.login_msg_lbl.config(fg=ERROR_CLR); self._shake(self.login_btn); return
        try:
            if db.validate_user(user, pwd): self._show_dashboard(user)
            else: self.login_msg_var.set("✗  Invalid username or password."); self.login_msg_lbl.config(fg=ERROR_CLR); self._shake(self.login_btn)
        except ConnectionError as e: self.login_msg_var.set(str(e)); self.login_msg_lbl.config(fg=ERROR_CLR)

    def _on_signup(self):
        user, pwd = self.signup_user_var.get().strip(), self.signup_pass_var.get().strip()
        ok, msg = db.register_user(user, pwd)
        self.signup_msg_var.set(msg); self.signup_msg_lbl.config(fg=SUCCESS if ok else ERROR_CLR)
        if ok: self.after(800, lambda: self._switch_to("login"))

    def _on_logout(self):
        self._current_user, self._orig_image, self._result_image = None, None, None
        if hasattr(self, 'dash_root'): self.dash_root.grid_remove()
        self._center_window(480, 660); self.minsize(360, 560)
        self.auth_root.grid(row=0, column=0, sticky="nsew"); self._switch_to("login")

    def _fade_in(self):
        self.attributes("-alpha", self._alpha)
        if self._alpha < 1.0: self._alpha = min(self._alpha + 0.05, 1.0); self.after(20, self._fade_in)

    def _shake(self, widget, count=6, delta=6):
        if count == 0: widget.grid_configure(padx=32); return
        d = delta if count % 2 == 0 else -delta
        widget.grid_configure(padx=(32 + d, 32 - d)); self.after(40, lambda: self._shake(widget, count - 1, delta))

    def _center_window(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()

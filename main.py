import tkinter as tk
import tkinter.font as tkfont
import random
import pygame
import time

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

pygame.mixer.init()
pygame.mixer.music.load("song.wav")

LYRICS = [
    (8,    "One night I was bored in bed"),
    (11.5, "And stalked you on the internet"),
    (15.5, "It's feminine intuition"),
    (18.5, "'Cuz I always had a vision of us standing like this"),
    (22.5, "All pressed up in the bathroom line"),
    (26,   "You're looking like an angel on the walls of Versailles"),
    (30,   "The most alive I've ever been"),
    (34,   "But kiss me and I might"),
]

# ---------- Outro ----------
OUTRO_DELAY   = 4.0
SONG_TITLE    = "Olivia Rodrigo — Drop Dead"
SCRIPT_CREDIT = "Script Made by Keniii (RevsCloud)"
LOGO_PATH     = "logo.png"
STAGE_GAP_MS  = 90   # jeda antar elemen saat muncul


# ---------- Font ----------
def pick_serif_font():
    try:
        probe = tk.Tk(); probe.withdraw()
        families = set(tkfont.families())
        probe.destroy()
    except Exception:
        families = set()
    for name in ("Playfair Display", "Georgia", "Palatino Linotype", "Palatino",
                 "Garamond", "Cambria", "Book Antiqua", "Times New Roman",
                 "DejaVu Serif", "Liberation Serif", "Noto Serif"):
        if name in families:
            return name
    return "Times"


SERIF_FONT = pick_serif_font()

# ---------- Kartu lirik ----------
BOX_W, BOX_H = 420, 290
SHADOW       = 6
FONT         = (SERIF_FONT, 22, "italic")
FONT_SMALL   = (SERIF_FONT, 11)

BG_COLOR     = "#FAF5EA"
FG_COLOR     = "#2A241C"
ACCENT_COLOR = "#B4884E"
BORDER_COLOR = "#DDCFAF"
SHADOW_COLOR = "#C9B99B"

RISE_SPEED          = 88
BOTTOM_SPAWN_OFFSET = 170
STACK_SPACING       = 44
Y_JITTER            = 30
SIDE_PADDING        = 40
CENTER_GAP          = 60

# ---------- Overlay ----------
OVERLAY_ALPHA         = 0.55
OVERLAY_COLOR         = "#000000"
OVERLAY_FADE_STEP     = 0.035
OVERLAY_FADE_INTERVAL = 20

# ---------- Tema Outro ----------
OUTRO_BG     = "#14110E"
OUTRO_FG     = "#FAF5EA"
OUTRO_ACCENT = "#C79A5E"


def ease_out_back(t, s=1.70158):
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


# ============================================================
#                        LYRIC CARD
# ============================================================
class LyricCard:
    def __init__(self, parent, text, x, y):
        self.win = tk.Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=SHADOW_COLOR)
        self.win.geometry(f"{BOX_W + SHADOW}x{BOX_H + SHADOW}+{int(x)}+{int(y)}")
        self.win.resizable(False, False)

        self.alpha = 0.0
        self.target_alpha = 0.97
        try:
            self.win.attributes("-alpha", self.alpha)
            self._has_alpha = True
        except tk.TclError:
            self._has_alpha = False

        card_outer = tk.Frame(self.win, bg=BORDER_COLOR,
                              width=BOX_W, height=BOX_H)
        card_outer.place(x=0, y=0)
        card_outer.pack_propagate(False)

        self.card = tk.Frame(card_outer, bg=BG_COLOR)
        self.card.pack(fill="both", expand=True, padx=1, pady=1)

        self._build_top_ornament()
        self.label = tk.Label(self.card, text="", font=FONT, bg=BG_COLOR,
                              fg=FG_COLOR, wraplength=BOX_W - 110,
                              justify="center")
        self.label.pack(expand=True, fill="both", padx=45, pady=(0, 10))
        self._build_bottom_ornament()

        self.full_text = text
        self.typewriter_index = 0
        self.typewriter()
        self._fade_in()

        self.x = x
        self.y = float(y)

    def _build_top_ornament(self):
        c = tk.Canvas(self.card, bg=BG_COLOR, height=22,
                      highlightthickness=0, bd=0)
        c.pack(fill="x", pady=(28, 6))

        def draw(_=None):
            w = c.winfo_width(); cx = w // 2
            c.delete("all")
            c.create_line(cx - 82, 11, cx - 16, 11, fill=ACCENT_COLOR)
            c.create_line(cx + 16, 11, cx + 82, 11, fill=ACCENT_COLOR)
            c.create_text(cx, 11, text="✦", fill=ACCENT_COLOR, font=FONT_SMALL)

        c.bind("<Configure>", draw)

    def _build_bottom_ornament(self):
        c = tk.Canvas(self.card, bg=BG_COLOR, height=14,
                      highlightthickness=0, bd=0)
        c.pack(fill="x", pady=(4, 24))

        def draw(_=None):
            w = c.winfo_width(); cx = w // 2
            c.delete("all")
            for dx in (-14, 0, 14):
                c.create_oval(cx + dx - 2, 5, cx + dx + 2, 9,
                              fill=ACCENT_COLOR, outline="")

        c.bind("<Configure>", draw)

    def _fade_in(self):
        if not self._has_alpha:
            return
        if self.alpha < self.target_alpha:
            self.alpha = min(self.alpha + 0.055, self.target_alpha)
            try:
                self.win.attributes("-alpha", self.alpha)
            except tk.TclError:
                return
            self.win.after(18, self._fade_in)

    def rise(self, dy):
        self.y -= dy
        self.win.geometry(
            f"{BOX_W + SHADOW}x{BOX_H + SHADOW}+{int(self.x)}+{int(self.y)}"
        )

    def is_offscreen(self):
        return self.y + BOX_H < -50

    def typewriter(self):
        if self.typewriter_index <= len(self.full_text):
            self.label.config(text=self.full_text[:self.typewriter_index])
            self.typewriter_index += 1
            self.win.after(55, self.typewriter)


# ============================================================
#                        OUTRO
# ============================================================
class OutroScreen:
    def __init__(self, parent, screen_w, screen_h,
                 logo_path=LOGO_PATH, on_escape=None):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.on_escape = on_escape

        self.win = tk.Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=OUTRO_BG)
        self.win.geometry(f"{screen_w}x{screen_h}+0+0")

        # Fade-in layar (stage 1)
        self.alpha = 0.0
        self.target_alpha = 1.0
        try:
            self.win.attributes("-alpha", 0.0)
            self.has_alpha = True
        except tk.TclError:
            self.has_alpha = False

        # Fokus supaya Esc kena
        try:
            self.win.focus_force()
        except tk.TclError:
            pass

        # Build Ornamen nya
        self._build_edge_ornaments()

        # Judul (font disiapin, tapi ukuran awal sangat kecil)
        self.title_font = tkfont.Font(family=SERIF_FONT, size=4,
                                      weight="bold", slant="italic")
        self.title_label = tk.Label(
            self.win, text=SONG_TITLE, font=self.title_font,
            bg=OUTRO_BG, fg=OUTRO_FG, justify="center",
        )
        self.title_label.place(relx=0.5, rely=0.42, anchor="center")

        # Credit
        self.sub_font = tkfont.Font(family=SERIF_FONT, size=2, slant="italic")
        self.sub_label = tk.Label(
            self.win, text=SCRIPT_CREDIT, font=self.sub_font,
            bg=OUTRO_BG, fg=OUTRO_ACCENT,
        )
        self.sub_label.place(relx=0.5, rely=0.57, anchor="center")

        # ---- Logo ----
        self.logo_img = None
        self.logo_base = None
        self.logo_is_text = False

        if HAS_PIL:
            try:
                orig = Image.open(logo_path).convert("RGBA")
                max_w = 170
                ratio = max_w / orig.width
                self.logo_base = orig.resize(
                    (int(orig.width * ratio), int(orig.height * ratio)),
                    Image.LANCZOS,
                )
                # Placeholder 1x1 transparan
                placeholder = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
                self.logo_img = ImageTk.PhotoImage(placeholder)
                self.logo_label = tk.Label(
                    self.win, image=self.logo_img,
                    bg=OUTRO_BG, bd=0,
                )
            except Exception:
                self.logo_label = None

        if not HAS_PIL or self.logo_label is None:
            # Fallback: teks "RevsCloud"
            self.logo_is_text = True
            self.logo_text_font = tkfont.Font(
                family=SERIF_FONT, size=2, slant="italic"
            )
            self.logo_label = tk.Label(
                self.win, text="RevsCloud",
                font=self.logo_text_font,
                bg=OUTRO_BG, fg=OUTRO_ACCENT,
            )

        self.logo_label.place(relx=0.5, rely=0.75, anchor="center")

        # Bind Esc — bind_all supaya dapat dari window mana aja
        try:
            self.win.bind_all("<Escape>", self._handle_escape)
        except tk.TclError:
            pass

        # Mulai urutan
        self._run_intro_sequence()

    # ---------- Ornamen tepi ----------
    def _build_edge_ornaments(self):
        tk.Frame(self.win, bg=OUTRO_ACCENT, height=2, width=160).place(
            relx=0.5, y=48, anchor="n")
        tk.Frame(self.win, bg=OUTRO_ACCENT, height=2, width=160).place(
            relx=0.5, rely=1.0, y=-48, anchor="s")
        tk.Label(self.win, text="✦", font=FONT_SMALL,
                 bg=OUTRO_BG, fg=OUTRO_ACCENT).place(
            relx=0.5, y=40, anchor="n")
        tk.Label(self.win, text="✦", font=FONT_SMALL,
                 bg=OUTRO_BG, fg=OUTRO_ACCENT).place(
            relx=0.5, rely=1.0, y=-56, anchor="s")

    # ---------- Urutan intro (bg → judul → credit → logo) ----------
    def _run_intro_sequence(self):
        self._fade_in_bg(on_done=lambda: self.win.after(
            STAGE_GAP_MS, self._stage_title))

    def _stage_title(self):
        self._animate_font_scale(
            self.title_font, 4, 54, duration_ms=700, delay_ms=0,
            on_done=lambda: self.win.after(STAGE_GAP_MS, self._stage_credit),
        )

    def _stage_credit(self):
        self._animate_font_scale(
            self.sub_font, 2, 18, duration_ms=550, delay_ms=0,
            on_done=lambda: self.win.after(STAGE_GAP_MS, self._stage_logo),
        )

    def _stage_logo(self):
        self._animate_logo(delay_ms=0, duration_ms=650)

    # ---------- Fade in background ----------
    def _fade_in_bg(self, on_done=None):
        if not self.has_alpha:
            if on_done:
                on_done()
            return

        def step():
            if self.alpha < self.target_alpha:
                self.alpha = min(self.alpha + 0.05, self.target_alpha)
                try:
                    self.win.attributes("-alpha", self.alpha)
                except tk.TclError:
                    if on_done:
                        on_done()
                    return
                self.win.after(18, step)
            else:
                if on_done:
                    on_done()

        step()

    # ---------- Animasi font scale (bouncing) ----------
    def _animate_font_scale(self, font_obj, min_size, max_size,
                            duration_ms, delay_ms, on_done=None):
        holder = {"start": None}

        def begin():
            holder["start"] = time.time()
            step()

        def step():
            elapsed_ms = (time.time() - holder["start"]) * 1000.0
            t = min(elapsed_ms / duration_ms, 1.0)
            k = ease_out_back(t)
            size = max(1, int(min_size + (max_size - min_size) * k))
            try:
                font_obj.configure(size=size)
            except tk.TclError:
                return
            if t < 1.0:
                self.win.after(16, step)
            elif on_done:
                on_done()

        self.win.after(delay_ms, begin)

    # ---------- Animasi logo (scale + fade) ----------
    def _animate_logo(self, delay_ms=0, duration_ms=650, on_done=None):
        if self.logo_is_text:
            self._animate_font_scale(
                self.logo_text_font, 2, 16, duration_ms, delay_ms,
                on_done=on_done,
            )
            return
        if self.logo_base is None:
            if on_done:
                on_done()
            return

        target_w, target_h = self.logo_base.size
        holder = {"start": None}

        def begin():
            holder["start"] = time.time()
            step()

        def step():
            elapsed_ms = (time.time() - holder["start"]) * 1000.0
            t = min(elapsed_ms / duration_ms, 1.0)
            k = ease_out_back(t)
            alpha = min(t * 1.4, 1.0)

            scale = 0.55 + 0.45 * k
            w = max(1, int(target_w * scale))
            h = max(1, int(target_h * scale))
            img = self.logo_base.resize((w, h), Image.LANCZOS)

            if img.mode == "RGBA":
                a = img.split()[3].point(lambda p: int(p * alpha))
                img.putalpha(a)

            photo = ImageTk.PhotoImage(img)
            self.logo_label.configure(image=photo)
            self.logo_label.image = photo

            if t < 1.0:
                self.win.after(16, step)
            elif on_done:
                on_done()

        self.win.after(delay_ms, begin)

    # ---------- Fade out untuk keluar ----------
    def fade_out(self, on_done=None, step=0.09, interval=18):
        def tick():
            try:
                a = float(self.win.attributes("-alpha"))
            except tk.TclError:
                if on_done:
                    on_done()
                return
            if a > 0:
                a = max(0.0, a - step)
                try:
                    self.win.attributes("-alpha", a)
                except tk.TclError:
                    if on_done:
                        on_done()
                    return
                self.win.after(interval, tick)
            else:
                if on_done:
                    on_done()

        tick()

    def _handle_escape(self, event=None):
        if self.on_escape:
            self.on_escape()


# ============================================================
#                        MAIN APP
# ============================================================
class LyricFloatApp:
    def __init__(self, root):
        self.root = root
        self.screen_w = root.winfo_screenwidth()
        self.screen_h = root.winfo_screenheight()
        self.next_lyric_idx = 0
        self.boxes = []
        self.last_frame_time = None
        self.current_side = "left"
        self.lift_counter = 0
        self.overlay = None
        self.outro = None
        self.outro_shown = False
        self.exiting = False
        self.start()

    def create_overlay(self):
        ov = tk.Toplevel(self.root)
        ov.overrideredirect(True)
        ov.attributes("-topmost", True)
        ov.configure(bg=OVERLAY_COLOR)
        ov.geometry(f"{self.screen_w}x{self.screen_h}+0+0")
        try:
            ov.attributes("-alpha", 0.0)
        except tk.TclError:
            pass
        ov.update_idletasks()
        ov.lift()

        def fade():
            try:
                a = float(ov.attributes("-alpha"))
            except tk.TclError:
                return
            if a < OVERLAY_ALPHA:
                a = min(a + OVERLAY_FADE_STEP, OVERLAY_ALPHA)
                try:
                    ov.attributes("-alpha", a)
                except tk.TclError:
                    return
                ov.after(OVERLAY_FADE_INTERVAL, fade)

        ov.after(60, fade)
        return ov

    def random_x_on_side(self, side):
        center = self.screen_w // 2
        if side == "left":
            x_min = SIDE_PADDING
            x_max = center - CENTER_GAP - BOX_W
        else:
            x_min = center + CENTER_GAP
            x_max = self.screen_w - BOX_W - SIDE_PADDING
        if x_max < x_min:
            x_min, x_max = x_max, x_min
        return random.randint(int(x_min), int(x_max))

    def next_y(self):
        floor_y = self.screen_h - BOX_H - BOTTOM_SPAWN_OFFSET
        if self.boxes:
            lowest = max(box.y for box in self.boxes)
            base_y = max(floor_y, lowest + BOX_H + STACK_SPACING)
        else:
            base_y = floor_y
        y = base_y + random.randint(0, Y_JITTER)
        return min(y, self.screen_h - BOX_H - 20)

    def start(self):
        self.root.iconify()
        self.overlay = self.create_overlay()
        try:
            self.root.bind_all("<Escape>", lambda e: self.exit_program())
        except tk.TclError:
            pass
        self.start_time = time.time()
        self.last_frame_time = self.start_time
        pygame.mixer.music.play()
        self.tick()

    def show_outro(self):
        if self.outro_shown:
            return
        self.outro_shown = True

        # Hancurin semua kartu nya
        for box in self.boxes:
            try:
                box.win.destroy()
            except tk.TclError:
                pass
        self.boxes = []

        self.outro = OutroScreen(
            self.root, self.screen_w, self.screen_h,
            on_escape=self.exit_program,
        )
        try:
            self.outro.win.lift()
        except tk.TclError:
            pass

    # ---------- Keluar: fade out habis itu destroy semua ----------
    def exit_program(self):
        if self.exiting:
            return
        self.exiting = True

        def cleanup():
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            for box in list(self.boxes):
                try:
                    box.win.destroy()
                except tk.TclError:
                    pass
            if self.overlay is not None:
                try:
                    self.overlay.destroy()
                except tk.TclError:
                    pass
            if self.outro is not None:
                try:
                    self.outro.win.destroy()
                except tk.TclError:
                    pass
            try:
                self.root.destroy()
            except tk.TclError:
                pass

        if self.outro is not None:
            self.outro.fade_out(on_done=cleanup)
        else:
            cleanup()

    def tick(self):
        if self.exiting:
            return
        now = time.time()
        elapsed = now - self.start_time
        dt = now - self.last_frame_time
        self.last_frame_time = now

        if not self.outro_shown:
            while (self.next_lyric_idx < len(LYRICS) and
                   LYRICS[self.next_lyric_idx][0] <= elapsed):
                _, text = LYRICS[self.next_lyric_idx]
                side = self.current_side
                self.current_side = "right" if side == "left" else "left"
                x = self.random_x_on_side(side)
                y = self.next_y()
                box = LyricCard(self.root, text, x, y)
                self.boxes.append(box)
                try:
                    box.win.lift()
                except tk.TclError:
                    pass
                self.next_lyric_idx += 1

        if not self.outro_shown and LYRICS:
            if elapsed >= LYRICS[-1][0] + OUTRO_DELAY:
                self.show_outro()

        if self.boxes:
            dy = RISE_SPEED * dt
            for box in self.boxes:
                box.rise(dy)
            still_visible = []
            for box in self.boxes:
                if box.is_offscreen():
                    try:
                        box.win.destroy()
                    except tk.TclError:
                        pass
                else:
                    still_visible.append(box)
            self.boxes = still_visible

            if not self.outro_shown:
                self.lift_counter += 1
                if self.lift_counter >= 30:
                    self.lift_counter = 0
                    for box in self.boxes:
                        try:
                            box.win.lift()
                        except tk.TclError:
                            pass

        if self.outro_shown and self.outro is not None:
            try:
                self.outro.win.lift()
            except tk.TclError:
                pass

        if not self.outro_shown or self.outro is not None:
            self.root.after(16, self.tick)


if __name__ == "__main__":
    root = tk.Tk()
    app = LyricFloatApp(root)
    root.mainloop()

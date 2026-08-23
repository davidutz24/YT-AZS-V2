#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  YT AZS  -  Version 12.0  (Cross-Platform: Windows & Linux)
  Multi-Source Video & Audio Downloader with Modern GUI and Web Fallback
  (c) 2026 David Marica - AZS Gherla
=============================================================================
"""

import os
import sys
import subprocess
import threading
import json
import re
import io
import webbrowser
from collections import deque
from datetime import datetime
from urllib.parse import parse_qs, quote_plus, urlparse
from urllib.request import Request, urlopen

try:
    from PIL import Image, ImageOps, ImageDraw
except ImportError:
    Image = None
    ImageOps = None
    ImageDraw = None

try:
    from PIL import ImageTk
except ImportError:
    ImageTk = None

try:
    import customtkinter as ctk
    from tkinter import messagebox, filedialog

    # --- MONKEY PATCH: Rock-solid CustomTkinter scroll on Windows, Linux & Mac ---
    def _patched_mouse_wheel_all(self, event):
        if not self.winfo_exists() or not self.winfo_ismapped():
            return
        
        try:
            x_root = event.x_root if hasattr(event, 'x_root') and event.x_root else self.winfo_pointerx()
            y_root = event.y_root if hasattr(event, 'y_root') and event.y_root else self.winfo_pointery()
        except Exception:
            x_root, y_root = 0, 0

        # Check if cursor is over this canvas
        try:
            cx = self._parent_canvas.winfo_rootx()
            cy = self._parent_canvas.winfo_rooty()
            cw = self._parent_canvas.winfo_width()
            ch = self._parent_canvas.winfo_height()
            if not (cx <= x_root <= cx + cw and cy <= y_root <= cy + ch):
                return
        except Exception:
            pass

        # If hovering directly over a Textbox inside this frame, let the textbox scroll
        try:
            w = self.winfo_containing(x_root, y_root)
            if w and (getattr(w, "widgetName", "") == "text" or "text" in str(w).lower()):
                return
        except Exception:
            pass

        try:
            if sys.platform.startswith("win"):
                delta = getattr(event, "delta", 0)
                if delta:
                    step = -int(delta / 40)
                    if step != 0:
                        self._parent_canvas.yview_scroll(step, "units")
            elif sys.platform == "darwin":
                delta = getattr(event, "delta", 0)
                if delta:
                    self._parent_canvas.yview_scroll(-int(delta), "units")
            else:
                num = getattr(event, "num", None)
                if num == 4:
                    self._parent_canvas.yview_scroll(-3, "units")
                elif num == 5:
                    self._parent_canvas.yview_scroll(3, "units")
                elif hasattr(event, "delta") and event.delta:
                    self._parent_canvas.yview_scroll(-int(event.delta / 40), "units")
        except Exception:
            pass
            
    ctk.windows.widgets.ctk_scrollable_frame.CTkScrollableFrame._mouse_wheel_all = _patched_mouse_wheel_all
    # ----------------------------------------------------------------------------
except ImportError:
    ctk = None
    messagebox = None
    filedialog = None

import yt_dlp
from download_engines import ENGINE_LIST, FFMPEG_PATH, get_engine_by_name

CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
VERSION = "12.0"

# ── Format lists ─────────────────────────────────────────────────────────────
VIDEO_FORMATS = [
    "Video - MP4  ProPresenter/Compatibil (H.264+AAC)",
    "Video - MP4  (1080p H.264+AAC)",
    "Video - MP4  (720p  H.264+AAC)",
    "Video - MP4  (480p  H.264+AAC)",
    "Video - MP4  (360p  H.264+AAC)",
    "Video - MP4  (Maxim 4K/8K - toate codecurile)",
    "Video - MKV  (Calitate Maxima)",
    "Video - WEBM (VP9/Opus)",
]
AUDIO_FORMATS = [
    "Audio - MP3  (320 kbps)",
    "Audio - M4A  (AAC)",
    "Audio - FLAC (Lossless)",
    "Audio - OPUS (Opus)",
    "Audio - OGG  (Vorbis)",
    "Audio - WAV  (Necomprimat)",
]
FORMAT_OPTIONS = VIDEO_FORMATS + AUDIO_FORMATS

# ── Palette & Themes ─────────────────────────────────────────────────────────
THEME_CYCLE = ["navy", "light"]

PALETTES = {
    "navy": {
        "bg":             "#14171E",
        "surface":        "#1D222D",
        "surface2":       "#262C3A",
        "border":         "#343D50",
        "btn":            "#2A3242",
        "btn_hover":      "#374257",
        "accent":         "#38BDF8",
        "accent_dim":     "#0284C7",
        "success":        "#10B981",
        "warning":        "#F59E0B",
        "danger":         "#EF4444",
        "text":           "#F1F5F9",
        "muted":          "#94A3B8",
        "log_text":       "#CBD5E1",
        "log_bg":         "#11151C",
        "ctk_mode":       "Dark",
        "dropdown_bg":    "#222836",
        "dropdown_hover": "#0284C7",
    },
    "light": {
        "bg":             "#F8FAFC",
        "surface":        "#FFFFFF",
        "surface2":       "#F1F5F9",
        "border":         "#CBD5E1",
        "btn":            "#E2E8F0",
        "btn_hover":      "#CBD5E1",
        "accent":         "#0284C7",
        "accent_dim":     "#0369A1",
        "success":        "#10B981",
        "warning":        "#D97706",
        "danger":         "#DC2626",
        "text":           "#0F172A",
        "muted":          "#64748B",
        "log_text":       "#334155",
        "log_bg":         "#F1F5F9",
        "ctk_mode":       "Light",
        "dropdown_bg":    "#FFFFFF",
        "dropdown_hover": "#0284C7",
        "dropdown_hover_text": "#FFFFFF",
    },
}

def create_spinner_pil_frames(size=20, color="#38BDF8", ring_opacity=45, num_frames=20):
    """Generates antialiased circular rotating arc spinner frames using PIL."""
    if Image is None:
        return []
    frames = []
    scale = 4
    render_size = size * scale
    line_w = max(int(render_size * 0.12), 3)
    pad = line_w // 2 + 2
    bbox = [pad, pad, render_size - pad, render_size - pad]

    c = color.lstrip("#")
    r, g, b = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

    for i in range(num_frames):
        img = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Background subtle ring
        draw.arc(bbox, 0, 360, fill=(r, g, b, ring_opacity), width=line_w)
        # Rotating active arc (115 degrees)
        start_angle = (i * 360 / num_frames)
        end_angle = start_angle + 115
        draw.arc(bbox, start_angle, end_angle, fill=(r, g, b, 255), width=line_w)
        # Antialiased downsample
        smooth = img.resize((size, size), Image.Resampling.LANCZOS)
        frames.append(smooth)
    return frames


BaseWindow = ctk.CTk if ctk else object

class YtAzsApp(BaseWindow):
    def __init__(self):
        super().__init__()
        self.title(f"YT AZS - V{VERSION} (Multi-Engine)")
        self.geometry("920x720")
        self.minsize(840, 640)
        self.resizable(True, True)

        self._config_messages = []
        self._config_message_keys = set()
        self._config_loaded_from = None
        self._migrated_config_from = None
        self._pending_config_save = None
        self._autosave_ready = False
        self.is_cancelled    = False
        self._download_active = False
        self._update_active = False
        self._download_spinner_idx = 0
        self._update_spinner_idx = 0
        self._thumb_ctk_image = None
        self._preview_after_id = None
        self._preview_request_id = 0
        self._preview_active_id = 0
        self._last_preview_url = ""
        self._last_preview_video_id = ""
        self._clipboard_seen = ""
        self._last_clipboard_url = ""
        self._clipboard_poll_job = None
        self.config_file     = self._resolve_config_file()
        self.config          = self._load_config()
        self._theme          = self.config.get("theme", "navy")
        self.C               = PALETTES[self._theme]
        self._themed         = []
        self._optmenus       = []
        self._switches       = []
        self._ui_refresh_ms  = 50
        self._max_log_lines  = 500
        self._last_win_pos   = None
        self._ui_lock        = threading.Lock()
        self._ui_actions     = deque()
        self._log_queue      = deque()
        self._pending_progress = None

        # Pre-render high resolution circular spinner frames
        self._init_spinner_assets()

        ctk.set_appearance_mode(self.C["ctk_mode"])
        self.configure(fg_color=self.C["bg"])

        # Icon setup (Windows & Linux)
        self._setup_window_icons()
        self._logo_dark = self._logo_light = None
        self._load_logos()
        self._build_ui()
        self._bind_config_autosave()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Închide dropdown-urile flotante DOAR când fereastra se deplasează efectiv pe ecran sau la click afară
        self.bind("<Configure>", self._on_window_configure)
        self.bind_all("<Button-1>", self._on_global_click, add="+")
        
        self.after(self._ui_refresh_ms, self._drain_ui_queue)
        self._startup_log()
        self.after(1000, self._poll_clipboard)

    def _init_spinner_assets(self):
        if ctk is None or Image is None:
            self._update_spinner_ctk = []
            self._dl_spinner_ctk = []
            return
        # Update spinner (cyan/accent)
        pil_update_frames = create_spinner_pil_frames(size=18, color=self.C["accent"], ring_opacity=50, num_frames=20)
        self._update_spinner_ctk = [ctk.CTkImage(light_image=f, dark_image=f, size=(18, 18)) for f in pil_update_frames]

        # Download spinner (white on vibrant green)
        pil_dl_frames = create_spinner_pil_frames(size=22, color="#FFFFFF", ring_opacity=70, num_frames=20)
        self._dl_spinner_ctk = [ctk.CTkImage(light_image=f, dark_image=f, size=(22, 22)) for f in pil_dl_frames]

    def _rebuild_spinner_assets(self):
        if ctk is None or Image is None:
            return
        pil_update_frames = create_spinner_pil_frames(size=18, color=self.C["accent"], ring_opacity=50, num_frames=20)
        self._update_spinner_ctk = [ctk.CTkImage(light_image=f, dark_image=f, size=(18, 18)) for f in pil_update_frames]

    def _setup_window_icons(self):
        ico = self._find_file_static("YT-AZS.ico")
        png = self._find_file_static("logo_white_PNG.png") or self._find_file_static("logo_black_PNG.png")
        self._window_icon = None

        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DavidMarica.YTAZS.Downloader.12.0")
            except Exception:
                pass
            if ico:
                try: self.iconbitmap(ico)
                except Exception: pass

        if ico and Image is not None and ImageTk is not None:
            try:
                img = Image.open(ico)
                self._window_icon = ImageTk.PhotoImage(img)
                self.iconphoto(True, self._window_icon)
                return
            except Exception:
                pass

        if png and Image is not None and ImageTk is not None:
            try:
                img = Image.open(png)
                self._window_icon = ImageTk.PhotoImage(img)
                self.iconphoto(True, self._window_icon)
            except Exception:
                pass

    # ── Config ─────────────────────────────────────────────────────────────────
    def _app_root(self):
        base = sys.executable if getattr(sys, "frozen", False) else __file__
        return os.path.dirname(os.path.abspath(base))

    def _resolve_config_file(self):
        if sys.platform == "win32":
            appdata = os.getenv("APPDATA")
            if appdata:
                return os.path.join(appdata, "YT AZS", "ytdlp_config.json")
        else:
            xdg_config = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
            return os.path.join(xdg_config, "yt-azs", "ytdlp_config.json")
        return os.path.join(self._app_root(), "ytdlp_config.json")

    def _legacy_config_files(self):
        current = os.path.normcase(os.path.abspath(self.config_file))
        seen = {current}
        candidates = []
        for base in [self._app_root(), os.getcwd(), os.path.expanduser("~")]:
            raw_path = os.path.abspath(os.path.join(base, "ytdlp_config.json"))
            key = os.path.normcase(raw_path)
            if key not in seen:
                seen.add(key)
                candidates.append(raw_path)
        return candidates

    def _remember_config_message(self, msg):
        if msg in self._config_message_keys: return
        self._config_message_keys.add(msg)
        self._config_messages.append(msg)
        if hasattr(self, "log_box"):
            self._log(msg, self.C["warning"])

    def _write_config_data(self, data):
        folder = os.path.dirname(self.config_file)
        if folder: os.makedirs(folder, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _refresh_config_from_widgets(self):
        if hasattr(self, "engine_var"):
            self.config["engine"] = self.engine_var.get()
        if hasattr(self, "speed_entry"):
            self.config["speed_limit"] = self.speed_entry.get().strip()
        if hasattr(self, "cookies_var"):
            self.config["cookies_browser"] = self.cookies_var.get()
        if hasattr(self, "format_var"):
            self.config["format"] = self.format_var.get()
        if hasattr(self, "playlist_var"):
            self.config["playlist"] = bool(self.playlist_var.get())
        if hasattr(self, "subtitles_var"):
            self.config["subtitles"] = bool(self.subtitles_var.get())
        if hasattr(self, "thumbnail_var"):
            self.config["thumbnail"] = bool(self.thumbnail_var.get())
        if hasattr(self, "auto_clipboard_var"):
            self.config["auto_clipboard"] = bool(self.auto_clipboard_var.get())
        self.config["theme"] = self._theme

    def _load_config(self):
        default_dl = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.isdir(default_dl):
            default_dl = os.path.expanduser("~")

        d = {
            "last_path":       default_dl,
            "engine":          ENGINE_LIST[0],
            "speed_limit":     "",
            "cookies_browser": "Niciunul",
            "theme":           "navy",
            "format":          FORMAT_OPTIONS[0],
            "playlist":        False,
            "subtitles":       False,
            "thumbnail":       True,
            "auto_clipboard":  True,
        }
        source = self.config_file
        if not os.path.exists(source):
            source = next((p for p in self._legacy_config_files() if os.path.exists(p)), self.config_file)
        self._config_loaded_from = source
        if os.path.exists(source):
            try:
                with open(source, "r", encoding="utf-8") as f:
                    d.update(json.load(f))
            except Exception as exc:
                self._remember_config_message(f"Nu am putut citi setarile din {source}: {exc}")

        if not d["last_path"] or not os.path.isdir(d["last_path"]):
            d["last_path"] = default_dl
        if d.get("format") not in FORMAT_OPTIONS:
            d["format"] = FORMAT_OPTIONS[0]
        if d.get("engine") not in ENGINE_LIST:
            d["engine"] = ENGINE_LIST[0]
        if d.get("theme") not in PALETTES:
            d["theme"] = "navy"

        if os.path.exists(source) and os.path.normcase(os.path.abspath(source)) != os.path.normcase(os.path.abspath(self.config_file)):
            try:
                self._write_config_data(d)
                self._migrated_config_from = source
            except Exception as exc:
                self._remember_config_message(f"Nu am putut migra setarile in {self.config_file}: {exc}")
        return d

    def _save_config(self):
        try:
            self._refresh_config_from_widgets()
            self._write_config_data(self.config)
            return True
        except Exception as exc:
            self._remember_config_message(f"Nu am putut salva setarile in {self.config_file}: {exc}")
            return False

    def _schedule_config_save(self, delay=250):
        if not self._autosave_ready: return
        if self._pending_config_save is not None:
            try: self.after_cancel(self._pending_config_save)
            except Exception: pass
        self._pending_config_save = self.after(delay, self._flush_pending_config_save)

    def _flush_pending_config_save(self):
        self._pending_config_save = None
        self._save_config()

    def _on_preference_changed(self, *_args):
        self._schedule_config_save()

    def _on_speed_entry_changed(self, _event=None):
        self._schedule_config_save()

    def _bind_config_autosave(self):
        watched_vars = [
            self.engine_var,
            self.format_var,
            self.cookies_var,
            self.playlist_var,
            self.subtitles_var,
            self.thumbnail_var,
            self.auto_clipboard_var,
        ]
        for var in watched_vars:
            var.trace_add("write", self._on_preference_changed)
        self.speed_entry.bind("<KeyRelease>", self._on_speed_entry_changed, add="+")
        self.speed_entry.bind("<FocusOut>", self._on_speed_entry_changed, add="+")
        self._autosave_ready = True

    def _on_close(self):
        if self._pending_config_save is not None:
            try: self.after_cancel(self._pending_config_save)
            except Exception: pass
            self._pending_config_save = None
        self._save_config()
        self.destroy()

    # ── Logo loaders ───────────────────────────────────────────────────────────
    def _find_file_static(self, filename):
        meipass = getattr(sys, "_MEIPASS", None)
        paths = []
        if meipass:
            paths.append(os.path.join(meipass, filename))
        paths += [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), filename),
            os.path.join(os.getcwd(), filename),
        ]
        return next((p for p in paths if os.path.exists(p)), None)

    def _composite_logo(self, filename, bg_hex):
        p = self._find_file_static(filename)
        if not p: return None
        try:
            logo = Image.open(p).convert("RGBA")
            r = int(bg_hex[1:3], 16)
            g = int(bg_hex[3:5], 16)
            b = int(bg_hex[5:7], 16)
            bg = Image.new("RGBA", logo.size, (r, g, b, 255))
            bg.paste(logo, mask=logo.split()[3])
            return bg.convert("RGB")
        except Exception:
            return None

    def _load_logos(self):
        size = (168, 58)
        dark_surface = self.C["surface"] if self._theme != "light" else PALETTES["navy"]["surface"]
        img = self._composite_logo("logo_white_PNG.png", dark_surface)
        if img:
            self._logo_dark = ctk.CTkImage(light_image=img, dark_image=img, size=size)
        img = self._composite_logo("logo_black_PNG.png", PALETTES["light"]["surface"])
        if img:
            self._logo_light = ctk.CTkImage(light_image=img, dark_image=img, size=size)

    def _rebuild_logos(self):
        dark_surf  = self.C["surface"] if self._theme != "light" else PALETTES["navy"]["surface"]
        light_surf = PALETTES["light"]["surface"]
        size = (168, 58)
        img = self._composite_logo("logo_white_PNG.png", dark_surf)
        if img:
            self._logo_dark = ctk.CTkImage(light_image=img, dark_image=img, size=size)
        img = self._composite_logo("logo_black_PNG.png", light_surf)
        if img:
            self._logo_light = ctk.CTkImage(light_image=img, dark_image=img, size=size)

    # ── Theme helpers ──────────────────────────────────────────────────────────
    def _reg(self, w, attr, key):
        self._themed.append((w, attr, key))

    def _reg_om(self, w):
        self._optmenus.append(w)

    def _on_window_configure(self, event=None):
        if event and event.widget == self:
            cur_pos = (self.winfo_x(), self.winfo_y())
            if self._last_win_pos is not None and self._last_win_pos != cur_pos:
                self._close_dropdowns()
            self._last_win_pos = cur_pos

    def _on_global_click(self, event=None):
        if event:
            try:
                w = self.winfo_containing(event.x_root, event.y_root)
                for om in self._optmenus:
                    if w == om or (hasattr(om, "_text_label") and w == om._text_label) or (hasattr(om, "_canvas") and w == om._canvas):
                        return
            except Exception:
                pass
        self._close_dropdowns()

    def _close_dropdowns(self, event=None):
        for om in self._optmenus:
            try:
                if hasattr(om, "_dropdown_menu") and om._dropdown_menu:
                    if hasattr(om._dropdown_menu, "close"):
                        om._dropdown_menu.close()
                    elif hasattr(om._dropdown_menu, "unpost"):
                        om._dropdown_menu.unpost()
                    elif hasattr(om._dropdown_menu, "withdraw"):
                        om._dropdown_menu.withdraw()
            except Exception:
                pass

    def _toggle_theme(self):
        idx = THEME_CYCLE.index(self._theme) if self._theme in THEME_CYCLE else 0
        self._theme = THEME_CYCLE[(idx + 1) % len(THEME_CYCLE)]
        self.C = PALETTES[self._theme]
        ctk.set_appearance_mode(self.C["ctk_mode"])
        self._rebuild_spinner_assets()
        self._apply_theme()
        self._save_config()

    def _apply_theme(self):
        C = self.C
        self.configure(fg_color=C["bg"])

        for w, attr, key in self._themed:
            try: w.configure(**{attr: C[key]})
            except Exception: pass

        for om in self._optmenus:
            try:
                om.configure(
                    fg_color=C["surface2"],
                    button_color=C["border"],
                    button_hover_color=C["accent_dim"],
                    text_color=C["text"],
                    dropdown_fg_color=C["dropdown_bg"],
                    dropdown_hover_color=C["accent_dim"],
                    dropdown_text_color=C["text"],
                )
            except Exception: pass

        if hasattr(self, "type_seg"):
            try:
                self.type_seg.configure(
                    fg_color=C["surface2"],
                    selected_color=C["accent_dim"],
                    selected_hover_color=C["accent"],
                    unselected_color=C["btn"],
                    unselected_hover_color=C["btn_hover"],
                    text_color=C["text"],
                )
            except Exception: pass

        for sw in self._switches:
            try:
                sw.configure(
                    fg_color=C["surface2"],
                    progress_color=C["accent_dim"],
                    button_color=C["text"],
                    button_hover_color=C["surface"],
                    text_color=C["muted"],
                )
            except Exception: pass

        self._rebuild_logos()
        if self.logo_label:
            img = self._logo_light if self._theme == "light" else self._logo_dark
            if img: self.logo_label.configure(image=img)

        self.theme_btn.configure(text="Light" if self._theme == "navy" else "Navy")
        self.pct_label.configure(text_color=C["accent"])
        self.status_label.configure(text_color=C["muted"])
        self._log(f"Tema comutata pe: {'Navy' if self._theme == 'navy' else 'Light'}", C["accent"])

    # ── Card helpers ───────────────────────────────────────────────────────────
    def _card_header(self, parent, title):
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(10, 0))
        strip = ctk.CTkFrame(hdr, width=3, height=14, fg_color=self.C["accent"], corner_radius=2)
        strip.pack(side="left", padx=(0, 8))
        self._reg(strip, "fg_color", "accent")
        title_lbl = ctk.CTkLabel(hdr, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color=self.C["muted"])
        title_lbl.pack(side="left", anchor="w")
        self._reg(title_lbl, "text_color", "muted")
        sep = ctk.CTkFrame(parent, height=1, fg_color=self.C["border"])
        sep.pack(fill="x", padx=14, pady=(5, 0))
        self._reg(sep, "fg_color", "border")

    def _card(self, parent, title=None, pady_bottom=8):
        card = ctk.CTkFrame(parent, fg_color=self.C["surface"], corner_radius=12,
                            border_color=self.C["border"], border_width=1)
        card.pack(fill="x", padx=12, pady=(0, pady_bottom))
        self._reg(card, "fg_color", "surface")
        self._reg(card, "border_color", "border")
        if title:
            self._card_header(card, title)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=(8, 12))
        return inner

    def _lbl(self, parent, text):
        lbl = ctk.CTkLabel(parent, text=text, text_color=self.C["muted"], font=ctk.CTkFont(size=12))
        self._reg(lbl, "text_color", "muted")
        return lbl

    def _optmenu(self, parent, var, values, width=None):
        C = self.C
        kw = {"width": width} if width else {}
        om = ctk.CTkOptionMenu(
            parent, variable=var, values=values, height=36,
            fg_color=C["surface2"],
            button_color=C["border"],
            button_hover_color=C["accent_dim"],
            text_color=C["text"],
            dropdown_fg_color=C["dropdown_bg"],
            dropdown_hover_color=C["accent_dim"],
            dropdown_text_color=C["text"],
            dynamic_resizing=False,
            corner_radius=8,
            font=ctk.CTkFont(size=12), **kw)
        self._reg_om(om)
        return om

    def _on_type_change(self, val):
        opts = VIDEO_FORMATS if val == "Video" else AUDIO_FORMATS
        self.format_menu.configure(values=opts)
        if self.format_var.get() not in opts:
            self.format_var.set(opts[0])
            self.format_menu.set(opts[0])
        self._schedule_config_save()

    # ── UI Builder ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        C = self.C

        # ── HEADER ──
        self.header = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0, height=76)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        self._reg(self.header, "fg_color", "surface")

        hline = ctk.CTkFrame(self, height=2, fg_color=C["accent"], corner_radius=0)
        hline.pack(fill="x")
        self._reg(hline, "fg_color", "accent")

        left = ctk.CTkFrame(self.header, fg_color="transparent")
        left.pack(side="left", padx=18, pady=9)

        logo_img = self._logo_light if self._theme == "light" else self._logo_dark
        self.logo_label = None
        if logo_img:
            self.logo_label = ctk.CTkLabel(left, image=logo_img, text="")
            self.logo_label.pack(side="left", padx=(0, 16))

        div = ctk.CTkFrame(left, width=1, height=46, fg_color=C["border"])
        div.pack(side="left", padx=(0, 14))
        self._reg(div, "fg_color", "border")

        title_frame = ctk.CTkFrame(left, fg_color="transparent")
        title_frame.pack(side="left")

        self.title_label = ctk.CTkLabel(
            title_frame, text="YT AZS",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=C["accent"])
        self.title_label.pack(anchor="w")
        self._reg(self.title_label, "text_color", "accent")

        self.subtitle_label = ctk.CTkLabel(
            title_frame, text=f"Multi-Source Downloader  |  V{VERSION}",
            font=ctk.CTkFont(size=10), text_color=C["muted"])
        self.subtitle_label.pack(anchor="w")
        self._reg(self.subtitle_label, "text_color", "muted")

        right = ctk.CTkFrame(self.header, fg_color="transparent")
        right.pack(side="right", padx=18, pady=18)

        self.btn_about = ctk.CTkButton(
            right, text="i",
            width=38, height=38, corner_radius=19,
            fg_color=C["surface2"], hover_color=C["btn_hover"], text_color=C["text"],
            border_width=1, border_color=C["border"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._show_about_dialog)
        self.btn_about.pack(side="left", padx=(0, 10))
        self._reg(self.btn_about, "fg_color", "surface2")
        self._reg(self.btn_about, "hover_color", "btn_hover")
        self._reg(self.btn_about, "text_color", "text")
        self._reg(self.btn_about, "border_color", "border")

        self.theme_btn = ctk.CTkButton(
            right, text="Light" if self._theme == "navy" else "Navy",
            width=88, height=38, corner_radius=19,
            fg_color=C["surface2"], hover_color=C["btn_hover"], text_color=C["text"],
            border_width=1, border_color=C["border"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._toggle_theme)
        self.theme_btn.pack(side="left", padx=(0, 10))
        self._reg(self.theme_btn, "fg_color", "surface2")
        self._reg(self.theme_btn, "hover_color", "btn_hover")
        self._reg(self.theme_btn, "text_color", "text")
        self._reg(self.theme_btn, "border_color", "border")

        self.btn_update = ctk.CTkButton(
            right, text="Actualizare Surse",
            width=155, height=38, corner_radius=19,
            fg_color=C["surface2"], hover_color=C["btn_hover"], text_color=C["text"],
            border_width=1, border_color=C["border"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.update_ytdlp)
        self.btn_update.pack(side="left")
        self._reg(self.btn_update, "fg_color", "surface2")
        self._reg(self.btn_update, "hover_color", "btn_hover")
        self._reg(self.btn_update, "text_color", "text")
        self._reg(self.btn_update, "border_color", "border")

        # ── SCROLLABLE BODY ──
        self.body = ctk.CTkScrollableFrame(
            self, fg_color=C["bg"],
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["surface2"])
        self.body.pack(fill="both", expand=True, pady=(10, 0))
        self._reg(self.body, "fg_color", "bg")
        self._reg(self.body, "scrollbar_button_color", "border")
        self._reg(self.body, "scrollbar_button_hover_color", "surface2")

        # ── Sursa / Engine Card ──
        eng_inner = self._card(self.body, "Sursa de descarcare (Download Engine / Backend)")
        eng_row = ctk.CTkFrame(eng_inner, fg_color="transparent")
        eng_row.pack(fill="x")
        self._lbl(eng_row, "Sursa activa:").pack(side="left", padx=(0, 10))

        self.engine_var = ctk.StringVar(value=self.config.get("engine", ENGINE_LIST[0]))
        self.engine_menu = self._optmenu(eng_row, self.engine_var, ENGINE_LIST)
        self.engine_menu.pack(side="left", fill="x", expand=True)

        # ── URL Card ──
        url_inner = self._card(self.body, "URL Video / Playlist")
        url_layout = ctk.CTkFrame(url_inner, fg_color="transparent")
        url_layout.pack(fill="x")

        self.preview_box = ctk.CTkFrame(
            url_layout, width=116, height=72,
            fg_color=C["surface2"], border_color=C["border"],
            border_width=1, corner_radius=10)
        self.preview_box.pack(side="left", padx=(0, 12))
        self.preview_box.pack_propagate(False)
        self._reg(self.preview_box, "fg_color", "surface2")
        self._reg(self.preview_box, "border_color", "border")

        self.preview_image_label = ctk.CTkLabel(
            self.preview_box, text="Preview", text_color=C["muted"], font=ctk.CTkFont(size=10))
        self.preview_image_label.pack(fill="both", expand=True, padx=4, pady=4)
        self._reg(self.preview_image_label, "text_color", "muted")

        url_right = ctk.CTkFrame(url_layout, fg_color="transparent")
        url_right.pack(side="left", fill="both", expand=True)

        url_row = ctk.CTkFrame(url_right, fg_color="transparent")
        url_row.pack(fill="x")
        self.url_entry = ctk.CTkEntry(
            url_row,
            placeholder_text="https://www.youtube.com/watch?v=... sau link playlist / video",
            height=40, font=ctk.CTkFont(size=12),
            fg_color=C["surface2"], border_color=C["border"], border_width=1,
            text_color=C["text"], corner_radius=8)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.url_entry.bind("<Return>", lambda _event: self.start_download())
        self._reg(self.url_entry, "fg_color", "surface2")
        self._reg(self.url_entry, "border_color", "border")

        self.btn_paste = ctk.CTkButton(
            url_row, text="Paste", width=92, height=40, corner_radius=8,
            fg_color=C["accent_dim"], hover_color=C["accent"], text_color="white",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._paste_url)
        self.btn_paste.pack(side="right")
        self._reg(self.btn_paste, "fg_color", "accent_dim")
        self._reg(self.btn_paste, "hover_color", "accent")

        self.url_entry.bind("<KeyRelease>", self._on_url_entry_changed, add="+")
        self.url_entry.bind("<<Paste>>", lambda _event: self.after(80, self._on_url_entry_changed), add="+")

        url_tools = ctk.CTkFrame(url_right, fg_color="transparent")
        url_tools.pack(fill="x", pady=(8, 0))
        self.auto_clipboard_var = ctk.BooleanVar(value=self.config.get("auto_clipboard", True))
        self.auto_clipboard_switch = ctk.CTkSwitch(
            url_tools, text="Auto clipboard",
            variable=self.auto_clipboard_var,
            onvalue=True, offvalue=False,
            fg_color=C["surface2"],
            progress_color=C["accent_dim"],
            button_color=C["text"],
            button_hover_color=C["surface"],
            text_color=C["muted"],
            font=ctk.CTkFont(size=12),
            height=24)
        self.auto_clipboard_switch.pack(side="left")
        self._switches.append(self.auto_clipboard_switch)

        self.preview_title_label = ctk.CTkLabel(
            url_tools, text="Introdu un link YouTube pentru previzualizare.",
            text_color=C["muted"], font=ctk.CTkFont(size=11), anchor="w")
        self.preview_title_label.pack(side="left", fill="x", expand=True, padx=(12, 0))
        self._reg(self.preview_title_label, "text_color", "muted")

        # ── Format + Optiuni (2-column layout) ──
        two_col = ctk.CTkFrame(self.body, fg_color="transparent", height=200)
        two_col.pack(fill="x", padx=12, pady=(0, 8))
        two_col.pack_propagate(False)
        two_col.columnconfigure(0, weight=55)
        two_col.columnconfigure(1, weight=45)
        two_col.rowconfigure(0, weight=1)

        # LEFT — Format descarcare
        fmt_card = ctk.CTkFrame(two_col, fg_color=C["surface"], corner_radius=12,
                                border_color=C["border"], border_width=1)
        fmt_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self._reg(fmt_card, "fg_color", "surface")
        self._reg(fmt_card, "border_color", "border")
        self._card_header(fmt_card, "Format descarcare")
        fmt_body = ctk.CTkFrame(fmt_card, fg_color="transparent")
        fmt_body.pack(fill="x", padx=14, pady=(8, 14))

        init_fmt  = self.config.get("format", FORMAT_OPTIONS[0])
        init_type = "Audio" if init_fmt.startswith("Audio") else "Video"
        self.format_var = ctk.StringVar(value=init_fmt)
        self.type_seg = ctk.CTkSegmentedButton(
            fmt_body, values=["Video", "Audio"],
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36, corner_radius=8,
            fg_color=C["surface2"],
            selected_color=C["accent_dim"],
            selected_hover_color=C["accent"],
            unselected_color=C["btn"],
            unselected_hover_color=C["btn_hover"],
            text_color=C["text"],
            command=self._on_type_change)
        self.type_seg.set(init_type)
        self.type_seg.pack(fill="x", pady=(0, 8))

        fmt_opts = VIDEO_FORMATS if init_type == "Video" else AUDIO_FORMATS
        if init_fmt not in fmt_opts:
            init_fmt = fmt_opts[0]
            self.format_var.set(init_fmt)
        self.format_menu = self._optmenu(fmt_body, self.format_var, fmt_opts)
        self.format_menu.pack(fill="x", pady=(0, 8))

        spd_row = ctk.CTkFrame(fmt_body, fg_color="transparent")
        spd_row.pack(fill="x")
        self._lbl(spd_row, "Limita viteza:").pack(side="left", padx=(0, 6))
        self.speed_entry = ctk.CTkEntry(
            spd_row, placeholder_text="2M / 500K / gol = nelimitat",
            height=32, fg_color=C["surface2"],
            border_color=C["border"], border_width=1,
            text_color=C["text"], font=ctk.CTkFont(size=11), corner_radius=6)
        self.speed_entry.insert(0, self.config.get("speed_limit", ""))
        self.speed_entry.pack(side="left", fill="x", expand=True)
        self._reg(self.speed_entry, "fg_color", "surface2")
        self._reg(self.speed_entry, "border_color", "border")

        # RIGHT — Optiuni
        opt_card = ctk.CTkFrame(two_col, fg_color=C["surface"], corner_radius=12,
                                border_color=C["border"], border_width=1)
        opt_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self._reg(opt_card, "fg_color", "surface")
        self._reg(opt_card, "border_color", "border")
        self._card_header(opt_card, "Optiuni")
        opt_body = ctk.CTkFrame(opt_card, fg_color="transparent")
        opt_body.pack(fill="x", padx=14, pady=(8, 14))

        sw_kw = dict(
            onvalue=True, offvalue=False,
            fg_color=C["surface2"],
            progress_color=C["accent_dim"],
            button_color=C["text"],
            button_hover_color=C["surface"],
            text_color=C["muted"],
            font=ctk.CTkFont(size=12),
            height=28,
        )
        self.playlist_var  = ctk.BooleanVar(value=self.config.get("playlist",  False))
        self.subtitles_var = ctk.BooleanVar(value=self.config.get("subtitles", False))
        self.thumbnail_var = ctk.BooleanVar(value=self.config.get("thumbnail", True))

        for text, var in [
            ("Playlist complet",  self.playlist_var),
            ("Subtitrari (RO / EN)", self.subtitles_var),
            ("Embed thumbnail",   self.thumbnail_var),
        ]:
            sw = ctk.CTkSwitch(opt_body, text=text, variable=var, **sw_kw)
            sw.pack(anchor="w", pady=(0, 6))
            self._switches.append(sw)

        ck_row = ctk.CTkFrame(opt_body, fg_color="transparent")
        ck_row.pack(fill="x", pady=(2, 0))
        self._lbl(ck_row, "Cookies:").pack(side="left", padx=(0, 8))
        self.cookies_var = ctk.StringVar(value=self.config.get("cookies_browser", "Niciunul"))
        co = self._optmenu(ck_row, self.cookies_var,
                           ["Niciunul", "chrome", "firefox", "edge", "brave", "opera", "vivaldi", "chromium"])
        co.pack(side="left", fill="x", expand=True)

        # ── Folder salvare card ──
        folder_inner = self._card(self.body, "Folder salvare")
        fr = ctk.CTkFrame(folder_inner, fg_color="transparent")
        fr.pack(fill="x")
        self.path_label = ctk.CTkLabel(
            fr, text=self._short(self.config["last_path"]),
            text_color=C["accent"], font=ctk.CTkFont(size=12), anchor="w")
        self.path_label.pack(side="left", fill="x", expand=True)
        self._reg(self.path_label, "text_color", "accent")

        self.btn_open_folder = ctk.CTkButton(
            fr, text="Deschide", width=86, height=32, corner_radius=8,
            fg_color=C["btn"], hover_color=C["accent_dim"], text_color=C["text"],
            command=self._open_folder)
        self.btn_open_folder.pack(side="right", padx=(6, 0))
        self._reg(self.btn_open_folder, "fg_color", "btn")
        self._reg(self.btn_open_folder, "hover_color", "accent_dim")
        self._reg(self.btn_open_folder, "text_color", "text")

        self.btn_change_folder = ctk.CTkButton(
            fr, text="Schimba", width=78, height=32, corner_radius=8,
            fg_color=C["btn"], hover_color=C["accent_dim"], text_color=C["text"],
            command=self._choose_folder)
        self.btn_change_folder.pack(side="right")
        self._reg(self.btn_change_folder, "fg_color", "btn")
        self._reg(self.btn_change_folder, "hover_color", "accent_dim")
        self._reg(self.btn_change_folder, "text_color", "text")

        # ── Log card ──
        log_inner = self._card(self.body, "Jurnal evenimente", pady_bottom=4)
        log_top = ctk.CTkFrame(log_inner, fg_color="transparent")
        log_top.pack(fill="x", pady=(0, 4))
        self.btn_clear_log = ctk.CTkButton(
            log_top, text="Curata jurnal", width=90, height=24, corner_radius=6,
            fg_color="transparent", hover_color=C["surface2"],
            text_color=C["muted"], command=self._clear_log)
        self.btn_clear_log.pack(side="right")
        self._reg(self.btn_clear_log, "hover_color", "surface2")
        self._reg(self.btn_clear_log, "text_color", "muted")

        self.log_box = ctk.CTkTextbox(
            log_inner, height=120, font=ctk.CTkFont(family="Consolas" if sys.platform == "win32" else "Monospace", size=10),
            fg_color=C["log_bg"], text_color=C["log_text"],
            border_color=C["border"], border_width=1,
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["surface2"], corner_radius=8)
        self.log_box.pack(fill="x")
        self.log_box.configure(state="disabled")
        self._reg(self.log_box, "fg_color",     "log_bg")
        self._reg(self.log_box, "text_color",   "log_text")
        self._reg(self.log_box, "border_color", "border")
        self._reg(self.log_box, "scrollbar_button_color", "border")
        self._reg(self.log_box, "scrollbar_button_hover_color", "surface2")

        # ── BOTTOM BAR ──
        self.bot = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0, height=126)
        self.bot.pack(fill="x", side="bottom")
        self.bot.pack_propagate(False)
        self._reg(self.bot, "fg_color", "surface")

        sep = ctk.CTkFrame(self.bot, height=1, fg_color=C["border"])
        sep.pack(fill="x", side="top")
        self._reg(sep, "fg_color", "border")

        progress_panel = ctk.CTkFrame(self.bot, fg_color="transparent")
        progress_panel.pack(fill="x", padx=14, pady=(8, 0))

        progress_top = ctk.CTkFrame(progress_panel, fg_color="transparent")
        progress_top.pack(fill="x")

        self.status_label = ctk.CTkLabel(
            progress_top, text="Gata de descarcare.",
            text_color=C["muted"], font=ctk.CTkFont(size=11), anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)
        self._reg(self.status_label, "text_color", "muted")

        self.pct_label = ctk.CTkLabel(
            progress_top, text="0%",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=C["accent"])
        self.pct_label.pack(side="right", padx=(10, 0))

        self.progress_bar = ctk.CTkProgressBar(
            progress_panel, height=9, corner_radius=5,
            fg_color=C["surface2"], progress_color=C["accent"])
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(4, 2))
        self._reg(self.progress_bar, "fg_color", "surface2")
        self._reg(self.progress_bar, "progress_color", "accent")

        progress_meta = ctk.CTkFrame(progress_panel, fg_color="transparent")
        progress_meta.pack(fill="x")
        self.speed_lbl = ctk.CTkLabel(
            progress_meta, text="", font=ctk.CTkFont(size=10), text_color=C["muted"])
        self.speed_lbl.pack(side="left")
        self._reg(self.speed_lbl, "text_color", "muted")

        self.eta_lbl = ctk.CTkLabel(
            progress_meta, text="", font=ctk.CTkFont(size=10), text_color=C["muted"])
        self.eta_lbl.pack(side="right")
        self._reg(self.eta_lbl, "text_color", "muted")

        bar = ctk.CTkFrame(self.bot, fg_color="transparent")
        bar.pack(fill="x", padx=14, pady=(6, 10))

        self.btn_download = ctk.CTkButton(
            bar, text="DESCARCA",
            font=ctk.CTkFont(size=16, weight="bold"),
            width=240, height=52, corner_radius=12,
            fg_color=C["accent_dim"], hover_color=C["accent"], text_color="white",
            command=self.start_download)
        self.btn_download.pack(side="left", padx=(0, 10))
        self._reg(self.btn_download, "fg_color", "accent_dim")
        self._reg(self.btn_download, "hover_color", "accent")

        self.btn_cancel = ctk.CTkButton(
            bar, text="Anuleaza",
            font=ctk.CTkFont(size=15, weight="bold"),
            width=170, height=52, corner_radius=12,
            fg_color=C["surface2"], hover_color=C["danger"], text_color=C["muted"],
            state="normal", command=self.cancel_download)
        self.btn_cancel.pack(side="left")
        self._reg(self.btn_cancel, "fg_color", "surface2")
        self._reg(self.btn_cancel, "hover_color", "danger")
        self._reg(self.btn_cancel, "text_color", "muted")

        ctk.CTkLabel(
            bar, text="© 2026 David Marica - AZS Gherla",
            text_color=C["border"], font=ctk.CTkFont(size=10)
        ).pack(side="right", pady=(12, 0))

    def _show_about_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Despre YT AZS")
        dlg.geometry("660x560")
        dlg.minsize(580, 480)
        dlg.transient(self)
        dlg.grab_set()

        try:
            x = self.winfo_x() + (self.winfo_width() // 2) - 330
            y = self.winfo_y() + (self.winfo_height() // 2) - 280
            dlg.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        C = self.C
        dlg.configure(fg_color=C["bg"])

        hdr = ctk.CTkFrame(dlg, fg_color=C["surface"], corner_radius=10, border_color=C["border"], border_width=1)
        hdr.pack(fill="x", padx=16, pady=(16, 10))

        logo_img = self._logo_light if self._theme == "light" else self._logo_dark
        if logo_img:
            l_lbl = ctk.CTkLabel(hdr, image=logo_img, text="")
            l_lbl.pack(side="left", padx=14, pady=10)

        t_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        t_frame.pack(side="left", padx=6, pady=10)

        ctk.CTkLabel(t_frame, text=f"YT AZS — V{VERSION}", font=ctk.CTkFont(size=18, weight="bold"), text_color=C["accent"]).pack(anchor="w")
        ctk.CTkLabel(t_frame, text="Multi-Source Video & Audio Downloader", font=ctk.CTkFont(size=12), text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(t_frame, text="© 2026 David Marica - AZS Gherla", font=ctk.CTkFont(size=11), text_color=C["muted"]).pack(anchor="w")

        tabs = ctk.CTkTabview(dlg, fg_color=C["surface"], segmented_button_selected_color=C["accent_dim"],
                               segmented_button_unselected_color=C["surface2"], text_color=C["text"])
        tabs.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        tab_sources = tabs.add("Surse & Credite")
        tab_readme = tabs.add("Documentatie (README)")

        s_frame = ctk.CTkScrollableFrame(tab_sources, fg_color="transparent")
        s_frame.pack(fill="both", expand=True, padx=4, pady=4)

        sources_data = [
            ("GitHub Proiect YT-AZS", "https://github.com/davidutz24/YT-AZS", "Codul sursa oficial, noutati si lansari YT-AZS."),
            ("GitHub Release V11.4", "https://github.com/davidutz24/YT-AZS/releases/tag/V11.4", "Versiunea anterioara si arhiva de lansari."),
            ("YT-DLP", "https://github.com/yt-dlp/yt-dlp", "Motorul principal de extractie video/audio avansat."),
            ("NewPipe Extractor", "https://github.com/teamnewpipe/newpipeextractor", "Extractor Android InnerTube fara dependinte externe."),
            ("Cobalt Tools Directory", "https://cobalt.directory/", "Indexul oficial si instanțele active Cobalt Tools API."),
            ("YouTubeExplode", "https://github.com/tyrrrz/youtubeexplode", "Proiect C# de analiza si parsare streamuri YouTube."),
            ("ytdl-patched", "https://github.com/ytdl-patched/ytdl-patched", "Versiune compatibila pentru extractie clasica."),
            ("9xBuddy", "https://9xbuddy.com/", "Extractor universal pentru platforme media diverse."),
        ]

        for title, link, desc in sources_data:
            c = ctk.CTkFrame(s_frame, fg_color=C["surface2"], corner_radius=8, border_color=C["border"], border_width=1)
            c.pack(fill="x", pady=4)

            top_r = ctk.CTkFrame(c, fg_color="transparent")
            top_r.pack(fill="x", padx=10, pady=(6, 2))

            ctk.CTkLabel(top_r, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=C["accent"]).pack(side="left")

            btn_link = ctk.CTkButton(
                top_r, text="Deschide Link ↗", width=110, height=24, corner_radius=6,
                fg_color=C["accent_dim"], hover_color=C["accent"], text_color="#fff",
                font=ctk.CTkFont(size=11),
                command=lambda u=link: webbrowser.open(u))
            btn_link.pack(side="right")

            ctk.CTkLabel(c, text=desc, font=ctk.CTkFont(size=11), text_color=C["muted"], anchor="w").pack(fill="x", padx=10, pady=(0, 6))

        readme_box = ctk.CTkTextbox(
            tab_readme, font=ctk.CTkFont(family="Consolas" if sys.platform == "win32" else "Monospace", size=11),
            fg_color=C["log_bg"], text_color=C["log_text"], corner_radius=8)
        readme_box.pack(fill="both", expand=True, padx=4, pady=4)

        readme_path = self._find_file_static("README.md")
        readme_text = ""
        if readme_path and os.path.exists(readme_path):
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    readme_text = f.read()
            except Exception:
                pass
        if not readme_text:
            readme_text = f"YT-AZS Versiunea {VERSION}\nAutor: David Marica - AZS Gherla\n© 2026 Toate drepturile rezervate."

        readme_box.insert("1.0", readme_text)
        readme_box.configure(state="disabled")

        b_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        b_frame.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkButton(
            b_frame, text="Inchide", width=120, height=36, corner_radius=8,
            fg_color=C["surface2"], hover_color=C["accent_dim"], text_color=C["text"],
            command=dlg.destroy
        ).pack(side="right")

    def _startup_log(self):
        self._log(f"YT AZS V{VERSION} pornit pe {sys.platform.upper()}.", self.C["accent"])
        self._log(f"Configuratie: {self.config_file}", self.C["muted"])
        if FFMPEG_PATH:
            self._log(f"FFmpeg OK: {os.path.basename(FFMPEG_PATH)} ({FFMPEG_PATH})", self.C["success"])
        else:
            self._log("FFmpeg negasit! Conversiile video/audio complexe pot fi limitate.", self.C["warning"])
        self._log(f"Folder salvare: {self.config['last_path']}", self.C["muted"])
        self._log(f"Sursa activa: {self.config.get('engine', ENGINE_LIST[0])}", self.C["accent"])

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _short(self, path, n=62):
        return path if len(path) <= n else "..." + path[-(n-3):]

    def _extract_first_url(self, text):
        if not text: return ""
        m = re.search(r'https?://[^\s<>"\'\\]+', text.strip())
        if not m: return ""
        return m.group(0).rstrip(").,;]")

    def _is_supported_media_url(self, url):
        try:
            host = urlparse(url).netloc.lower()
            return any(h in host for h in ("youtube.com", "youtu.be", "youtube-nocookie.com", "tiktok.com", "instagram.com", "vimeo.com"))
        except Exception:
            return False

    def _youtube_video_id(self, url):
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower().replace("www.", "")
            path = parsed.path.strip("/")
            if host == "youtu.be":
                return path.split("/")[0][:11]
            if "youtube.com" in host or "youtube-nocookie.com" in host:
                query_id = parse_qs(parsed.query).get("v", [""])[0]
                if query_id: return query_id[:11]
                parts = path.split("/")
                for key in ("shorts", "embed", "live", "v"):
                    if key in parts:
                        idx = parts.index(key)
                        if idx + 1 < len(parts): return parts[idx + 1][:11]
        except Exception:
            pass
        return ""

    def _direct_thumbnail_urls(self, video_id):
        if not video_id: return []
        base = f"https://img.youtube.com/vi/{quote_plus(video_id)}"
        return [f"{base}/hqdefault.jpg"]

    def _load_preview_image_from_url(self, thumb_url, timeout=2.0):
        req = Request(thumb_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=timeout) as response:
            data = response.read(3 * 1024 * 1024)
        image = Image.open(io.BytesIO(data)).convert("RGB")
        return ImageOps.fit(image, (96, 54), method=Image.Resampling.LANCZOS)

    def _set_preview_title(self, text):
        try: self.preview_title_label.configure(text=text)
        except Exception: pass

    def _replace_preview_label(self, text="", image=None):
        old_label = getattr(self, "preview_image_label", None)
        if old_label is not None:
            self._themed = [item for item in self._themed if item[0] is not old_label]
            try: old_label.destroy()
            except Exception: pass
        self.preview_image_label = ctk.CTkLabel(
            self.preview_box, text=text, image=image,
            text_color=self.C["muted"], font=ctk.CTkFont(size=10))
        self.preview_image_label.pack(fill="both", expand=True, padx=4, pady=4)
        self._reg(self.preview_image_label, "text_color", "muted")

    def _set_preview_empty(self, text):
        self._thumb_ctk_image = None
        self._replace_preview_label(text=text)

    def _apply_preview(self, request_id, url, video_id, image, title, uploader, duration, error):
        if request_id != self._preview_active_id:
            return
        self._last_preview_url = url
        self._last_preview_video_id = video_id
        self._preview_active_id = 0
        if error:
            self._set_preview_empty("No preview")
            self._set_preview_title(f"Previzualizare indisponibila: {error}")
            return
        if image:
            self._thumb_ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(96, 54))
            self._replace_preview_label(image=self._thumb_ctk_image)
        else:
            self._set_preview_empty("No image")
        meta = " | ".join(x for x in (uploader, duration) if x)
        label = title if not meta else f"{title}  ({meta})"
        self._set_preview_title(self._short(label, 88))
        self._log(f"Thumbnail incarcat: {self._short(title, 60)}", self.C["success"])

    def _set_url(self, url, source="manual"):
        url = self._extract_first_url(url) or url.strip()
        if not url: return
        current = self._extract_first_url(self.url_entry.get().strip())
        if current != url:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url)
        if source == "clipboard":
            self._log("Link detectat automat in clipboard.", self.C["accent"])
        self._schedule_preview_fetch(url)

    def _on_url_entry_changed(self, _event=None):
        self._schedule_preview_fetch(self.url_entry.get().strip())

    def _poll_clipboard(self):
        try:
            if self.auto_clipboard_var.get():
                clip = self.clipboard_get().strip()
                if clip:
                    url = self._extract_first_url(clip)
                    if url and self._is_supported_media_url(url):
                        current_url = self._extract_first_url(self.url_entry.get().strip())
                        if clip != self._clipboard_seen or url != self._last_clipboard_url or url != current_url:
                            self._clipboard_seen = clip
                            self._last_clipboard_url = url
                            self._set_url(url, source="clipboard")
                    else:
                        self._clipboard_seen = clip
        except Exception:
            pass
        finally:
            self._clipboard_poll_job = self.after(1000, self._poll_clipboard)

    def _schedule_preview_fetch(self, url, delay_ms=350):
        url = self._extract_first_url(url)
        video_id = self._youtube_video_id(url)
        if self._preview_after_id:
            try: self.after_cancel(self._preview_after_id)
            except Exception: pass
            self._preview_after_id = None

        if not url:
            self._last_preview_url = ""
            self._last_preview_video_id = ""
            self._preview_request_id += 1
            self._preview_active_id = 0
            self._set_preview_empty("Preview")
            self._set_preview_title("Introdu un link YouTube pentru previzualizare.")
            return

        self._preview_request_id += 1
        request_id = self._preview_request_id
        self._preview_active_id = request_id
        self._set_preview_empty("Loading...")
        if video_id:
            self._set_preview_title(f"Video YouTube: {video_id}")
        else:
            self._set_preview_title("Preluare date video...")
            
        def _trigger():
            self._start_preview_fetch(request_id, url, video_id)
            
        self._preview_after_id = self.after(delay_ms, _trigger)

    def _start_preview_fetch(self, request_id, url, expected_video_id=""):
        def _run():
            try:
                video_id = expected_video_id or self._youtube_video_id(url)
                if video_id:
                    for thumb_url in self._direct_thumbnail_urls(video_id):
                        try:
                            image = self._load_preview_image_from_url(thumb_url, timeout=2.0)
                            self._queue_preview_result(
                                request_id, url, video_id, image, f"YouTube video: {video_id}", "", "", None)
                            return
                        except Exception:
                            continue

                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "skip_download": True,
                    "noplaylist": True,
                }
                browser = self.cookies_var.get()
                if browser != "Niciunul":
                    ydl_opts["cookiesfrombrowser"] = (browser, None, None, None)
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                title = info.get("title") or "Video detectat"
                uploader = info.get("uploader") or info.get("channel") or ""
                duration = info.get("duration_string") or ""
                thumb_url = info.get("thumbnail") or ""
                image = None
                if thumb_url:
                    try: image = self._load_preview_image_from_url(thumb_url, timeout=2.5)
                    except Exception: pass
                self._queue_preview_result(request_id, url, video_id, image, title, uploader, duration, None)
            except Exception as ex:
                self._queue_preview_result(request_id, url, expected_video_id, None, "", "", "", str(ex)[:80])

        threading.Thread(target=_run, daemon=True).start()

    def _queue_preview_result(self, request_id, url, video_id, image, title, uploader, duration, error):
        self._queue_ui_action(self._apply_preview, request_id, url, video_id, image, title, uploader, duration, error)

    def _paste_url(self):
        try: self._set_url(self.clipboard_get().strip(), source="paste")
        except Exception: pass

    def _choose_folder(self):
        path = filedialog.askdirectory(
            title="Alege folderul de salvare",
            initialdir=self.config.get("last_path", os.path.expanduser("~")))
        if path:
            self.config["last_path"] = path
            self.path_label.configure(text=self._short(path))
            self._save_config()
            self._log(f"Folder setat: {path}", self.C["accent"])

    def _open_folder(self):
        path = self.config.get("last_path", "")
        if path and os.path.isdir(path):
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        else:
            messagebox.showwarning("Folder invalid", "Folderul specificat nu exista.")

    # ── Notification System ───────────────────────────────────────────────────
    def _notify(self, title: str, message: str):
        if sys.platform == "win32":
            t = title.replace('"', "'").replace("\n", " ")
            m = message.replace('"', "'").replace("\n", " ")
            ps = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$i = [System.Drawing.SystemIcons]::Information; "
                "$n = New-Object System.Windows.Forms.NotifyIcon; "
                "$n.Icon = $i; "
                "$n.Visible = $true; "
                f'$n.ShowBalloonTip(8000, "{t}", "{m}", [System.Windows.Forms.ToolTipIcon]::Info); '
                "Start-Sleep -Milliseconds 9000; "
                "$n.Dispose()"
            )
            try:
                subprocess.Popen(
                    ["powershell", "-WindowStyle", "Hidden", "-NonInteractive", "-Command", ps],
                    creationflags=CREATE_NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        elif sys.platform == "linux":
            try:
                subprocess.Popen(["notify-send", title, message])
            except Exception:
                pass
        elif sys.platform == "darwin":
            try:
                subprocess.Popen(["osascript", "-e", f'display notification "{message}" with title "{title}"'])
            except Exception:
                pass

    # ── Log & UI Queue ─────────────────────────────────────────────────────────
    def _log(self, msg, color=None):
        line = f"[{datetime.now().strftime('%H:%M:%S')}]  {msg}"
        with self._ui_lock:
            self._log_queue.append(line)

    def _clear_log(self):
        with self._ui_lock:
            self._log_queue.clear()
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _queue_ui_action(self, callback, *args, **kwargs):
        with self._ui_lock:
            self._ui_actions.append((callback, args, kwargs))

    def _queue_progress_state(self, **state):
        with self._ui_lock:
            current = dict(self._pending_progress or {})
            current.update(state)
            self._pending_progress = current

    def _flush_log_lines(self, lines):
        if not lines: return
        self.log_box.configure(state="normal")
        self.log_box.insert("end", "\n".join(lines) + "\n")
        line_count = int(float(self.log_box.index("end-1c").split(".")[0]))
        overflow = line_count - self._max_log_lines
        if overflow > 0:
            self.log_box.delete("1.0", f"{overflow + 1}.0")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _apply_progress_state(self, state):
        if not state: return
        if "progress" in state:
            self.progress_bar.set(state["progress"])
        if "pct_text" in state:
            self.pct_label.configure(text=state["pct_text"])
        if "speed_text" in state:
            self.speed_lbl.configure(text=state["speed_text"])
        if "eta_text" in state:
            self.eta_lbl.configure(text=state["eta_text"])
        if "status_text" in state:
            opts = {"text": state["status_text"]}
            if "status_color" in state:
                col_name = state["status_color"]
                opts["text_color"] = self.C.get(col_name, self.C["text"])
            self.status_label.configure(**opts)

    def _drain_ui_queue(self):
        with self._ui_lock:
            actions = list(self._ui_actions)
            self._ui_actions.clear()
            logs = list(self._log_queue)
            self._log_queue.clear()
            progress = self._pending_progress
            self._pending_progress = None

        if actions:
            for callback, args, kwargs in actions:
                try: callback(*args, **kwargs)
                except Exception: pass

        if logs:
            self._flush_log_lines(logs)
        if progress:
            self._apply_progress_state(progress)
        self.after(self._ui_refresh_ms, self._drain_ui_queue)

    def _flash_folder_button(self):
        self.btn_change_folder.configure(fg_color=self.C["accent"], text_color="white")
        self.after(3000, lambda: self.btn_change_folder.configure(fg_color=self.C["btn"], text_color=self.C["text"]))

    # ── Smooth Rotating Circular Arc Animation ────────────────────────────────
    def _animate_update_button(self):
        if not self._update_active:
            self.btn_update.configure(
                text="Actualizare Surse",
                image=None,
                compound="none",
                state="normal",
                fg_color=self.C["surface2"],
                hover_color=self.C["btn_hover"],
                text_color=self.C["text"]
            )
            return
        frame = self._update_spinner_ctk[self._update_spinner_idx % len(self._update_spinner_ctk)]
        self._update_spinner_idx += 1
        self.btn_update.configure(
            image=frame,
            compound="left",
            text=" Actualizare...",
            fg_color=self.C["surface2"],
            hover_color=self.C["btn_hover"],
            text_color=self.C["accent"]
        )
        self.after(40, self._animate_update_button)

    def _animate_download_button(self):
        if not self._download_active:
            self.btn_download.configure(
                text="DESCARCA",
                image=None,
                compound="none",
                fg_color=self.C["accent_dim"],
                hover_color=self.C["accent"],
                text_color="white"
            )
            return
        frame = self._dl_spinner_ctk[self._download_spinner_idx % len(self._dl_spinner_ctk)]
        self._download_spinner_idx += 1
        pct = self.pct_label.cget("text")
        if pct and pct != "0%":
            label_text = f" SE DESCARCĂ ({pct})"
        else:
            label_text = " SE DESCARCĂ..."
        self.btn_download.configure(
            image=frame,
            compound="left",
            text=label_text,
            fg_color=self.C["success"],
            hover_color=self.C["success"],
            text_color="#FFFFFF"
        )
        self.after(40, self._animate_download_button)

    # ── Update All Sources & Core ──────────────────────────────────────────────
    def update_ytdlp(self):
        if self._update_active:
            return
        self._update_active = True
        self._update_spinner_idx = 0
        self.btn_update.configure(state="disabled")
        self._animate_update_button()

        self._log("Se actualizeaza motoarele de extractie si dependintele (yt-dlp, mutagen)...", self.C["warning"])
        def _run():
            try:
                cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp", "mutagen"]
                r = subprocess.run(cmd, capture_output=True, text=True, check=True, creationflags=CREATE_NO_WINDOW)
                info = next((l.strip() for l in r.stdout.splitlines() if "installed" in l.lower() or "up-to-date" in l.lower()), "OK")
                self._log(f"Toate sursele si motoarele au fost actualizate la zi! ({info})", self.C["success"])
                self._queue_progress_state(status_text="Surse actualizate cu succes! Componentele sunt la zi.", status_color="success")
            except Exception as e:
                self._log(f"Actualizare esuata: {e}", self.C["danger"])
            finally:
                self._update_active = False
                self._queue_ui_action(
                    self.btn_update.configure,
                    text="Actualizare Surse",
                    image=None,
                    compound="none",
                    state="normal",
                    fg_color=self.C["surface2"],
                    hover_color=self.C["btn_hover"],
                    text_color=self.C["text"]
                )

        threading.Thread(target=_run, daemon=True).start()

    # ── Cancel Download ────────────────────────────────────────────────────────
    def cancel_download(self):
        if not self._download_active:
            self.status_label.configure(text="Nicio descarcare activa.", text_color=self.C["muted"])
            return
        self.is_cancelled = True
        self.status_label.configure(text="Anulare in curs...", text_color=self.C["danger"])
        self._log("Descarcarea a fost anulata de utilizator.", self.C["danger"])

    # ── Start Download ─────────────────────────────────────────────────────────
    def start_download(self):
        if self._download_active:
            return
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Eroare", "Introdu un URL valid.")
            return
        save_path = self.config.get("last_path", "")
        if not save_path or not os.path.isdir(save_path):
            save_path = filedialog.askdirectory(title="Alege folderul de salvare", initialdir=os.path.expanduser("~"))
            if not save_path: return
            self.config["last_path"] = save_path
            self.path_label.configure(text=self._short(save_path))

        job = {
            "engine": self.engine_var.get(),
            "format": self.format_var.get(),
            "playlist": bool(self.playlist_var.get()),
            "subtitles": bool(self.subtitles_var.get()),
            "thumbnail": bool(self.thumbnail_var.get()),
            "cookies_browser": self.cookies_var.get(),
            "speed_limit": self.speed_entry.get().strip(),
        }
        self._save_config()
        self.is_cancelled = False
        self._download_active = True
        self._download_spinner_idx = 0
        self._animate_download_button()

        self.btn_cancel.configure(state="normal", text_color=self.C["danger"])
        self.progress_bar.set(0)
        self.pct_label.configure(text="0%")
        self.speed_lbl.configure(text="")
        self.eta_lbl.configure(text="")

        self._log(f"Pornire descarcare: {self._short(url, 65)} (Sursa: {job['engine']})", self.C["accent"])
        threading.Thread(target=self._do_download, args=(url, save_path, job), daemon=True).start()

    def _do_download(self, url, save_path, job):
        engine_name = job.get("engine", ENGINE_LIST[0])
        engine = get_engine_by_name(engine_name)

        def progress_cb(**kwargs):
            self._queue_progress_state(**kwargs)

        def log_cb(msg, color_key="muted"):
            self._log(msg, self.C.get(color_key, self.C["text"]))

        def is_cancelled_fn():
            return self.is_cancelled

        try:
            success = engine.download(url, save_path, job, progress_cb, log_cb, is_cancelled_fn)
            if success:
                self._queue_progress_state(
                    progress=1.0,
                    pct_text="100%",
                    status_text=f"Descarcare completa! Salvat in: {self._short(save_path)}",
                    status_color="success")
                self._log(f"Complet! Fisierul a fost salvat in: {save_path}", self.C["success"])
                threading.Thread(
                    target=self._notify,
                    args=("YT AZS - Descarcare completa!", f"Fisierul a fost salvat in:\n{self._short(save_path, 50)}"),
                    daemon=True
                ).start()
                self._queue_ui_action(self._flash_folder_button)
        except Exception as e:
            if self.is_cancelled:
                self._queue_progress_state(status_text="Descarcare anulata.", status_color="danger")
                self._log("Descarcarea a fost oprita.", self.C["danger"])
            else:
                err_text = str(e).strip()
                self._queue_progress_state(status_text=f"Eroare: {err_text[:80]}", status_color="danger")
                self._log(f"Eroare la descarcare: {err_text}", self.C["danger"])
                threading.Thread(
                    target=self._notify,
                    args=("YT AZS - Eroare descarcare", f"A aparut o eroare: {err_text[:60]}"),
                    daemon=True
                ).start()
        finally:
            self._download_active = False
            self._queue_ui_action(
                self.btn_download.configure,
                text="DESCARCA",
                image=None,
                compound="none",
                fg_color=self.C["accent_dim"],
                hover_color=self.C["accent"],
                text_color="white"
            )
            self._queue_ui_action(self.btn_cancel.configure, state="normal", text_color=self.C["muted"])


def main():
    if "--web" in sys.argv or "-w" in sys.argv:
        try:
            import web_server
            web_server.start_server()
            return
        except Exception as e:
            print(f"[YT-AZS Web Mode Error] {e}")
            return

    if ctk is None:
        print("[YT-AZS] Lipsesc dependinte GUI (customtkinter, Pillow). Pornire mod Web Browser de rezerva...")
        try:
            import web_server
            web_server.start_server()
            return
        except Exception as exc:
            print(f"[YT-AZS Fatal] {exc}")
            sys.exit(1)

    app = YtAzsApp()
    app.mainloop()


if __name__ == "__main__":
    main()

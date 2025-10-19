#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrajnaPlayer v12.2 – Compact UI + Shortcuts + Center Image (fixed)
- Nút nhỏ gọn, hiển thị phím tắt ngay trên nút
- Ảnh trung tâm: tự tìm buddha/logo; nút Set Image [Ctrl+I]; nhớ vào prajna_config.json
- Thanh filter dưới ảnh; progress + playlist; VLC playback (nếu có)

Author: PharmApp (2025)
"""

import json
import random
import time
from pathlib import Path
from typing import Dict, List, Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --- Optional Pillow (for images) ---
try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

# --- Optional mutagen (durations) ---
try:
    from mutagen import File as MutagenFile
except Exception:
    MutagenFile = None

# --- Optional VLC ---
try:
    import vlc
except Exception:
    vlc = None

# ---------- Theme -----
BG = "#fdf5e6"
FG = "#2a2a2a"
BTN_BG = "#f4a261"
BTN_BG_ACTIVE = "#e76f51"
TV_HEAD_BG = "#b5838d"

AUDIO_EXTS = (".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")

SORT_CHOICES = [
    "Title (A→Z)", "Title (Z→A)",
    "Modified (Newest)", "Modified (Oldest)",
    "Size (Large→Small)", "Size (Small→Large)",
    "Duration (Long→Short)", "Duration (Short→Long)",
]


def apply_pharmapp_theme(root: tk.Tk):
    s = ttk.Style(root)
    try:
        s.theme_use("default")
    except Exception:
        pass
    s.configure("TFrame", background=BG)
    s.configure("TLabelframe", background=BG)
    s.configure("TLabel", background=BG, foreground=FG, font=("Arial", 11))
    s.configure("TEntry", padding=5)
    s.configure("TCombobox", padding=5)
    s.configure("TButton", font=("Arial", 10))
    s.configure("Expander.TButton", background=BG, relief="flat", padding=6)
    s.map("Expander.TButton", background=[("active", BG)])

    s.configure("Treeview",
               background="white", foreground=FG, fieldbackground="white",
               font=("Arial", 10), rowheight=22)
    s.configure("Treeview.Heading",
               background=TV_HEAD_BG, foreground="white", font=("Arial", 10, "bold"))
    s.map("Treeview", background=[("selected", "#e9c46a")])


def style_btn(b: tk.Button) -> None:
    b.configure(bg=BTN_BG, fg="black",
                activebackground=BTN_BG_ACTIVE, activeforeground="black",
                bd=0, relief=tk.FLAT, font=("Arial", 9, "bold"),
                cursor="hand2", padx=6, pady=3)


# ---------- Simple Expander ----------
class Expander(ttk.Frame):
    def __init__(self, master, title: str, open_=True):
        super().__init__(master)
        self.var_open = tk.BooleanVar(value=open_)
        self.btn = ttk.Button(self, text=title, style="Expander.TButton", command=self.toggle)
        self.btn.pack(fill=tk.X)
        self.body = ttk.Frame(self)
        if open_:
            self.body.pack(fill=tk.BOTH, expand=True)

    def toggle(self):
        if self.var_open.get():
            self.var_open.set(False)
            self.body.forget()
        else:
            self.var_open.set(True)
            self.body.pack(fill=tk.BOTH, expand=True)


class PrajnaPlayerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PrajnaPlayer v12.2 · PharmApp")

        # State
        self.items_all: List[Dict] = []
        self.items_view: List[int] = []
        self.current_index: int = -1
        self.is_repeat = False
        self.is_shuffle = False
        self.current_folder: Optional[str] = None

        # Vars
        self.search_var = tk.StringVar()
        self.sort_mode = tk.StringVar(value=SORT_CHOICES[2])
        self.folder_filter = tk.StringVar(value="(All)")
        self.volume = tk.IntVar(value=70)

        # Images
        self._current_img_w = 420
        self._logo_tk = None
        self._logo_pil = None
        self.center_img = None
        self.config_path = Path(__file__).with_name("prajna_config.json")

        # VLC
        self.vlc_instance = None
        self.player = None
        if vlc:
            self.vlc_instance = vlc.Instance()

        # Build UI
        apply_pharmapp_theme(self.root)
        self._build_hero_paned()
        self._build_bottom_filters_bar()
        self._build_progress_row()
        self._build_playlist_expander()

        # Shortcuts
        self.root.bind("<space>", lambda e: self.toggle_play())
        self.root.bind("<Return>", lambda e: self.play_selected())
        self.root.bind("<Control-Right>", lambda e: self.next())
        self.root.bind("<Control-Left>", lambda e: self.prev())
        # Extra shortcuts
        self.root.bind("<Escape>", lambda e: self.clear_filter())
        self.root.bind("<Control-o>", lambda e: self.open_folder())
        self.root.bind("<Control-j>", lambda e: self.open_static_file())
        self.root.bind("<F5>", lambda e: self.rescan_current_folder())
        self.root.bind("s", lambda e: self.stop())
        self.root.bind("r", lambda e: self.toggle_repeat())
        self.root.bind("h", lambda e: self.toggle_shuffle())
        self.root.bind("<Control-Up>",   lambda e: self._bump_volume(+5))
        self.root.bind("<Control-Down>", lambda e: self._bump_volume(-5))
        self.root.bind("<Control-i>", lambda e: self.choose_center_image())

        self.root.after(300, self._tick)

    # ---------- Small helpers ----------
    def _bump_volume(self, delta):
        try:
            v = int(self.volume.get())
        except Exception:
            v = 50
        v = max(0, min(100, v + delta))
        self.volume.set(v)
        self.set_volume()

    # ---------- Build UI ----------
    def _build_hero_paned(self):
        self.hero = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        self.hero.pack(fill=tk.X, padx=6, pady=(8, 4))

        # Left expander
        self.p_left = ttk.Frame(self.hero)
        self.exp_left = Expander(self.p_left, "Left Controls", open_=True)
        self.exp_left.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)
        self._populate_left_controls(self.exp_left.body)
        self.hero.add(self.p_left, weight=1)

        # Center image only (no overlay)
        self.p_center = ttk.Frame(self.hero)
        f = ttk.Frame(self.p_center)
        f.pack(fill=tk.BOTH, expand=True)
        self._load_center_image(f)  # build & auto-load
        self.hero.add(self.p_center, weight=2)

        # Right expander
        self.p_right = ttk.Frame(self.hero)
        self.exp_right = Expander(self.p_right, "Right Controls", open_=True)
        self.exp_right.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)
        self._populate_right_controls(self.exp_right.body)
        self.hero.add(self.p_right, weight=1)

    def _build_bottom_filters_bar(self):
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill=tk.X, padx=8, pady=(0, 4))

        left = tk.Frame(bar, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(left, text="Search:").pack(side=tk.LEFT, padx=(0, 4))
        ent = ttk.Entry(left, textvariable=self.search_var, width=28)
        ent.pack(side=tk.LEFT)
        ent.bind("<KeyRelease>", lambda e: self.apply_filter())

        btn_clear = tk.Button(left, text="Clear [Esc]", command=self.clear_filter)
        style_btn(btn_clear)
        btn_clear.pack(side=tk.LEFT, padx=(6, 12))

        btn_img = tk.Button(left, text="Set Image [Ctrl+I]", command=self.choose_center_image)
        style_btn(btn_img)
        btn_img.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(left, text="Sort:").pack(side=tk.LEFT, padx=(0, 4))
        self.sort_dropdown = ttk.Combobox(
            left, textvariable=self.sort_mode, values=SORT_CHOICES, width=22, state="readonly"
        )
        self.sort_dropdown.pack(side=tk.LEFT)
        self.sort_dropdown.bind("<<ComboboxSelected>>", lambda e: self.resort())

        # Folder filter (only shows if >1 folder)
        self.folder_frame = tk.Frame(left, bg=BG)
        ttk.Label(self.folder_frame, text="Folder:").pack(side=tk.LEFT, padx=(12, 4))
        self.folder_combo = ttk.Combobox(
            self.folder_frame, textvariable=self.folder_filter,
            values=["(All)"], width=24, state="readonly"
        )
        self.folder_combo.pack(side=tk.LEFT)
        self.folder_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filter())

        right = tk.Frame(bar, bg=BG)
        right.pack(side=tk.RIGHT)
        ttk.Label(right, text="Vol:").pack(side=tk.LEFT, padx=(0, 4))
        self.vol_scale = tk.Scale(
            right, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.volume,
            command=self.set_volume, length=240, bg=BG, highlightthickness=0
        )
        self.vol_scale.pack(side=tk.LEFT)
        self.vol_value_lbl = ttk.Label(right, text=str(self.volume.get()))
        self.vol_value_lbl.pack(side=tk.LEFT, padx=(6, 0))

        def _sync_vol(*_):
            self.vol_value_lbl.config(text=str(self.volume.get()))
        self.volume.trace_add("write", lambda *_: _sync_vol())
        _sync_vol()

    def _build_progress_row(self):
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill=tk.X, padx=8, pady=(0, 4))
        self.time_label = ttk.Label(bar, text="00:00 / 00:00")
        self.time_label.pack(side=tk.LEFT)

        self.progress = ttk.Scale(bar, from_=0, to=1000, orient=tk.HORIZONTAL, length=760)
        self.progress.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
        self.progress.bind("<ButtonPress-1>", lambda e: self._on_seek_press())
        self.progress.bind("<ButtonRelease-1>", lambda e: self._on_seek_release())

    def _build_playlist_expander(self):
        wrap = ttk.Frame(self.root)
        wrap.pack(fill=tk.BOTH, expand=True, padx=8, pady=(2, 8))

        self.tv = ttk.Treeview(wrap, columns=("no", "title", "folder", "dur", "size", "mod"), show="headings")
        self.tv.heading("no", text="#")
        self.tv.heading("title", text="Title")
        self.tv.heading("folder", text="Folder")
        self.tv.heading("dur", text="Duration")
        self.tv.heading("size", text="Size")
        self.tv.heading("mod", text="Modified")

        self.tv.column("no", width=40, anchor="center")
        self.tv.column("title", width=480, anchor="w")
        self.tv.column("folder", width=230, anchor="w")
        self.tv.column("dur", width=90, anchor="e")
        self.tv.column("size", width=90, anchor="e")
        self.tv.column("mod", width=150, anchor="center")

        self.tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tv.bind("<Double-1>", lambda e: self.play_selected())

        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tv.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tv.configure(yscrollcommand=sb.set)

    def _populate_left_controls(self, parent):
        btn_open = tk.Button(parent, text="Open Folder [Ctrl+O]", command=self.open_folder)
        btn_open_json = tk.Button(parent, text="Open static.json [Ctrl+J]", command=self.open_static_file)
        btn_rescan = tk.Button(parent, text="Rescan [F5]", command=self.rescan_current_folder)
        for r, b in enumerate((btn_open, btn_open_json, btn_rescan)):
            style_btn(b)
            b.grid(row=r, column=0, padx=2, pady=4, sticky="ew")
        parent.grid_columnconfigure(0, weight=1)

    def _populate_right_controls(self, parent):
        btn_prev = tk.Button(parent, text="Prev [Ctrl+←]", command=self.prev)
        btn_play = tk.Button(parent, text="Play/Pause [Space]", command=self.toggle_play)
        btn_next = tk.Button(parent, text="Next [Ctrl+→]", command=self.next)
        btn_stop = tk.Button(parent, text="Stop [S]", command=self.stop)
        self._btn_repeat = tk.Button(parent, text="Repeat: Off [R]", command=self.toggle_repeat)
        self._btn_shuffle = tk.Button(parent, text="Shuffle: Off [H]", command=self.toggle_shuffle)
        for b in (btn_prev, btn_play, btn_next, btn_stop, self._btn_repeat, self._btn_shuffle):
            style_btn(b)
        btn_prev.grid(row=0, column=0, padx=2, pady=4, sticky="ew")
        btn_play.grid(row=0, column=1, padx=2, pady=4, sticky="ew")
        btn_next.grid(row=0, column=2, padx=2, pady=4, sticky="ew")
        btn_stop.grid(row=1, column=0, padx=2, pady=4, sticky="ew")
        self._btn_repeat.grid(row=1, column=1, padx=2, pady=4, sticky="ew")
        self._btn_shuffle.grid(row=1, column=2, padx=2, pady=4, sticky="ew")
        for c in range(3):
            parent.grid_columnconfigure(c, weight=1)

    # ---------- Image handling ----------
    def _load_center_image(self, parent):
        # Build widget first
        if Image is None or ImageTk is None:
            ph = tk.Label(parent, text="(Install Pillow: pip install pillow)\n"
                                       "Or press Set Image [Ctrl+I]",
                          bg=BG, fg="black", font=("Arial", 12, "bold"), justify="center")
            ph.pack(pady=10)
            self.center_img = ph
            return

        img_path = self._get_saved_image_path() or self._find_default_image()
        if img_path:
            self._set_center_image(img_path, parent)
        else:
            ph = tk.Label(parent, text="Drop buddha.png next to this .py\n"
                                       "or put an image in ./assets\n"
                                       "or use Set Image [Ctrl+I]",
                          bg=BG, fg="black", font=("Arial", 12, "bold"), justify="center")
            ph.pack(pady=10)
            self.center_img = ph

    def _set_center_image(self, img_path: Path, parent_widget=None):
        if Image is None or ImageTk is None:
            return
        try:
            self._logo_pil = Image.open(str(img_path)).convert("RGB")
        except Exception as e:
            messagebox.showerror("Image error", f"Cannot open image:\n{e}")
            return
        self._current_img_w = max(260, min(760, 420))
        im = self._resize_logo(self._current_img_w)
        self._logo_tk = ImageTk.PhotoImage(im)
        if isinstance(self.center_img, tk.Label) and getattr(self.center_img, "winfo_exists", lambda: False)():
            self.center_img.configure(image=self._logo_tk, text="")
        else:
            parent = parent_widget or self.p_center
            self.center_img = tk.Label(parent, image=self._logo_tk, bg=BG, bd=0, highlightthickness=0)
            self.center_img.pack(pady=2)

        container = self.center_img.master
        def _on_cfg(e):
            avail = max(260, e.width - 24)
            target = max(260, min(760, avail))
            if abs(target - self._current_img_w) < 12:
                return
            self._current_img_w = target
            im = self._resize_logo(target)
            self._logo_tk = ImageTk.PhotoImage(im)
            self.center_img.configure(image=self._logo_tk)
        container.bind("<Configure>", _on_cfg, add="+")

    def _resize_logo(self, target_w):
        return self._logo_pil.resize(
            (target_w, int(self._logo_pil.size[1] * target_w / self._logo_pil.size[0])),
            Image.LANCZOS
        )

    def _get_saved_image_path(self) -> Optional[Path]:
        try:
            if self.config_path.exists():
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
                p = Path(data.get("center_image", ""))
                if p.exists() and p.suffix.lower() in IMAGE_EXTS:
                    return p
        except Exception:
            pass
        return None

    def _save_image_path(self, p: Path):
        try:
            data = {"center_image": str(p)}
            self.config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _find_default_image(self) -> Optional[Path]:
        here = Path(__file__).parent
        candidates = [
            here / "buddha.png",
            here / "buddha.jpg",
            here / "logo.png",
            here / "logo.jpg",
        ]
        assets = here / "assets"
        if assets.exists():
            for name in ["buddha.png", "buddha.jpg", "logo.png", "logo.jpg"]:
                candidates.append(assets / name)
            candidates.extend(sorted([p for p in assets.glob("*") if p.suffix.lower() in IMAGE_EXTS], key=lambda x: x.name))
        candidates.extend(sorted([p for p in here.glob("*") if p.suffix.lower() in IMAGE_EXTS], key=lambda x: x.name))
        for p in candidates:
            if p.exists():
                return p
        return None

    def choose_center_image(self):
        initial = Path(self.current_folder or Path(__file__).parent)
        f = filedialog.askopenfilename(
            title="Choose an image",
            initialdir=str(initial),
            filetypes=(("Image files", "*.png;*.jpg;*.jpeg;*.webp;*.gif;*.bmp"), ("All files", "*.*"))
        )
        if not f:
            return
        p = Path(f)
        self._save_image_path(p)
        if Image is None or ImageTk is None:
            messagebox.showinfo("Info", "Pillow not installed. Run: pip install pillow")
            return
        self._set_center_image(p)

    # ---------- Data & View ----------
    def open_folder(self):
        folder = filedialog.askdirectory(title="Select music folder")
        if not folder:
            return
        self.current_folder = folder
        self.scan_folder(folder)
        self.resort()
        self.apply_filter()

    def open_static_file(self):
        here = Path(self.current_folder or Path.cwd())
        f = filedialog.askopenfilename(
            title="Open static.json",
            initialdir=str(here),
            filetypes=(("JSON", "*.json"), ("All", "*.*"))
        )
        if not f:
            return
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as e:
            messagebox.showerror("Invalid JSON", f"Cannot parse:\\n{e}")
            return
        paths = []
        if isinstance(data, list):
            paths = data
        elif isinstance(data, dict) and "files" in data and isinstance(data["files"], list):
            paths = data["files"]
        else:
            messagebox.showwarning("Unsupported", "JSON must be list[str] or {files: list[str]}")
            return
        items = []
        for p in paths:
            p = Path(p)
            if p.suffix.lower() in AUDIO_EXTS and p.exists():
                items.append(self._make_item_from_path(p))
        self.items_all = items
        self.current_folder = str(Path(paths[0]).parent) if paths else None
        self.resort()
        self.apply_filter()

    def rescan_current_folder(self):
        if not self.current_folder:
            return
        self.scan_folder(self.current_folder)
        self.resort()
        self.apply_filter()

    def scan_folder(self, folder: str):
        folder = Path(folder)
        files = []
        for ext in AUDIO_EXTS:
            files.extend(folder.rglob(f"*{ext}"))
        items = []
        for p in files:
            items.append(self._make_item_from_path(p))
        self.items_all = items
        self._refresh_folder_filter_visibility()

    def _refresh_folder_filter_visibility(self):
        folders = sorted({it["folder"] for it in self.items_all})
        if len(folders) > 1:
            values = ["(All)"] + folders
            self.folder_combo.configure(values=values)
            if self.folder_filter.get() not in values:
                self.folder_filter.set("(All)")
            if not self.folder_frame.winfo_ismapped():
                self.folder_frame.pack(side=tk.LEFT)
        else:
            if self.folder_frame.winfo_ismapped():
                self.folder_frame.pack_forget()
            self.folder_filter.set("(All)")

    def _format_bytes(self, n):
        if n <= 0:
            return "0 MB"
        return f"{n/1_000_000:.1f} MB"

    def _format_dt(self, ts):
        if ts <= 0:
            return ""
        lt = time.localtime(ts)
        return time.strftime("%Y-%m-%d %H:%M", lt)

    def _format_dur(self, ms):
        if ms is None or ms <= 0:
            return "—"
        s = int(ms/1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def _make_item_from_path(self, p: Path) -> Dict:
        try:
            st = p.stat()
            mtime = st.st_mtime
            size = st.st_size
        except Exception:
            mtime = 0
            size = 0
        dur = None
        if MutagenFile is not None:
            try:
                mf = MutagenFile(str(p))
                if mf and mf.info and getattr(mf.info, 'length', None):
                    dur = int(float(mf.info.length) * 1000)
            except Exception:
                dur = None
        return {
            "path": str(p),
            "name": p.stem,
            "folder": str(p.parent.name),
            "size": size,
            "mtime": mtime,
            "duration_ms": dur,
        }

    def resort(self):
        key = self.sort_mode.get()
        items = self.items_all[:]
        if key == "Title (A→Z)":
            items.sort(key=lambda x: x["name"].lower())
        elif key == "Title (Z→A)":
            items.sort(key=lambda x: x["name"].lower(), reverse=True)
        elif key == "Modified (Newest)":
            items.sort(key=lambda x: x["mtime"], reverse=True)
        elif key == "Modified (Oldest)":
            items.sort(key=lambda x: x["mtime"])
        elif key == "Size (Large→Small)":
            items.sort(key=lambda x: x["size"], reverse=True)
        elif key == "Size (Small→Large)":
            items.sort(key=lambda x: x["size"])
        elif key == "Duration (Long→Short)":
            items.sort(key=lambda x: (x["duration_ms"] if x["duration_ms"] else -1), reverse=True)
        elif key == "Duration (Short→Long)":
            items.sort(key=lambda x: (x["duration_ms"] if x["duration_ms"] else 10**12))
        self.items_all = items
        self.apply_filter()

    def apply_filter(self):
        q = (self.search_var.get() or "").strip().lower()
        folder = self.folder_filter.get()
        view_idx = []
        for i, it in enumerate(self.items_all):
            if folder and folder != "(All)" and it["folder"] != folder:
                continue
            if q and q not in it["name"].lower():
                continue
            view_idx.append(i)
        self.items_view = view_idx
        self._refresh_tree()

    def _refresh_tree(self):
        self.tv.delete(*self.tv.get_children())
        for n, idx in enumerate(self.items_view, start=1):
            it = self.items_all[idx]
            self.tv.insert("", "end", iid=str(idx), values=(
                n,
                it["name"],
                it["folder"],
                self._format_dur(it["duration_ms"]),
                self._format_bytes(it["size"]),
                self._format_dt(it["mtime"]),
            ))

    def clear_filter(self):
        self.search_var.set("")
        self.folder_filter.set("(All)")
        self.apply_filter()

    # ---------- Playback ----------
    def _ensure_player(self):
        if not vlc:
            messagebox.showwarning(
                "VLC not available",
                "python-vlc is not installed. Install with:\\n\\npip install python-vlc"
            )
            return False
        if not self.player:
            self.player = self.vlc_instance.media_player_new()
            self.player.audio_set_volume(int(self.volume.get()))
        return True

    def selected_view_index(self):
        sel = self.tv.selection()
        if not sel:
            return None
        iid = sel[0]
        try:
            idx = int(iid)
        except Exception:
            return None
        if idx < 0 or idx >= len(self.items_all):
            return None
        return idx

    def play_selected(self):
        idx = self.selected_view_index()
        if idx is None:
            if self.items_view:
                idx = self.items_view[0]
            else:
                return
        self._play_index(idx)

    def _play_index(self, idx):
        if not self._ensure_player():
            return
        self.current_index = idx
        path = self.items_all[idx]["path"]
        if vlc:
            media = self.vlc_instance.media_new(path)
            self.player.set_media(media)
            self.player.play()
        self.root.after(700, lambda: self._maybe_fill_duration(idx))

    def _maybe_fill_duration(self, idx):
        if not vlc or not self.player:
            return
        try:
            length = self.player.get_length()
            if length > 0:
                self.items_all[idx]["duration_ms"] = length
                self._refresh_tree()
        except Exception:
            pass

    def toggle_play(self):
        if not self.player:
            self.play_selected()
            return
        state = self.player.get_state() if vlc else None
        if vlc and state in (vlc.State.Playing, vlc.State.Buffering):
            self.player.pause()
        else:
            self.player.play()

    def stop(self):
        if self.player:
            self.player.stop()

    def _next_index(self):
        if not self.items_all:
            return -1
        if self.is_shuffle:
            if len(self.items_all) > 1:
                cand = random.randrange(0, len(self.items_all))
                while cand == self.current_index:
                    cand = random.randrange(0, len(self.items_all))
                return cand
            return self.current_index
        nxt = (self.current_index + 1) % len(self.items_all)
        if not self.is_repeat and nxt == 0 and self.current_index != -1:
            return -1
        return nxt

    def next(self):
        idx = self._next_index()
        if idx == -1:
            return
        self._play_index(idx)

    def prev(self):
        if not self.items_all:
            return
        if self.is_shuffle:
            cand = random.randrange(0, len(self.items_all))
            self._play_index(cand)
            return
        idx = (self.current_index - 1) % len(self.items_all) if self.current_index != -1 else 0
        self._play_index(idx)

    def toggle_repeat(self):
        self.is_repeat = not self.is_repeat
        self._btn_repeat.config(text=f"Repeat: {'On' if self.is_repeat else 'Off'} [R]")

    def toggle_shuffle(self):
        self.is_shuffle = not self.is_shuffle
        self._btn_shuffle.config(text=f"Shuffle: {'On' if self.is_shuffle else 'Off'} [H]")

    # ---------- Seeking & volume ----------
    def _on_seek_press(self):
        self._seeking = True

    def _on_seek_release(self):
        self._seeking = False
        self.seek()

    def set_volume(self, *_):
        if self.player and vlc:
            try:
                self.player.audio_set_volume(int(self.volume.get()))
            except Exception:
                pass

    def seek(self):
        if not self.player or not vlc:
            return
        try:
            x = float(self.progress.get())
        except Exception:
            return
        pos = x / 1000.0
        pos = max(0.0, min(1.0, pos))
        try:
            self.player.set_position(pos)
        except Exception:
            pass

    # ---------- UI updater ----------
    def _tick(self):
        self._update_progress()
        self.root.after(300, self._tick)

    def _update_progress(self):
        if not self.player or not vlc:
            self.time_label.config(text="00:00 / 00:00")
            return

        length_ms = int(self.player.get_length())
        time_ms = int(self.player.get_time())
        state = self.player.get_state()

        if length_ms > 0 and time_ms >= length_ms - 150 and state == vlc.State.Ended:
            if self.is_repeat or self.is_shuffle or self.current_index + 1 < len(self.items_all):
                self.next()

        def fmt(ms):
            if ms < 0:
                ms = 0
            s = int(ms / 1000)
            m, s = divmod(s, 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

        self.time_label.config(text=f"{fmt(time_ms)} / {fmt(length_ms)}")

        if not getattr(self, "_seeking", False) and length_ms > 0:
            try:
                self.progress.set(max(0, min(1000, int(1000 * time_ms / length_ms))))
            except Exception:
                pass


def set_app_icon(root: tk.Tk):
    """Try set app icon from buddha.ico/png if available next to script."""
    here = Path(__file__).parent
    try:
        if Image is not None and ImageTk is not None:
            icon_png = here / "buddha.png"
            if icon_png.exists():
                img = Image.open(icon_png)
                root.iconphoto(True, ImageTk.PhotoImage(img))
    except Exception:
        pass


def main():
    root = tk.Tk()
    set_app_icon(root)
    app = PrajnaPlayerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrajnaPlayer v9 – Compact + Expanders + static.json resume (folder-optional)

- Ảnh Phật ở giữa, KHÔNG overlay
- Expander trái/phải
- Thanh Search+Sort+Folder (trái) | Volume (phải) ở dưới hero
- Treeview: No. | Title | Folder | Duration | Size | Modified
- Đọc/Ghi static.json (tự khôi phục bài & vị trí phát; hỗ trợ file static.json
  cũ KHÔNG có 'folder' — sẽ suy ra từ 'last_path').

Author: PharmApp (2025)
"""

import os
import time
import json
import random
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ---- optional PIL for image ----
try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

# ---- optional mutagen for duration ----
try:
    import mutagen
    from mutagen import File as MutagenFile
except Exception:
    mutagen = None
    MutagenFile = None

# ---- optional VLC backend ----
try:
    import vlc  # pip install python-vlc
except Exception:
    vlc = None

# ---------- Config ----------
BG = "#fdf5e6"
FG = "#2a2a2a"
BTN_BG = "#f4a261"
BTN_BG_ACTIVE = "#e76f51"
TV_HEAD_BG = "#b5838d"

AUDIO_EXTS = (".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma")
SORT_CHOICES = [
    "Title (A→Z)", "Title (Z→A)",
    "Modified (Newest)", "Modified (Oldest)",
    "Size (Large→Small)", "Size (Small→Large)",
    "Duration (Long→Short)", "Duration (Short→Long)",
]
AUTOPLAY_ON_LOAD = False  # True = tự phát ngay khi khôi phục từ static.json

def script_dir() -> str:
    try:
        return os.path.abspath(os.path.dirname(__file__))
    except Exception:
        return os.getcwd()

def apply_pharmapp_theme(root: tk.Tk) -> None:
    root.configure(bg=BG)
    s = ttk.Style()
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
    s.configure("Treeview", background="white", foreground=FG,
               fieldbackground="white", font=("Arial", 10), rowheight=25)
    s.configure("Treeview.Heading",
               background=TV_HEAD_BG, foreground="white", font=("Arial", 10, "bold"))
    s.map("Treeview", background=[("selected", "#e9c46a")])

def style_btn(b: tk.Button) -> None:
    b.configure(bg=BTN_BG, fg="black",
                activebackground=BTN_BG_ACTIVE, activeforeground="black",
                bd=0, relief=tk.FLAT, font=("Arial", 10, "bold"),
                cursor="hand2", padx=10, pady=6)

# ---------- Simple Expander ----------
class Expander(ttk.Frame):
    def __init__(self, parent, title: str, open_: bool = True):
        super().__init__(parent)
        self._open = tk.BooleanVar(value=open_)
        self._title = title
        self.header = ttk.Button(self, text=self._label(), style="Expander.TButton",
                                 command=self._toggle)
        self.header.pack(fill=tk.X)
        self.body = ttk.Frame(self)
        if open_:
            self.body.pack(fill=tk.BOTH, expand=True)
    def _label(self):
        return f"{'▾' if self._open.get() else '▸'} {self._title}"
    def _toggle(self):
        if self._open.get():
            self.body.forget(); self._open.set(False)
        else:
            self.body.pack(fill=tk.BOTH, expand=True); self._open.set(True)
        self.header.configure(text=self._label())

# ---------- Main App ----------
class PrajnaPlayerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PrajnaPlayer – Compact + Expanders")
        self.root.geometry("1180x760")

        # State
        self.items_all = []     # dicts: path, name, folder, mtime, size, duration_ms
        self.items_view = []    # indices into items_all
        self.current_index = -1
        self.current_folder = None

        self.search_var = tk.StringVar()
        self.sort_mode = tk.StringVar(value=SORT_CHOICES[0])
        self.folder_filter = tk.StringVar(value="(All)")
        self.volume = tk.IntVar(value=70)
        self.progress = tk.DoubleVar(value=0.0)
        self.is_repeat = False
        self.is_shuffle = False
        self._seeking = False

        # static.json path + pending resume
        self.static_path = os.path.join(script_dir(), "static.json")
        self.pending_resume_path = None
        self.pending_resume_ms = None

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

        # Close handler -> save state
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Try load static.json on startup
        self.load_state_from_static(autoplay=AUTOPLAY_ON_LOAD)

        self.root.after(300, self._tick)

    # ---------- UI ----------
    def _build_hero_paned(self):
        self.hero = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        self.hero.pack(fill=tk.X, padx=6, pady=(8, 4))

        # Left expander
        self.p_left = ttk.Frame(self.hero)
        self.exp_left = Expander(self.p_left, "Left Controls", open_=True)
        self.exp_left.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)
        self._populate_left_controls(self.exp_left.body)
        self.hero.add(self.p_left, weight=1)

        # Center image (no overlay)
        self.p_center = ttk.Frame(self.hero)
        f = ttk.Frame(self.p_center)
        f.pack(fill=tk.BOTH, expand=True)
        self._load_center_image(f)
        self.hero.add(self.p_center, weight=3)

        # Right expander
        self.p_right = ttk.Frame(self.hero)
        self.exp_right = Expander(self.p_right, "Playback Controls", open_=True)
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

        btn_clear = tk.Button(left, text="Clear", command=self.clear_filter)
        style_btn(btn_clear)
        btn_clear.pack(side=tk.LEFT, padx=(6, 12))

        ttk.Label(left, text="Sort:").pack(side=tk.LEFT, padx=(0, 4))
        self.sort_dropdown = ttk.Combobox(
            left, textvariable=self.sort_mode, values=SORT_CHOICES, width=22, state="readonly"
        )
        self.sort_dropdown.pack(side=tk.LEFT)
        self.sort_dropdown.bind("<<ComboboxSelected>>", lambda e: self.resort())

        # Folder filter (hiện khi có >1 folder)
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
        def _sync_vol(*_): self.vol_value_lbl.config(text=str(self.volume.get()))
        self.volume.trace_add("write", _sync_vol)

    def _build_progress_row(self):
        row = ttk.Frame(self.root)
        row.pack(fill=tk.X, padx=8, pady=(0, 4))
        self.progress_bar = ttk.Scale(
            row, from_=0, to=1000, orient=tk.HORIZONTAL,
            variable=self.progress, command=self._on_seek_drag
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.time_label = ttk.Label(row, text="00:00 / 00:00")
        self.time_label.pack(side=tk.LEFT, padx=(8, 0))
        self.progress_bar.bind("<ButtonRelease-1>", lambda e: self.seek())

    def _build_playlist_expander(self):
        self.exp_playlist = Expander(self.root, "Playlist", open_=True)
        self.exp_playlist.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        wrap = self.exp_playlist.body
        cols = ("no", "title", "folder", "dur", "size", "mod")
        self.tv = ttk.Treeview(wrap, columns=cols, show="headings", height=12)
        self.tv.heading("no", text="No.")
        self.tv.heading("title", text="Title")
        self.tv.heading("folder", text="Folder")
        self.tv.heading("dur", text="Duration")
        self.tv.heading("size", text="Size")
        self.tv.heading("mod", text="Modified")
        self.tv.column("no", width=48, anchor="e")
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

    # ---------- Controls content ----------
    def _populate_left_controls(self, parent):
        btn_open = tk.Button(parent, text="Open Folder", command=self.open_folder)
        btn_open_json = tk.Button(parent, text="Open static.json", command=self.open_static_file)
        btn_rescan = tk.Button(parent, text="Rescan", command=self.rescan_current_folder)
        for r, b in enumerate((btn_open, btn_open_json, btn_rescan)):
            style_btn(b); b.grid(row=r, column=0, padx=2, pady=4, sticky="ew")
        parent.grid_columnconfigure(0, weight=1)

    def _populate_right_controls(self, parent):
        btn_prev = tk.Button(parent, text="Prev", command=self.prev)
        btn_play = tk.Button(parent, text="Play/Pause", command=self.toggle_play)
        btn_next = tk.Button(parent, text="Next", command=self.next)
        btn_stop = tk.Button(parent, text="Stop", command=self.stop)
        self._btn_repeat = tk.Button(parent, text="Repeat: Off", command=self.toggle_repeat)
        self._btn_shuffle = tk.Button(parent, text="Shuffle: Off", command=self.toggle_shuffle)
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

    # ---------- Image ----------
    def _load_center_image(self, parent):
        self._logo_pil = None
        for name in ("phat_duoc_su_2.png", "phat_duoc_su_2.jpg"):
            p = os.path.join(script_dir(), name)
            if os.path.exists(p) and Image:
                self._logo_pil = Image.open(p); break
        if self._logo_pil is None or ImageTk is None:
            ttk.Label(parent, text="(phat_duoc_su_2.* not found)").pack(pady=4); return
        self._current_img_w = 460
        img = self._resize_logo(self._current_img_w)
        self._logo_tk = ImageTk.PhotoImage(img)
        self.center_img = tk.Label(parent, image=self._logo_tk, bg=BG, bd=0, highlightthickness=0)
        self.center_img.pack(pady=2)
        def _on_cfg(e):
            avail = max(260, e.width - 24)
            target = max(260, min(760, avail))
            if abs(target - self._current_img_w) < 12: return
            self._current_img_w = target
            im = self._resize_logo(target)
            self._logo_tk = ImageTk.PhotoImage(im)
            self.center_img.configure(image=self._logo_tk)
        parent.bind("<Configure>", _on_cfg)
    def _resize_logo(self, target_w):
        return self._logo_pil.resize(
            (target_w, int(self._logo_pil.size[1] * target_w / self._logo_pil.size[0])),
            Image.LANCZOS
        )

    # ---------- Data & View ----------
    def open_folder(self):
        folder = filedialog.askdirectory(title="Select music folder")
        if not folder: return
        self.current_folder = folder
        self.scan_folder(folder); self.resort(); self.apply_filter()

    def rescan_current_folder(self):
        if not self.current_folder:
            messagebox.showinfo("Rescan", "Please choose a folder first."); return
        self.scan_folder(self.current_folder); self.resort(); self.apply_filter()

    def open_static_file(self):
        p = filedialog.askopenfilename(
            title="Open static.json",
            filetypes=[("JSON", "*.json"), ("All Files", "*.*")]
        )
        if not p: return
        self.static_path = p
        self.load_state_from_static(autoplay=AUTOPLAY_ON_LOAD)

    def _probe_duration_ms(self, path: str):
        try:
            if MutagenFile:
                a = MutagenFile(path)
                if a is not None and getattr(a, "info", None) and getattr(a.info, "length", None):
                    return int(a.info.length * 1000)
        except Exception:
            pass
        return -1  # unknown

    def scan_folder(self, folder: str):
        self.items_all.clear()
        for rootdir, _, files in os.walk(folder):
            for fn in files:
                if not fn.lower().endswith(AUDIO_EXTS): continue
                p = os.path.join(rootdir, fn)
                try:
                    mtime = os.path.getmtime(p); size = os.path.getsize(p)
                except Exception:
                    mtime, size = 0.0, 0
                folder_name = os.path.basename(rootdir)
                dur_ms = self._probe_duration_ms(p)
                self.items_all.append({
                    "path": p, "name": fn, "folder": folder_name,
                    "mtime": mtime, "size": size, "duration_ms": dur_ms
                })
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
        return f"{n/1_000_000:.1f} MB" if n > 0 else "0 MB"
    def _format_dt(self, ts):
        if ts <= 0: return ""
        lt = time.localtime(ts); return time.strftime("%Y-%m-%d %H:%M", lt)
    def _format_dur(self, ms):
        if ms is None or ms < 0: return "—"
        s = int(ms/1000); m, s = divmod(s, 60); h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def resort(self):
        key = self.sort_mode.get()
        if key == "Title (A→Z)":
            self.items_all.sort(key=lambda x: x["name"].lower())
        elif key == "Title (Z→A)":
            self.items_all.sort(key=lambda x: x["name"].lower(), reverse=True)
        elif key == "Modified (Newest)":
            self.items_all.sort(key=lambda x: x["mtime"], reverse=True)
        elif key == "Modified (Oldest)":
            self.items_all.sort(key=lambda x: x["mtime"])
        elif key == "Size (Large→Small)":
            self.items_all.sort(key=lambda x: x["size"], reverse=True)
        elif key == "Size (Small→Large)":
            self.items_all.sort(key=lambda x: x["size"])
        elif key == "Duration (Long→Short)":
            self.items_all.sort(key=lambda x: (x["duration_ms"] if x["duration_ms"] >= 0 else -1), reverse=True)
        else:
            self.items_all.sort(key=lambda x: (x["duration_ms"] if x["duration_ms"] >= 0 else 10**12))
        self.apply_filter()

    def apply_filter(self):
        q = self.search_var.get().strip().lower()
        want_folder = self.folder_filter.get()
        self.items_view = []
        self.tv.delete(*self.tv.get_children())

        for i, it in enumerate(self.items_all):
            if want_folder != "(All)" and it["folder"] != want_folder: continue
            if q and (q not in it["name"].lower() and q not in it["folder"].lower()): continue
            view_idx = len(self.items_view) + 1
            self.items_view.append(i)
            self.tv.insert("", "end",
                values=(view_idx, it["name"], it["folder"],
                        self._format_dur(it["duration_ms"]),
                        self._format_bytes(it["size"]),
                        self._format_dt(it["mtime"])))

        # nếu có pending resume → chọn đúng dòng
        if self.pending_resume_path:
            di = self._find_data_index_by_path(self.pending_resume_path)
            if di is not None:
                self._select_view_by_data_index(di)

    def clear_filter(self):
        self.search_var.set(""); self.folder_filter.set("(All)"); self.apply_filter()

    # ---------- static.json load/save ----------
    def load_state_from_static(self, autoplay=False):
        p = self.static_path
        if not os.path.exists(p):
            return
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            messagebox.showwarning("static.json", "Không đọc được static.json"); return

        sess = data.get("last_session", data)  # hỗ trợ file cũ
        last_path = sess.get("last_path")
        folder = sess.get("folder")
        last_index = sess.get("last_index")
        last_pos = sess.get("last_position_ms")

        # Suy ra folder nếu thiếu mà có last_path
        if not folder and last_path:
            folder = os.path.dirname(last_path)

        # Nếu có folder -> scan
        if folder and os.path.isdir(folder):
            self.current_folder = folder
            self.scan_folder(folder); self.resort(); self.apply_filter()
        elif last_path and os.path.exists(last_path):
            # Mở theo thư mục của last_path
            folder = os.path.dirname(last_path)
            self.current_folder = folder
            self.scan_folder(folder); self.resort(); self.apply_filter()
        else:
            # Không có gì để mở
            return

        # Tìm đúng bài
        target_index = None
        if last_path:
            di = self._find_data_index_by_path(last_path)
            if di is not None: target_index = di
        if target_index is None and last_index is not None:
            if 0 <= last_index < len(self.items_all):
                target_index = last_index

        if target_index is not None:
            self._select_view_by_data_index(target_index)
            # lưu pending resume cho lần play tiếp theo
            self.pending_resume_path = self.items_all[target_index]["path"]
            self.pending_resume_ms = int(last_pos) if isinstance(last_pos, (int, float)) else None
            if autoplay:
                self.play_index(target_index)

    def save_state_to_static(self):
        try:
            # lấy thời gian hiện tại nếu đang phát
            pos_ms = 0
            try:
                if self.player and vlc:
                    cur = int(self.player.get_time())
                    if cur > 0: pos_ms = cur
            except Exception:
                pass

            last_path = None; last_index = self.current_index
            if 0 <= self.current_index < len(self.items_all):
                last_path = self.items_all[self.current_index]["path"]

            data = {
                "last_session": {
                    "folder": self.current_folder,
                    "last_path": last_path,
                    "last_index": last_index,
                    "last_position_ms": pos_ms,
                    "timestamp": int(time.time())
                }
            }
            with open(self.static_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            # im lặng nếu ghi lỗi để không cản đóng app
            pass

    def _on_close(self):
        self.save_state_to_static()
        self.root.destroy()

    # ---------- helpers for selection ----------
    def _find_data_index_by_path(self, path):
        norm = os.path.normcase(os.path.abspath(path))
        for i, it in enumerate(self.items_all):
            if os.path.normcase(os.path.abspath(it["path"])) == norm:
                return i
        # fallback: match by filename
        base = os.path.basename(path)
        for i, it in enumerate(self.items_all):
            if it["name"] == base:
                return i
        return None

    def _select_view_by_data_index(self, di):
        try:
            view_row = self.items_view.index(di)
        except ValueError:
            return
        try:
            iid = self.tv.get_children()[view_row]
            self.tv.selection_set(iid)
            self.tv.see(iid)
        except Exception:
            pass

    # ---------- Playback ----------
    def _ensure_player(self):
        if not vlc:
            messagebox.showwarning(
                "VLC not available",
                "python-vlc is not installed. Install with:\n\npip install python-vlc"
            ); return False
        if not self.player:
            self.player = self.vlc_instance.media_player_new()
            self.player.audio_set_volume(int(self.volume.get()))
        return True

    def selected_view_index(self):
        sel = self.tv.selection()
        if not sel: return None
        try:
            vals = self.tv.item(sel[0], "values")
            return int(vals[0]) - 1
        except Exception:
            return None

    def play_selected(self):
        idx_view = self.selected_view_index()
        if idx_view is None or idx_view < 0 or idx_view >= len(self.items_view): return
        self.play_index(self.items_view[idx_view])

    def play_index(self, data_index: int):
        if data_index < 0 or data_index >= len(self.items_all): return
        if not self._ensure_player(): return
        p = self.items_all[data_index]["path"]
        media = self.vlc_instance.media_new(p)
        self.player.set_media(media)
        self.player.play()
        self.current_index = data_index
        # nếu cần resume
        if self.pending_resume_path and os.path.samefile(p, self.pending_resume_path) if os.path.exists(p) else (self.pending_resume_path == p):
            if isinstance(self.pending_resume_ms, (int, float)) and self.pending_resume_ms > 0:
                self._seek_after_start(self.pending_resume_ms)
        # lưu state sơ bộ
        self.save_state_to_static()
        # nếu duration chưa biết -> xin từ VLC
        self.root.after(600, self._maybe_update_duration_from_vlc)

    def _seek_after_start(self, ms):
        # đợi VLC load rồi mới seek
        def do_seek():
            if not self.player or not vlc: return
            length_ms = int(self.player.get_length())
            if length_ms <= 0:
                self.root.after(300, do_seek); return
            pos = max(0.0, min(1.0, ms / max(1, length_ms)))
            self.player.set_position(pos)
            # xong thì bỏ pending
            self.pending_resume_path = None
            self.pending_resume_ms = None
        self.root.after(700, do_seek)

    def _maybe_update_duration_from_vlc(self):
        di = self.current_index
        if di == -1 or not self.player or not vlc: return
        ms = int(self.player.get_length())
        if ms > 0 and self.items_all[di]["duration_ms"] < 0:
            self.items_all[di]["duration_ms"] = ms
            try:
                # cập nhật hàng hiển thị
                for iid in self.tv.get_children(""):
                    vals = self.tv.item(iid, "values")
                    if vals and vals[1] == self.items_all[di]["name"] and vals[2] == self.items_all[di]["folder"]:
                        new_vals = list(vals); new_vals[3] = self._format_dur(ms)
                        self.tv.item(iid, values=new_vals); break
            except Exception:
                pass

    def toggle_play(self):
        if not self.player:
            self.play_selected(); return
        state = self.player.get_state() if vlc else None
        if vlc and state in (vlc.State.Playing, vlc.State.Buffering): self.player.pause()
        else: self.player.play()

    def stop(self):
        if self.player: self.player.stop(); self.save_state_to_static()

    def _next_index(self):
        if not self.items_all: return -1
        if self.is_shuffle:
            if len(self.items_all) > 1:
                cand = random.randrange(0, len(self.items_all))
                while cand == self.current_index:
                    cand = random.randrange(0, len(self.items_all))
                return cand
            return self.current_index
        nxt = (self.current_index + 1) % len(self.items_all)
        if not self.is_repeat and nxt == 0 and self.current_index != -1: return -1
        return nxt

    def next(self):
        if self.current_index == -1 and self.items_all:
            self.play_index(0); return
        ni = self._next_index()
        if ni != -1: self.play_index(ni)

    def prev(self):
        if not self.items_all: return
        if self.is_shuffle: self.next(); return
        pi = (self.current_index - 1) % len(self.items_all) if self.current_index != -1 else 0
        self.play_index(pi)

    def toggle_repeat(self):
        self.is_repeat = not self.is_repeat
        for child in self.exp_right.body.grid_slaves():
            if isinstance(child, tk.Button) and child.cget("text").startswith("Repeat"):
                child.config(text=f"Repeat: {'On' if self.is_repeat else 'Off'}"); break

    def toggle_shuffle(self):
        self.is_shuffle = not self.is_shuffle
        for child in self.exp_right.body.grid_slaves():
            if isinstance(child, tk.Button) and child.cget("text").startswith("Shuffle"):
                child.config(text=f"Shuffle: {'On' if self.is_shuffle else 'Off'}"); break

    def set_volume(self, *_):
        if self.player:
            try: self.player.audio_set_volume(int(self.volume.get()))
            except Exception: pass
        self.save_state_to_static()

    # Seeking
    def _on_seek_drag(self, *_): self._seeking = True
    def seek(self):
        if not self.player or not vlc:
            self._seeking = False; return
        length_ms = int(self.player.get_length())
        if length_ms > 0:
            pos = float(self.progress.get()) / 1000.0
            pos = max(0.0, min(1.0, pos)); self.player.set_position(pos)
            self.save_state_to_static()
        self._seeking = False

    # ---------- UI updater ----------
    def _tick(self):
        self._update_progress()
        self.root.after(300, self._tick)

    def _update_progress(self):
        if not self.player or not vlc:
            self.time_label.config(text="00:00 / 00:00"); return
        length_ms = int(self.player.get_length()); time_ms = int(self.player.get_time())
        state = self.player.get_state()
        if length_ms > 0 and time_ms >= length_ms - 150 and state == vlc.State.Ended:
            if self.is_repeat or self.is_shuffle or self.current_index + 1 < len(self.items_all):
                self.next()
        def fmt(ms):
            if ms < 0: ms = 0
            s = int(ms / 1000); m, s = divmod(s, 60); h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        if length_ms > 0 and not self._seeking:
            pos = self.player.get_position(); self.progress.set(int(pos * 1000.0))
        self.time_label.config(text=f"{fmt(time_ms)} / {fmt(length_ms)}")

# ---------- Main ----------
def main():
    root = tk.Tk()
    app = PrajnaPlayerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

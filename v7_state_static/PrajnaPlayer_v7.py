# PrajnaPlayer using python-vlc (v8)
# - Changes in v8:
#   * static.json ONLY saved inside the opened music folder (no script-side copy).
#   * Safe write for static.json using a folder-local lock file + atomic write (tmp + os.replace).
#   * Per-folder state files next to script: state_<hash>.json . Global pointer "state_recent.json".
#   * CLI flag --read-only-static: never write static.json (Open/Rescan operate read-only).
#
# - Kept from v7/v6/v5:
#   * Optional logo loaded from ./ (same dir as script) if present.
#   * On "Open Folder": if static.json exists, ask to reuse or rescan/overwrite (unless read-only).
#   * Title uses static["title"] (default: folder name) => "<Title> || PrajnaPlayer VLC".
#   * "Rescan" button + F5 hotkey; try to restore current track/position.
#   * Columns: No., Title, Folder, Duration, Size, Modified; search, volume, sort; recurse subfolders.
#   * VLC-based playback + durations; double-click to play.

import os
import json
import random
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import vlc
import time
from datetime import datetime
import argparse
import contextlib
import hashlib

# ===== Paths & Settings =====
def script_dir():
    try:
        return os.path.dirname(__file__)
    except Exception:
        return os.getcwd()

RECENT_FILE = os.path.join(script_dir(), "state_recent.json")  # pointer to last-used folder

SUPPORTED_EXTS = (".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg")
SORT_CHOICES = [
    "Filename A-Z",
    "Filename Z-A",
    "Newest First",
    "Oldest First",
    "Size: Largest First",
    "Size: Smallest First",
]

DEFAULT_STATE = {"folder": "", "index": 0, "volume": 80, "song": "", "position": 0}

def fmt_mmss(seconds):
    if not seconds or seconds <= 0:
        return ""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02}:{s:02}"

def fmt_bytes(n):
    try:
        n = int(n)
    except Exception:
        return ""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"

# ===== Recent pointer (last used folder) =====
def load_recent():
    if os.path.exists(RECENT_FILE):
        try:
            with open(RECENT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"folder": ""}

def save_recent(folder: str):
    try:
        with open(RECENT_FILE, "w", encoding="utf-8") as f:
            json.dump({"folder": folder}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ===== Per-folder state (next to script) =====
def _state_file_for(folder: str):
    if not folder:
        return os.path.join(script_dir(), "state_default.json")
    h = hashlib.sha1(os.path.abspath(folder).encode("utf-8")).hexdigest()[:12]
    return os.path.join(script_dir(), f"state_{h}.json")

def save_state(folder, index, volume, song_path, position_seconds):
    path = _state_file_for(folder)
    payload = {
        "folder": folder,
        "index": index,
        "volume": volume,
        "song": song_path,
        "position": position_seconds
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    # also update recent pointer
    if folder:
        save_recent(folder)

def load_state_for_folder(folder):
    path = _state_file_for(folder)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # fallback default (pre-filled with folder)
    s = DEFAULT_STATE.copy()
    s["folder"] = folder or ""
    return s

# ===== static.json helpers (folder-only) =====
def static_path_for(folder: str) -> str:
    return os.path.join(folder, "static.json")

def read_static_from_file(path: str):
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "tracks" not in data:
            return None
        return data
    except Exception:
        return None

def read_static(folder: str):
    return read_static_from_file(static_path_for(folder))

# --- lock + atomic write ---
@contextlib.contextmanager
def _file_lock(lock_path, timeout=10.0, poll=0.2):
    start = time.time()
    fd = None
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            break
        except FileExistsError:
            if time.time() - start > timeout:
                raise TimeoutError(f"Lock timeout: {lock_path}")
            time.sleep(poll)
    try:
        yield
    finally:
        try:
            if fd is not None:
                os.close(fd)
        except Exception:
            pass
        try:
            os.remove(lock_path)
        except Exception:
            pass

def _atomic_write_json(path, payload):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # atomic on Windows/Unix

def write_static(folder: str, tracks: list, title: str):
    """
    Write ONLY the per-folder static.json, safely (lock + atomic).
    """
    payload = {
        "title": title,
        "base_folder": os.path.abspath(folder),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tracks": []
    }
    for t in tracks:
        payload["tracks"].append({
            "path": t.get("path", ""),
            "title": t.get("title", ""),
            "folder": t.get("folder", ""),
            "size": int(t.get("size") or 0),
            "mtime": float(t.get("mtime") or 0.0),
        })

    lock = os.path.join(folder, "static.lock")
    try:
        with _file_lock(lock, timeout=10.0):
            _atomic_write_json(static_path_for(folder), payload)
    except TimeoutError as te:
        messagebox.showwarning("static.json", f"Timeout acquiring lock:\n{te}")
    except Exception as e:
        messagebox.showwarning("static.json", f"Cannot write static.json:\n{e}")

def build_tracks_from_static(data: dict) -> list:
    out = []
    for item in data.get("tracks", []):
        p = item.get("path", "")
        base = os.path.basename(os.path.dirname(p)) if p else ""
        out.append({
            "path": p,
            "title": item.get("title") or os.path.basename(p),
            "folder": item.get("folder") or base,
            "dur": None,
            "size": int(item.get("size") or 0),
            "mtime": float(item.get("mtime") or 0.0),
        })
    return out

def derive_base_folder_from_static(data: dict) -> str:
    base = data.get("base_folder", "") if isinstance(data, dict) else ""
    if base and os.path.isdir(base):
        return base
    for item in data.get("tracks", []):
        p = item.get("path", "")
        if p and os.path.exists(p):
            return os.path.dirname(p)
    return ""

# ===== UI + Player =====
class PrajnaPlayerUI:
    def __init__(self, sort_mode_arg=None, read_only_static=False):
        self.root = tk.Tk()

        self.read_only_static = read_only_static  # NEW in v8

        # Default Title
        self.app_base_title = "PrajnaPlayer VLC"
        self.root.title(self.app_base_title)
        self.root.geometry("1024x720")

        # Optional logo from ./ (same folder as this script)
        try:
            logo_path = os.path.join(script_dir(), "phat_duoc_su_2.jpg")
            if os.path.exists(logo_path):
                from PIL import Image
                logo_img = Image.open(logo_path)
                scale = 300 / logo_img.size[0]
                logo_img = logo_img.resize((300, int(logo_img.size[1] * scale)), Image.LANCZOS)
                self.logo = ImageTk.PhotoImage(logo_img)
                tk.Label(self.root, image=self.logo).pack(pady=6)
        except Exception as e:
            print("Logo error:", e)

        # Data
        self.tracks = []            # list of dict {path,title,folder,dur,size,mtime}
        self.filtered_indices = None
        self.current_index = 0
        self.duration_total = 1
        self.repeat_mode = False
        self.shuffle_mode = False
        self.volume = tk.IntVar(value=80)
        self.sort_mode = tk.StringVar(value=sort_mode_arg or "Filename A-Z")
        self.music_folder = ""      # set when a folder/static is loaded

        # VLC
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # --- Top controls: Search | Volume | Sort ---
        top = tk.Frame(self.root)
        top.pack(fill=tk.X)
        inner = tk.Frame(top)
        inner.pack()
        for c in range(3):
            inner.grid_columnconfigure(c, weight=1)

        # Search
        self.search_var = tk.StringVar()
        col0 = tk.Frame(inner)
        col0.grid(row=0, column=0, padx=10, pady=(4, 0), sticky="n")
        tk.Label(col0, text="Search").pack()
        search_row = tk.Frame(col0)
        search_row.pack()
        ent = tk.Entry(search_row, textvariable=self.search_var, width=28)
        ent.pack(side=tk.LEFT)
        ent.bind("<KeyRelease>", lambda e: self.apply_filter())
        tk.Button(search_row, text="Clear", command=self.clear_filter).pack(side=tk.LEFT, padx=6)

        # Volume
        col1 = tk.Frame(inner)
        col1.grid(row=0, column=1, padx=10, pady=(4, 0), sticky="n")
        tk.Label(col1, text="Volume").pack()
        self.vol_scale = tk.Scale(col1, from_=0, to=100, orient=tk.HORIZONTAL,
                                  variable=self.volume, command=self.set_volume, length=220)
        self.vol_scale.pack()
        self.vol_value = tk.Label(col1, text=str(self.volume.get()))
        self.vol_value.pack()
        self.volume.trace_add("write", lambda *_: self.vol_value.config(text=str(self.volume.get())))

        # Sort
        col2 = tk.Frame(inner)
        col2.grid(row=0, column=2, padx=10, pady=(4, 0), sticky="n")
        tk.Label(col2, text="Sort by").pack()
        self.sort_dropdown = ttk.Combobox(
            col2, textvariable=self.sort_mode, values=SORT_CHOICES, width=22, state="readonly"
        )
        self.sort_dropdown.pack()
        self.sort_dropdown.bind("<<ComboboxSelected>>", lambda e: self.resort())

        # Buttons row
        fbtn = tk.Frame(self.root)
        fbtn.pack(pady=6)
        tk.Button(fbtn, text="Open Folder", command=self.open_folder).pack(side=tk.LEFT, padx=2)
        tk.Button(fbtn, text="Open static.json", command=self.open_static_file).pack(side=tk.LEFT, padx=2)
        rescan_label = "Rescan (RO)" if self.read_only_static else "Rescan"
        tk.Button(fbtn, text=rescan_label, command=self.rescan_current_folder).pack(side=tk.LEFT, padx=2)
        tk.Button(fbtn, text="Prev", command=self.prev).pack(side=tk.LEFT, padx=2)
        tk.Button(fbtn, text="Play/Pause", command=self.toggle_play).pack(side=tk.LEFT, padx=2)
        tk.Button(fbtn, text="Next", command=self.next).pack(side=tk.LEFT, padx=2)
        tk.Button(fbtn, text="Stop", command=self.stop).pack(side=tk.LEFT, padx=2)
        tk.Button(fbtn, text="Repeat", command=self.toggle_repeat).pack(side=tk.LEFT, padx=2)
        tk.Button(fbtn, text="Shuffle", command=self.toggle_shuffle).pack(side=tk.LEFT, padx=2)

        # Treeview
        cols = ("no", "title", "folder", "length", "size", "mtime")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("no", text="No.")
        self.tree.heading("title", text="Title")
        self.tree.heading("folder", text="Folder")
        self.tree.heading("length", text="Duration")
        self.tree.heading("size", text="Size")
        self.tree.heading("mtime", text="Modified")
        self.tree.column("no", width=50, anchor="center", stretch=False)
        self.tree.column("title", width=420, anchor="w")
        self.tree.column("folder", width=200, anchor="w")
        self.tree.column("length", width=90, anchor="center", stretch=False)
        self.tree.column("size", width=100, anchor="e", stretch=False)
        self.tree.column("mtime", width=140, anchor="center", stretch=False)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.tag_configure("playing", background="#e8f6ff")

        # Progress + time label
        self.progress = tk.DoubleVar()
        self.progress_bar = ttk.Scale(self.root, from_=0, to=100, orient=tk.HORIZONTAL,
                                      variable=self.progress, command=self.seek)
        self.progress_bar.pack(fill=tk.X, padx=8)
        self.time_label = tk.Label(self.root, text="00:00 / 00:00")
        self.time_label.pack()

        # Now Playing
        self.now_playing_var = tk.StringVar(value="Now Playing: —")
        np_wrap = tk.Frame(self.root)
        np_wrap.pack(fill=tk.X)
        tk.Label(np_wrap, textvariable=self.now_playing_var, fg="#0a7").pack(pady=(2, 6))

        # Background updates + state handling
        self.update_loop()
        self.load_previous_state()
        self.periodic_save_state()

        # Hotkeys
        self.root.bind("<F5>", lambda e: self.rescan_current_folder())

    # ===== Title helpers =====
    def set_window_title(self, title_str: str):
        title = title_str.strip() if title_str else self.app_base_title
        self.root.title(f"{title} || {self.app_base_title}")

    def set_window_title_for_folder(self, folder: str):
        data = read_static(folder) if folder else None
        if data and isinstance(data.get("title"), str) and data["title"].strip():
            self.set_window_title(data["title"])
        else:
            self.set_window_title(os.path.basename(folder) if folder else self.app_base_title)

    # ===== Folder & Static loading =====
    def open_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        save_recent(folder)

        sp = static_path_for(folder)
        use_static = False
        if os.path.exists(sp):
            if self.read_only_static:
                # Read-only: always use existing static.json if present
                use_static = True
            else:
                use_static = messagebox.askyesno(
                    "static.json found",
                    "Found static.json in this folder.\n\n"
                    "Yes: Use existing static.json (no rescan)\n"
                    "No:  Rescan folder and overwrite static.json"
                )

        if use_static:
            data = read_static(folder)
            if not data:
                if self.read_only_static:
                    messagebox.showwarning("static.json", "static.json is invalid and read-only mode is on.\nWill scan to memory (no write).")
                    self._scan_no_write(folder)
                else:
                    messagebox.showwarning("static.json", "static.json is invalid. Will scan the folder and write static.json.")
                    self._scan_and_write_static(folder)
            else:
                self._load_from_static_dict(folder, data)
        else:
            if self.read_only_static:
                self._scan_no_write(folder)
            else:
                self._scan_and_write_static(folder)

        if self.tracks:
            self.play_track(0)

    def open_static_file(self):
        path = filedialog.askopenfilename(
            title="Open static.json",
            filetypes=[("Static JSON (static.json)", "static.json"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return
        data = read_static_from_file(path)
        if not data:
            messagebox.showerror("Open static.json", "Invalid static JSON.")
            return

        base = derive_base_folder_from_static(data)
        save_recent(base)
        self._load_from_static_dict(base, data)
        if self.tracks:
            self.play_track(0)

    def _load_from_static_dict(self, folder, data):
        self.tracks = build_tracks_from_static(data)
        self.tracks = [t for t in self.tracks if t.get("path") and os.path.exists(t["path"])]
        self.music_folder = folder or ""
        self.filtered_indices = None
        self.refresh_tree()
        threading.Thread(target=self._fill_durations_bg, daemon=True).start()

        title = data.get("title", "") if isinstance(data, dict) else ""
        if isinstance(title, str) and title.strip():
            self.set_window_title(title)
        else:
            self.set_window_title_for_folder(self.music_folder)

        # load per-folder state (volume/index/position) if available
        st = load_state_for_folder(self.music_folder)
        try:
            self.volume.set(int(st.get("volume", 80)))
        except Exception:
            pass

    def _scan_no_write(self, folder):
        # scan to memory only (read-only mode)
        self.load_tracks(folder)
        self.set_window_title_for_folder(folder)

    def _scan_and_write_static(self, folder):
        self.load_tracks(folder)
        title = os.path.basename(folder)
        if not self.read_only_static:
            write_static(folder, self.tracks, title)
        self.set_window_title_for_folder(folder)

    def load_tracks(self, folder):
        try:
            paths = []
            for root, _, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(SUPPORTED_EXTS):
                        paths.append(os.path.join(root, f))
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open folder:\n{e}")
            return

        # Sorting by chosen mode
        mode = self.sort_mode.get()
        if mode == "Filename A-Z":
            paths.sort()
        elif mode == "Filename Z-A":
            paths.sort(reverse=True)
        elif mode == "Newest First":
            paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        elif mode == "Oldest First":
            paths.sort(key=lambda x: os.path.getmtime(x))
        elif mode == "Size: Largest First":
            paths.sort(key=lambda x: os.path.getsize(x), reverse=True)
        elif mode == "Size: Smallest First":
            paths.sort(key=lambda x: os.path.getsize(x))

        self.tracks = []
        for p in paths:
            try:
                size = os.path.getsize(p)
                mtime = os.path.getmtime(p)
            except Exception:
                size, mtime = 0, 0.0
            self.tracks.append({
                "path": p,
                "title": os.path.basename(p),
                "folder": os.path.basename(os.path.dirname(p)),
                "dur": None,
                "size": size,
                "mtime": mtime
            })

        self.music_folder = folder
        self.filtered_indices = None
        self.refresh_tree()
        threading.Thread(target=self._fill_durations_bg, daemon=True).start()

    def _fill_durations_bg(self):
        """Use VLC to fill missing durations."""
        for idx, item in enumerate(self.tracks):
            if item["dur"] is not None:
                continue
            try:
                media = self.instance.media_new(item["path"])
                media.parse_with_options(vlc.MediaParseFlag.local, timeout=1500)
                dur_ms = media.get_duration()
                dur = (dur_ms or 0) / 1000.0
                item["dur"] = dur if dur > 0 else None
            except Exception:
                item["dur"] = None
            self.root.after(0, lambda i=idx: self._update_row_duration(i))

    # ===== Tree & filtering =====
    def visible_indices(self):
        if self.filtered_indices is not None:
            return self.filtered_indices
        return list(range(len(self.tracks)))

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        vis = self.visible_indices()
        for row_no, idx in enumerate(vis, start=1):
            it = self.tracks[idx]
            iid = str(idx)
            self.tree.insert(
                "", "end", iid=iid, values=(
                    row_no,
                    it["title"],
                    it.get("folder") or "",
                    fmt_mmss(it["dur"]),
                    fmt_bytes(it["size"]),
                    datetime.fromtimestamp(it["mtime"]).strftime("%Y-%m-%d %H:%M"),
                )
            )

    def _update_row_duration(self, index):
        iid = str(index)
        if not self.tree.exists(iid):
            return
        item = self.tracks[index]
        self.tree.set(iid, "length", fmt_mmss(item["dur"]))

    def apply_filter(self):
        q = (self.search_var.get() or "").strip().lower()
        if not q:
            self.filtered_indices = None
        else:
            self.filtered_indices = []
            for i, t in enumerate(self.tracks):
                hay = " ".join([
                    t.get("title") or "",
                    t.get("folder") or "",
                ]).lower()
                if q in hay:
                    self.filtered_indices.append(i)
        self.refresh_tree()

    def clear_filter(self):
        self.search_var.set("")
        self.filtered_indices = None
        self.refresh_tree()

    def resort(self):
        # Only re-scan if a real folder is known
        if self.music_folder and os.path.isdir(self.music_folder):
            self.load_tracks(self.music_folder)
            # Do not auto-write static here; use Rescan to persist (unless read-only).

    # ===== Playback =====
    def play_track(self, index, position=0):
        if not self.tracks:
            return
        self.current_index = index % len(self.tracks)
        media = self.instance.media_new(self.tracks[self.current_index]["path"])
        self.player.set_media(media)
        self.player.play()
        time.sleep(0.2)

        self.duration_total = max(1, self.player.get_length() / 1000.0)
        self.progress_bar.configure(to=self.duration_total)
        try:
            self.player.set_time(int(max(0, float(position)) * 1000))
        except Exception:
            pass
        try:
            self.player.audio_set_volume(self.volume.get())
        except Exception:
            pass

        # highlight
        for iid in self.tree.get_children():
            self.tree.item(iid, tags=())
        cur_iid = str(self.current_index)
        if self.tree.exists(cur_iid):
            self.tree.see(cur_iid)
            self.tree.selection_set(cur_iid)
            self.tree.item(cur_iid, tags=("playing",))

        # Now Playing
        title = self.tracks[self.current_index]["title"]
        self.now_playing_var.set(f"Now Playing: {title}")

        # save per-folder state
        try:
            save_state(self.music_folder, self.current_index, self.volume.get(),
                       self.tracks[self.current_index]["path"], position)
        except Exception:
            pass

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()

    def stop(self):
        try:
            self.player.stop()
        except Exception:
            pass

    def next(self):
        if not self.tracks:
            return
        if self.shuffle_mode:
            self.play_track(random.randint(0, len(self.tracks) - 1))
        else:
            self.play_track(self.current_index + 1)

    def prev(self):
        if self.tracks:
            self.play_track(self.current_index - 1)

    def on_double_click(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        try:
            idx = int(iid)
        except Exception:
            idx = 0
        self.play_track(idx)

    def seek(self, val):
        try:
            self.player.set_time(int(float(val) * 1000))
        except Exception:
            pass

    def set_volume(self, val):
        try:
            self.player.audio_set_volume(int(float(val)))
        except Exception:
            pass

    def toggle_repeat(self):
        self.repeat_mode = not self.repeat_mode
        messagebox.showinfo("Repeat", f"Repeat {'ON' if self.repeat_mode else 'OFF'}")

    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        messagebox.showinfo("Shuffle", f"Shuffle {'ON' if self.shuffle_mode else 'OFF'}")

    # ===== Background loop & periodic save =====
    def update_loop(self):
        def loop():
            while True:
                try:
                    if self.player.is_playing():
                        pos = self.player.get_time() / 1000.0
                        self.progress.set(pos)
                        self.time_label.config(
                            text=f"{fmt_mmss(pos)} / {fmt_mmss(self.duration_total)}"
                        )
                        # auto next on end
                        if self.duration_total > 1 and (self.duration_total - pos) <= 0.8:
                            time.sleep(0.8)
                            if self.repeat_mode:
                                self.play_track(self.current_index)
                            else:
                                self.next()
                    time.sleep(0.4)
                except Exception:
                    time.sleep(0.8)
        threading.Thread(target=loop, daemon=True).start()

    def load_previous_state(self):
        # Use recent pointer to locate last folder, then load its state + static
        recent = load_recent()
        folder = recent.get("folder", "")
        if folder and os.path.isdir(folder):
            try:
                data = read_static(folder)
                if data:
                    self._load_from_static_dict(folder, data)
                else:
                    # No static.json available
                    if self.read_only_static:
                        self._scan_no_write(folder)
                    else:
                        self.load_tracks(folder)
                        write_static(folder, self.tracks, os.path.basename(folder))
                        self.set_window_title_for_folder(folder)

                # load per-folder state and resume
                st = load_state_for_folder(folder)
                self.volume.set(st.get("volume", 80))
                self.play_track(st.get("index", 0), st.get("position", 0))
            except Exception as e:
                print(f"Error loading previous state: {e}")
        else:
            print("No recent folder. Please open a folder or static.json.")

    def periodic_save_state(self):
        try:
            if self.tracks:
                pos = max(0, self.player.get_time() / 1000.0)
                save_state(self.music_folder, self.current_index, self.volume.get(),
                           self.tracks[self.current_index]["path"], pos)
        except Exception:
            pass
        self.root.after(30000, self.periodic_save_state)

    # ===== Rescan =====
    def rescan_current_folder(self):
        """Rescan current music folder and (unless read-only) overwrite static.json; try to restore playback."""
        if not self.music_folder or not os.path.isdir(self.music_folder):
            messagebox.showinfo("Rescan", "No music folder known (open a folder first).")
            return

        if self.read_only_static:
            proceed = messagebox.askyesno(
                "Rescan (Read-Only)",
                "Read-only mode is ON.\nRescan will refresh the list in-memory WITHOUT writing static.json.\n\nProceed?"
            )
            if not proceed:
                return
        else:
            proceed = messagebox.askyesno(
                "Rescan audio",
                "Scan the folder again and overwrite static.json?\n\n"
                "Yes: Continue.\nNo:  Cancel."
            )
            if not proceed:
                return

        # Save current track & position
        last_path = ""
        last_pos = 0.0
        try:
            if self.tracks:
                last_path = self.tracks[self.current_index]["path"]
            last_pos = max(0.0, self.player.get_time() / 1000.0)
        except Exception:
            pass

        try:
            self.stop()
        except Exception:
            pass

        # Rescan
        if self.read_only_static:
            self._scan_no_write(self.music_folder)
        else:
            self._scan_and_write_static(self.music_folder)

        # Try restore
        resume_index = 0
        resume_pos = last_pos
        if last_path and self.tracks:
            def _norm(p):
                return os.path.normcase(os.path.normpath(p))
            try:
                for i, t in enumerate(self.tracks):
                    try:
                        if _norm(t["path"]) == _norm(last_path):
                            resume_index = i
                            break
                    except Exception:
                        continue
                else:
                    resume_pos = 0.0
            except Exception:
                resume_pos = 0.0

        if self.tracks:
            self.play_track(resume_index, position=resume_pos)
        else:
            self.now_playing_var.set("Now Playing: —")
            self.time_label.config(text="00:00 / 00:00")
            self.progress.set(0)

    def run(self):
        self.root.mainloop()

# ===== CLI =====
def parse_args():
    p = argparse.ArgumentParser(description="PrajnaPlayer VLC")
    p.add_argument("--sort", type=str, choices=SORT_CHOICES,
                   help="Sort mode (e.g., 'Filename A-Z', 'Newest First').")
    p.add_argument("--read-only-static", action="store_true",
                   help="Do not write static.json (Open/Rescan operate in-memory only).")
    # convenient shortcuts
    p.add_argument("--filename-az", action="store_true")
    p.add_argument("--filename-za", action="store_true")
    p.add_argument("--newest-first", action="store_true")
    p.add_argument("--oldest-first", action="store_true")
    p.add_argument("--size-largest", action="store_true")
    p.add_argument("--size-smallest", action="store_true")
    args = p.parse_args()

    mode = args.sort
    if args.filename_az:        mode = "Filename A-Z"
    if args.filename_za:        mode = "Filename Z-A"
    if args.newest_first:       mode = "Newest First"
    if args.oldest_first:       mode = "Oldest First"
    if args.size_largest:       mode = "Size: Largest First"
    if args.size_smallest:      mode = "Size: Smallest First"
    return mode, args.read_only_static

if __name__ == "__main__":
    sort_mode_from_cli, read_only_static = parse_args()
    app = PrajnaPlayerUI(sort_mode_arg=sort_mode_from_cli, read_only_static=read_only_static)
    app.run()

# PrajnaPlayer using python-vlc
# - Multi-column view: No., Title, Duration, Size, Modified
# - Highlights the currently playing row + "Now Playing" status label
# - If saved folder is missing -> skip and ask to open a new one
# - If state.json is corrupted -> delete and start fresh
# - Parses track duration in the background via VLC (may appear after 1–2s)

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

# ===== State Manager =====
STATE_FILE = "state.json"
DEFAULT_STATE = {"folder": "", "index": 0, "volume": 80, "song": "", "position": 0}

def save_state(folder, index, volume, song_path, position_seconds):
    """Save playback state to state.json."""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "folder": folder,
                "index": index,
                "volume": volume,
                "song": song_path,
                "position": position_seconds
            }, f, ensure_ascii=False)
    except Exception:
        pass

def load_state():
    """Load state; if JSON is broken, remove and return default."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            try:
                os.remove(STATE_FILE)
                print("⚠️ Corrupted state.json removed. Starting fresh.")
            except Exception:
                pass
            return DEFAULT_STATE.copy()
    return DEFAULT_STATE.copy()

# ===== Helpers =====
def fmt_mmss(seconds):
    """Format seconds -> mm:ss."""
    if not seconds or seconds <= 0:
        return ""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02}:{s:02}"

def fmt_bytes(n):
    """Format bytes -> B/KB/MB/GB."""
    try:
        n = int(n)
    except Exception:
        return ""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"

# ===== UI + Player =====
class PrajnaPlayerUI:
    def __init__(self):
        self.root = tk.Tk()

        # Window title from title.txt (optional)
        try:
            with open("title.txt", "r", encoding="utf-8") as f:
                title_text = f.read().strip()
        except Exception:
            title_text = "PrajnaPlayer VLC"

        self.root.title(f"{title_text} || PrajnaPlayer VLC")
        self.root.geometry("820x640")

        # Logo (optional)
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "phat_duoc_su_2.jpg")
            logo_img = Image.open(logo_path)
            scale = 300 / logo_img.size[0]
            logo_img = logo_img.resize((300, int(logo_img.size[1] * scale)), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(logo_img)
            tk.Label(self.root, image=self.logo).pack(pady=6)
        except Exception as e:
            print("Logo error:", e)

        # Now Playing label
        self.now_playing_var = tk.StringVar(value="Now Playing: —")
        tk.Label(self.root, textvariable=self.now_playing_var, fg="#0a7", anchor="w").pack(fill=tk.X, padx=8)

        # Data
        self.tracks = []       # list of dicts: {path, title, dur, size, mtime}
        self.current_index = 0
        self.duration_total = 1
        self.repeat_mode = False
        self.shuffle_mode = False
        self.volume = tk.IntVar(value=80)
        self.sort_mode = tk.StringVar(value="Newest First")

        # VLC
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # Treeview: No., Title, Duration, Size, Modified
        cols = ("no", "title", "length", "size", "mtime")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("no", text="No.")
        self.tree.heading("title", text="Title")
        self.tree.heading("length", text="Duration")
        self.tree.heading("size", text="Size")
        self.tree.heading("mtime", text="Modified")
        self.tree.column("no", width=60, anchor="center", stretch=False)
        self.tree.column("title", width=420, anchor="w")
        self.tree.column("length", width=90, anchor="center", stretch=False)
        self.tree.column("size", width=110, anchor="e", stretch=False)
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

        # Volume
        vol_frame = tk.Frame(self.root)
        vol_frame.pack()
        tk.Label(vol_frame, text="Volume").pack(side=tk.LEFT)
        tk.Scale(vol_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.volume,
                 command=self.set_volume, length=200).pack(side=tk.LEFT, padx=6)

        # Sort options
        sort_frame = tk.Frame(self.root)
        sort_frame.pack(pady=(4, 2))
        tk.Label(sort_frame, text="Sort by").pack(side=tk.LEFT)
        self.sort_dropdown = ttk.Combobox(
            sort_frame, textvariable=self.sort_mode,
            values=["Newest First", "Filename Z-A", "Filename A-Z", "Oldest First",
                    "Size: Largest First", "Size: Smallest First"],
            width=22, state="readonly"
        )
        self.sort_dropdown.pack(side=tk.LEFT, padx=6)
        self.sort_dropdown.bind("<<ComboboxSelected>>", lambda e: self.resort())

        # Buttons
        self.create_buttons()

        # Background updates + state handling
        self.update_loop()
        self.load_previous_state()
        self.periodic_save_state()

    # ----- Buttons -----
    def create_buttons(self):
        f = tk.Frame(self.root)
        f.pack(pady=4)
        tk.Button(f, text="📁 Open Folder", command=self.open_folder).pack(side=tk.LEFT, padx=2)
        tk.Button(f, text="⏮️ Prev", command=self.prev).pack(side=tk.LEFT, padx=2)
        tk.Button(f, text="▶️ Play/Pause", command=self.toggle_play).pack(side=tk.LEFT, padx=2)
        tk.Button(f, text="⏭️ Next", command=self.next).pack(side=tk.LEFT, padx=2)
        tk.Button(f, text="⏹ Stop", command=self.stop).pack(side=tk.LEFT, padx=2)
        tk.Button(f, text="🔁 Repeat", command=self.toggle_repeat).pack(side=tk.LEFT, padx=2)
        tk.Button(f, text="🔀 Shuffle", command=self.toggle_shuffle).pack(side=tk.LEFT, padx=2)

    # ----- Load data -----
    def open_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.load_tracks(folder)
            if self.tracks:
                self.play_track(0)

    def load_tracks(self, folder):
        """Read audio files and populate the table."""
        try:
            files = [f for f in os.listdir(folder) if f.lower().endswith(('.mp3', '.wav'))]
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open folder:\n{e}")
            return

        paths = [os.path.join(folder, f) for f in files]
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
                "dur": None,      # to be filled later
                "size": size,
                "mtime": mtime
            })
        self.music_folder = folder

        self.refresh_tree()
        threading.Thread(target=self._fill_durations_bg, daemon=True).start()

    def _fill_durations_bg(self):
        """Parse duration with VLC in background; update UI per row."""
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

    def _update_row_duration(self, index):
        iid = str(index)
        if not self.tree.exists(iid):
            return
        item = self.tracks[index]
        self.tree.set(iid, "length", fmt_mmss(item["dur"]))

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for i, it in enumerate(self.tracks, start=1):
            iid = str(i - 1)  # store zero-based index as iid
            self.tree.insert(
                "", "end", iid=iid, values=(
                    i,
                    it["title"],
                    fmt_mmss(it["dur"]),
                    fmt_bytes(it["size"]),
                    datetime.fromtimestamp(it["mtime"]).strftime("%Y-%m-%d %H:%M")
                )
            )

    def resort(self):
        if not getattr(self, "music_folder", None):
            return
        self.load_tracks(self.music_folder)

    # ----- Playback controls -----
    def play_track(self, index, position=0):
        if not self.tracks:
            return
        self.current_index = index % len(self.tracks)
        media = self.instance.media_new(self.tracks[self.current_index]["path"])
        self.player.set_media(media)
        self.player.play()
        time.sleep(0.2)

        # fallback duration from player if metadata not parsed yet
        self.duration_total = max(1, self.player.get_length() / 1000.0)
        self.progress_bar.configure(to=self.duration_total)
        self.player.set_time(int(max(0, float(position)) * 1000))
        self.player.audio_set_volume(self.volume.get())

        # highlight current row
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

        save_state(self.music_folder, self.current_index, self.volume.get(),
                   self.tracks[self.current_index]["path"], position)

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()

    def stop(self):
        self.player.stop()

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

    # ----- Threads & timers -----
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
                        # auto next on track end
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

    # ----- State load/save -----
    def load_previous_state(self):
        st = load_state()
        folder = st.get("folder", "")
        if folder and os.path.isdir(folder):
            try:
                self.load_tracks(folder)
                self.volume.set(st.get("volume", 80))
                self.play_track(st.get("index", 0), st.get("position", 0))
            except Exception as e:
                print(f"⚠️ Error loading previous state: {e}")
        else:
            print("⚠️ Previous folder not found. Please open a new folder.")

    def periodic_save_state(self):
        try:
            if self.tracks:
                pos = max(0, self.player.get_time() / 1000.0)
                save_state(self.music_folder, self.current_index, self.volume.get(),
                           self.tracks[self.current_index]["path"], pos)
        except Exception:
            pass
        self.root.after(30000, self.periodic_save_state)

    # ----- Main loop -----
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PrajnaPlayerUI()
    app.run()

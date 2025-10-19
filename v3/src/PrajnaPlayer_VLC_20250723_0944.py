# PrajnaPlayer with python-vlc
import os
import json
import random
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, ttk
from PIL import Image, ImageTk
import vlc
import time

# ===== State Manager =====
STATE_FILE = "state.json"

def save_state(path, index, volume, song, position):
    with open(STATE_FILE, "w") as f:
        json.dump({
            "folder": path,
            "index": index,
            "volume": volume,
            "song": song,
            "position": position
        }, f)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"folder": "", "index": 0, "volume": 80, "song": "", "position": 0}

# ===== VLC Player Class =====
class PrajnaPlayerUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sư Cô Tâm Tâm || PrajnaPlayer VLC")
        self.root.geometry("500x520")

        try:
            logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "phat_duoc_su_2.jpg")
            logo_img = Image.open(logo_path)
            scale = 300 / logo_img.size[0]
            logo_img = logo_img.resize((300, int(logo_img.size[1] * scale)), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(logo_img)
            tk.Label(self.root, image=self.logo).pack(pady=10)
        except Exception as e:
            print("Logo error:", e)

        self.media_list = []
        self.current_index = 0
        self.duration = 1
        self.repeat_mode = False
        self.shuffle_mode = False
        self.volume = tk.IntVar(value=80)

        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        self.listbox = Listbox(self.root)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind("<Double-1>", self.on_double_click)

        self.progress = tk.DoubleVar()
        self.progress_bar = ttk.Scale(self.root, from_=0, to=100, orient=tk.HORIZONTAL,
                                      variable=self.progress, command=self.seek_music)
        self.progress_bar.pack(fill=tk.X)

        self.time_label = tk.Label(self.root, text="00:00 / 00:00")
        self.time_label.pack()

        volume_frame = tk.Frame(self.root)
        volume_frame.pack()
        tk.Label(volume_frame, text="Volume").pack(side=tk.LEFT)
        tk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.volume,
                 command=self.set_volume, length=150).pack(side=tk.LEFT)

        self.create_buttons()
        self.update_thread()
        self.load_previous_state()
        self.periodic_save_state()

    def create_buttons(self):
        f = tk.Frame(self.root)
        f.pack()
        tk.Button(f, text="📁 Open Folder", command=self.open_folder).pack(side=tk.LEFT)
        tk.Button(f, text="⏮️ Prev", command=self.prev).pack(side=tk.LEFT)
        tk.Button(f, text="▶️ Play/Pause", command=self.toggle_play).pack(side=tk.LEFT)
        tk.Button(f, text="⏭️ Next", command=self.next).pack(side=tk.LEFT)
        tk.Button(f, text="⏹ Stop", command=self.stop).pack(side=tk.LEFT)
        tk.Button(f, text="🔁 Repeat", command=self.toggle_repeat).pack(side=tk.LEFT)
        tk.Button(f, text="🔀 Shuffle", command=self.toggle_shuffle).pack(side=tk.LEFT)

    def open_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.load_music(folder)
            self.play_song(0)

    def load_music(self, folder):
        self.media_list = [f for f in os.listdir(folder) if f.endswith(('.mp3', '.wav'))]
        self.media_list.sort(key=lambda x: int(''.join(filter(str.isdigit, x)) or 0))
        self.media_list = [os.path.join(folder, f) for f in self.media_list]
        self.listbox.delete(0, tk.END)
        for f in self.media_list:
            self.listbox.insert(tk.END, os.path.basename(f))
        self.music_folder = folder

    def play_song(self, index, position=0):
        if not self.media_list:
            return
        self.current_index = index % len(self.media_list)
        media = self.instance.media_new(self.media_list[self.current_index])
        self.player.set_media(media)
        self.player.play()
        time.sleep(0.2)
        self.duration = self.player.get_length() / 1000
        self.progress_bar.configure(to=self.duration)
        self.player.set_time(int(position * 1000))
        self.player.audio_set_volume(self.volume.get())
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.current_index)
        save_state(self.music_folder, self.current_index, self.volume.get(), self.media_list[self.current_index], position)

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()

    def stop(self):
        self.player.stop()

    def next(self):
        if self.shuffle_mode:
            self.play_song(random.randint(0, len(self.media_list)-1))
        else:
            self.play_song(self.current_index + 1)

    def prev(self):
        self.play_song(self.current_index - 1)

    def on_double_click(self, e):
        index = self.listbox.curselection()[0]
        self.play_song(index)

    def seek_music(self, val):
        self.player.set_time(int(float(val) * 1000))

    def set_volume(self, val):
        self.player.audio_set_volume(int(val))

    def toggle_repeat(self):
        self.repeat_mode = not self.repeat_mode
        messagebox.showinfo("Repeat", f"Repeat {'ON' if self.repeat_mode else 'OFF'}")

    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        messagebox.showinfo("Shuffle", f"Shuffle {'ON' if self.shuffle_mode else 'OFF'}")

    def update_thread(self):
        def loop():
            while True:
                if self.player.is_playing():
                    pos = self.player.get_time() / 1000
                    self.progress.set(pos)
                    self.time_label.config(text=f"{self.fmt(pos)} / {self.fmt(self.duration)}")
                    if abs(pos - self.duration) < 1 and self.duration > 1:
                        time.sleep(1)
                        if self.repeat_mode:
                            self.play_song(self.current_index)
                        else:
                            self.next()
                time.sleep(1)
        threading.Thread(target=loop, daemon=True).start()

    def fmt(self, sec):
        return f"{int(sec//60):02}:{int(sec%60):02}"

    def load_previous_state(self):
        state = load_state()
        if state['folder']:
            self.load_music(state['folder'])
            self.volume.set(state.get('volume', 80))
            self.play_song(state.get('index', 0), state.get('position', 0))

    def periodic_save_state(self):
        if self.media_list:
            pos = self.player.get_time() / 1000
            save_state(self.music_folder, self.current_index, self.volume.get(), self.media_list[self.current_index], pos)
        self.root.after(30000, self.periodic_save_state)

    def run(self):
        self.root.mainloop()

# ===== Main =====
if __name__ == "__main__":
    app = PrajnaPlayerUI()
    app.run()

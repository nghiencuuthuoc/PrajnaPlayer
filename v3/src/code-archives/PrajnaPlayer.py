import os
import json
import random
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, ttk
from PIL import Image, ImageTk
import pygame
import re

import warnings
warnings.filterwarnings("ignore")

# ===== State Manager Functions =====
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
    return {"folder": "", "index": 0, "volume": 0.8, "song": "", "position": 0}

# ===== Music Player Class =====
class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.current_song = None
        self.is_paused = False

    def load(self, filepath):
        self.current_song = filepath
        pygame.mixer.music.load(filepath)
        self.is_paused = False

    def play(self):
        pygame.mixer.music.play()
        self.is_paused = False

    def pause(self):
        pygame.mixer.music.pause()
        self.is_paused = True

    def unpause(self):
        pygame.mixer.music.unpause()
        self.is_paused = False

    def stop(self):
        pygame.mixer.music.stop()
        self.is_paused = False

    def is_playing(self):
        return pygame.mixer.music.get_busy() and not self.is_paused

    def is_paused_state(self):
        return self.is_paused

# ===== UI Class =====
class PrajnaPlayerUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sư Cô Tâm Tâm || PrajnaPlayer")
        self.root.geometry("500x520")

        pygame.init()
        pygame.mixer.init()
        self.SONG_END_EVENT = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.SONG_END_EVENT)

        try:
            logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "phat_duoc_su_2.jpg")
            logo_img = Image.open(logo_path)
            original_width, original_height = logo_img.size
            target_width = 300
            scale = target_width / original_width
            target_height = int(original_height * scale)
            logo_img = logo_img.resize((target_width, target_height), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(logo_img)
            self.logo_label = tk.Label(self.root, image=self.logo)
            self.logo_label.pack(pady=10)
        except Exception as e:
            print(f"Error loading logo: {e}")

        self.music_folder = ""
        self.music_files = []
        self.current_index = 0
        self.duration = 1
        self.repeat_mode = False
        self.shuffle_mode = False

        self.player = MusicPlayer()

        self.listbox = Listbox(self.root)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind("<Double-1>", self.on_double_click)

        self.volume = tk.DoubleVar(value=0.8)
        self.progress = tk.DoubleVar()
        self.progress_bar = ttk.Scale(self.root, from_=0, to=100, orient=tk.HORIZONTAL,
                                      variable=self.progress, command=self.seek_music)
        self.progress_bar.pack(fill=tk.X)

        time_frame = tk.Frame(self.root)
        time_frame.pack()
        self.time_label = tk.Label(time_frame, text="00:00 / 00:00")
        self.time_label.pack()

        volume_frame = tk.Frame(self.root)
        volume_frame.pack()
        tk.Label(volume_frame, text="Volume").pack(side=tk.LEFT)
        self.volume_slider = tk.Scale(volume_frame, from_=0, to=1, resolution=0.01, showvalue=0, length=150,
                                       variable=self.volume, orient=tk.HORIZONTAL,
                                       command=self.set_volume)
        self.volume_slider.pack(side=tk.LEFT)

        self.create_buttons()
        self.state_save_interval = 30_000  # 30 giây
        self.load_previous_state()
        self.root.bind("<<SongEnd>>", lambda e: self.auto_play_next())
        self.poll_pygame_event()
        self.update_progress()
        self.periodic_save_state()

    def create_buttons(self):
        btn_frame = tk.Frame(self.root)
        btn_frame.pack()
        tk.Button(btn_frame, text="📁 Open Folder", command=self.select_folder).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="⏮️ Previous", command=self.play_previous).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="▶️ Play/Pause", command=self.toggle_play).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="⏭️ Next", command=self.play_next).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="⏹ Stop", command=self.player.stop).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="🔁 Repeat", command=self.toggle_repeat).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="🔀 Shuffle", command=self.toggle_shuffle).pack(side=tk.LEFT)

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.load_music(path)

    def load_music(self, path):
        def extract_number(filename):
            match = re.search(r'\b(\d{3,})\b', filename)
            return int(match.group(1)) if match else 0

        self.music_folder = path
        files = [f for f in os.listdir(path) if f.endswith(('.mp3', '.wav'))]
        files.sort(key=extract_number)  # Sắp theo số bài tăng dần
        self.music_files = files
        self.listbox.delete(0, tk.END)
        for f in files:
            self.listbox.insert(tk.END, f)

    def play_music(self, index, position=0):
        if 0 <= index < len(self.music_files):
            filepath = os.path.join(self.music_folder, self.music_files[index])
            self.player.load(filepath)
            try:
                self.duration = pygame.mixer.Sound(filepath).get_length()
                self.progress_bar.configure(to=self.duration)
            except:
                self.duration = 1
            pygame.mixer.music.play(start=position)
            if position > 0:
                try:
                    pygame.mixer.music.set_pos(position)
                except:
                    pass
            self.player.is_paused = False
            self.current_index = index
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index)
            save_state(self.music_folder, index, self.volume.get(), self.music_files[index], position)

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
        elif self.player.is_paused_state():
            self.player.unpause()
        else:
            if not self.music_files:
                messagebox.showwarning("No music", "Please select a folder with music.")
                return
            self.play_music(self.current_index)

    def play_next(self):
        self.play_music((self.current_index + 1) % len(self.music_files))

    def play_previous(self):
        self.play_music((self.current_index - 1) % len(self.music_files))

    def load_previous_state(self):
        state = load_state()
        if state["folder"]:
            self.load_music(state["folder"])
            self.current_index = state.get("index", 0)
            vol = state.get("volume", 0.8)
            self.volume.set(vol)
            pygame.mixer.music.set_volume(vol)
            position = state.get("position", 0)
            self.play_music(self.current_index, position=position)
            self.progress.set(position)
            dur = self.duration if hasattr(self, 'duration') else 1
            self.time_label.config(text=f"{self.format_time(position)} / {self.format_time(dur)}")

    def update_progress(self):
        if self.player.is_playing() or self.player.is_paused_state():
            pos = pygame.mixer.music.get_pos() / 1000.0
            if pos < 0: pos = 0
            self.progress.set(pos)
            self.time_label.config(text=f"{self.format_time(pos)} / {self.format_time(self.duration)}")
        self.root.after(1000, self.update_progress)

    def seek_music(self, value):
        if self.music_files:
            try:
                pygame.mixer.music.play(start=float(value))
                pygame.mixer.music.set_pos(float(value))
                self.player.is_paused = False
                save_state(self.music_folder, self.current_index, self.volume.get(), self.music_files[self.current_index], float(value))
            except:
                pass

    def run(self):
        self.root.mainloop()

    def on_double_click(self, event):
        selected = self.listbox.curselection()
        if selected:
            index = selected[0]
            self.play_music(index)

    def set_volume(self, value):
        pygame.mixer.music.set_volume(float(value))
        save_state(self.music_folder, self.current_index, self.volume.get(), self.music_files[self.current_index], self.progress.get())

    def toggle_repeat(self):
        self.repeat_mode = not self.repeat_mode
        msg = "Repeat ON" if self.repeat_mode else "Repeat OFF"
        messagebox.showinfo("Repeat", msg)

    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        msg = "Shuffle ON" if self.shuffle_mode else "Shuffle OFF"
        messagebox.showinfo("Shuffle", msg)

    def format_time(self, seconds):
        mins = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{mins:02d}:{secs:02d}"

    def auto_play_next(self):
        if not self.music_files:
            return
        if self.repeat_mode:
            self.play_music(self.current_index)
        elif self.shuffle_mode:
            next_index = random.randint(0, len(self.music_files) - 1)
            self.play_music(next_index)
        else:
            self.play_next()

    def poll_pygame_event(self):
        for event in pygame.event.get():
            if event.type == self.SONG_END_EVENT:
                self.root.event_generate("<<SongEnd>>", when="tail")
        self.root.after(100, self.poll_pygame_event)

    def periodic_save_state(self):
        pos = pygame.mixer.music.get_pos() / 1000.0
        if pos < 0: pos = 0
        save_state(
            self.music_folder,
            self.current_index,
            self.volume.get(),
            self.music_files[self.current_index] if self.music_files else "",
            pos
        )
        self.root.after(self.state_save_interval, self.periodic_save_state)

# ===== Main entry =====
if __name__ == "__main__":
    app = PrajnaPlayerUI()
    app.run()

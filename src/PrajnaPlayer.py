import os
import json
import random
import time
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, ttk
from PIL import Image, ImageTk
import pygame

# ===== State Manager Functions =====
STATE_FILE = "state.json"

def save_state(path, index):
    with open(STATE_FILE, "w") as f:
        json.dump({"folder": path, "index": index}, f)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"folder": "", "index": 0}

# ===== Music Player Class =====
class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.current_song = None

    def load(self, filepath):
        self.current_song = filepath
        pygame.mixer.music.load(filepath)

    def play(self):
        pygame.mixer.music.play()

    def pause(self):
        pygame.mixer.music.pause()

    def unpause(self):
        pygame.mixer.music.unpause()

    def stop(self):
        pygame.mixer.music.stop()

    def is_playing(self):
        return pygame.mixer.music.get_busy()

# ===== UI Class =====
class PrajnaPlayerUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PrajnaPlayer")
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
        self.load_previous_state()

        self.root.bind("<<SongEnd>>", lambda e: self.auto_play_next())
        self.poll_pygame_event()
        self.update_progress()

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
        self.music_folder = path
        files = [f for f in os.listdir(path) if f.endswith(('.mp3', '.wav'))]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(path, x)), reverse=True)
        self.music_files = files
        self.listbox.delete(0, tk.END)
        for f in files:
            self.listbox.insert(tk.END, f)

    def play_music(self, index):
        if 0 <= index < len(self.music_files):
            filepath = os.path.join(self.music_folder, self.music_files[index])
            self.player.load(filepath)
            try:
                self.duration = pygame.mixer.Sound(filepath).get_length()
                self.progress_bar.configure(to=self.duration)
            except:
                self.duration = 1
            self.player.play()
            self.current_index = index
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index)
            save_state(self.music_folder, index)

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
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
            self.current_index = state["index"]
            self.play_music(self.current_index)

    def update_progress(self):
        if self.player.is_playing():
            pos = pygame.mixer.music.get_pos() / 1000.0
            self.progress.set(pos)
            self.time_label.config(text=f"{self.format_time(pos)} / {self.format_time(self.duration)}")
        self.root.after(1000, self.update_progress)

    def seek_music(self, value):
        if self.music_files:
            try:
                pygame.mixer.music.play(start=float(value))
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

# ===== Main entry =====
if __name__ == "__main__":
    app = PrajnaPlayerUI()
    app.run()

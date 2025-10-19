# PrajnaPlayer

Dual-subtitle media player (EN/VI) built with Tkinter + VLC.  
It auto-pairs English/Vietnamese subtitles, remembers your session per music folder, caches playlist metadata, and shows a random “center image” from your `assets/` folder for a clean, distraction-free look.

---

## ✨ Highlights

- **Dual subtitles (EN + VI)** with multiple pairing strategies:
  - `MyTalk.en.srt` + `MyTalk.vi.srt` or `.vtt`
  - Smart fuzzy match & global sub-index across the opened folder tree
- **Smart-Hold subtitle display**: linger time adapts to text length for better readability
- **Session resume**:
  - `config_state/state_<hash>.json` (per-folder playback position, volume, current track)
  - `config_state/state_recent.json` (last used folder)
- **Static cache** per content folder (`static.json`, atomic write with `static.lock`)
- **Random center image** from `./assets/` (or pick your own)
- **Filters & sorting** (A→Z by default, size/date/duration), folder filter, quick search
- **Lightweight UI** with keyboard shortcuts for a “playlist → play → next” workflow

---

## 🗂️ Runtime & Data Files

```
./PrajnaPlayer_v16.5.2.py
./assets/                 # optional images (prajna.png, buddha.jpg, …)
./config_state/           # auto-created at runtime (portable state)
  ├─ prajna_config.json   # UI + user prefs
  ├─ state_recent.json    # last opened folder pointer
  └─ state_<hash>.json    # one per music folder (resume index/position/volume)
<your-music-folder>/
  ├─ static.json          # cached tracks metadata for fast re-open
  └─ static.lock          # lock for safe/atomic write
```

---

## 📦 Requirements

- **Python 3.9+** (tested on 3.12)
- **VLC runtime** (64-bit recommended)  
  - Install VLC (https://www.videolan.org/vlc/) matching your Python architecture  
  - Or bundle `libvlc.dll`, `libvlccore.dll`, and the `plugins/` folder next to the app/exe
- Python packages:
  ```bash
  pip install python-vlc pillow mutagen
  ```
  (`tkinter` ships with most Python installers. `pillow` is for images; `mutagen` reads durations of audio files.)

---

## 🚀 Quick Start (from source)

```bash
git clone https://github.com/nghiencuuthuoc/PrajnaPlayer.git
cd PrajnaPlayer
python -m venv .venv && .venv\Scripts\activate   # Windows (use `source .venv/bin/activate` on Linux/Mac)
pip install -r requirements.txt                  # or: pip install python-vlc pillow mutagen
python PrajnaPlayer_v16.5.2.py
```

**Use it:**
1. Click **Open Folder** (Ctrl+O) and pick a folder with your audio/video files.
2. PrajnaPlayer scans and (optionally) creates/uses `static.json` in that folder.
3. If subtitles exist, it will auto-load EN/VI pairs; you can fine-tune with **Load Sub** (Ctrl+L).
4. Enjoy playback; your position and preferences will auto-save to `config_state/`.

---

## 🔤 Subtitle Pairing Rules

- **Strict match**: `File.en.srt` + `File.vi.srt` (or `.vtt`) in the same folder
- **Exact by stem**: `MyTalk.mp3` → `MyTalk.en.srt` / `MyTalk.vi.srt`
- **Global sub-index**: looks through the opened folder tree for best matches
- **Fuzzy fallback**: name tokens, YouTube ID hints (`[abc123...]`), etc.

**Adjust timing** with **Delay −5s / +5s** buttons.  
**Smart-Hold** parameters (linger/min/per-char) are configurable in the UI and persisted.

---

## ⌨️ Keyboard Shortcuts

- **Play/Pause**: `Space`  **Play selected**: `Enter`  
- **Next/Prev**: `Ctrl+→` / `Ctrl+←`  **Stop**: `S`  
- **Repeat**: `R`  **Shuffle**: `H`  
- **Open Folder**: `Ctrl+O`  **Open static.json**: `Ctrl+J`  
- **Rescan**: `F5`  **Clear search**: `Esc`  
- **Volume ±5**: `Ctrl+↑` / `Ctrl+↓`  
- **Sub on/off**: `Ctrl+K`  **Load sub**: `Ctrl+L`  
- **Font size**: `Ctrl+=` / `Ctrl++` / `Ctrl+-`  
- **Set center image**: `Ctrl+I`  
- **Toggle side panels**: `Ctrl+1` / `Ctrl+2`  **Toggle playlist**: `Ctrl+3`

---

## ⚙️ Configuration & Persistence

- `config_state/prajna_config.json`: UI options (subtitle font size, delays, autosave interval, allow_write_static, window geometry, selected center image, …)
- `config_state/state_<hash>.json`: per-music-folder state (current index, volume, last position in ms)
- `config_state/state_recent.json`: last used music folder
- `<music-folder>/static.json`: cached track list (path/title/size/mtime/duration), written atomically (`static.lock`)

**Resetting state:** delete files under `config_state/` (and `static.json` in your music folder to force a full rescan).

---

## 🧰 Build a Portable EXE (Windows)

> Works with **PyInstaller**. Two variants:  
> **A. Uses system VLC** (simpler) or **B. Fully portable** (bundle VLC DLLs + plugins).

### A) With system VLC installed

1. Install tools & deps
   ```bash
   pip install pyinstaller python-vlc pillow mutagen
   ```
2. Build (icon optional)
   ```bash
   pyinstaller --noconfirm --clean --onefile --windowed ^
     --name PrajnaPlayer ^
     --icon assets\prajna.ico ^
     --add-data "assets;assets" ^
     PrajnaPlayer_v16.5.2.py
   ```
3. Run `dist\PrajnaPlayer.exe`. Ensure your VLC installation matches Python (64-bit).

### B) Fully portable (bundle VLC runtime)

1. Locate your VLC install, e.g.  
   `C:\Program Files\VideoLAN\VLC\libvlc.dll`  
   `C:\Program Files\VideoLAN\VLC\libvlccore.dll`  
   `C:\Program Files\VideoLAN\VLC\plugins\` (entire folder)

2. Build with VLC DLLs and **plugins folder** included:
   ```bash
   pyinstaller --noconfirm --clean --onefile --windowed ^
     --name PrajnaPlayer ^
     --icon assets\prajna.ico ^
     --add-data "assets;assets" ^
     --add-binary "C:\Program Files\VideoLAN\VLC\libvlc.dll;." ^
     --add-binary "C:\Program Files\VideoLAN\VLC\libvlccore.dll;." ^
     --add-data  "C:\ Program Files\VideoLAN\VLC\plugins;plugins" ^
     PrajnaPlayer_v16.5.2.py
   ```
   The app sets `VLC_PLUGIN_PATH` to `./plugins` at runtime (when frozen), so VLC loads correctly inside the single-file app.

> **Tip:** If you see “VLC not available”, confirm DLL architecture (x64 <-> x86) matches your Python/EXE build.

---

## 🧪 Development Tips

- **Assets first**: put some images (e.g., `prajna.png`, `buddha.jpg`) under `./assets/` so the center image looks nice on first run.
- **Subtitles naming**: prefer strict pairing (`.en.srt` + `.vi.srt`) to guarantee dual-load; fuzzy matching is a fallback.
- **Static cache**: turn **Static write** off if you do not want to touch content folders.
- **Troubleshooting playback**:
  - No audio? Check VLC runtime availability (DLLs & `plugins/` when portable).
  - Resume not working? Ensure `config_state/` is writable; check `state_<hash>.json`.

---

## 📄 License

Choose the license that fits your distribution (MIT/BSD/Apache-2.0, etc.). Add a `LICENSE` file in the repo root.

---

## 🙏 Credits

- VLC/`python-vlc` team and contributors
- Pillow, Mutagen communities
- UI designed for a minimal, focus-first playlist experience

---

## 📷 Screenshots (optional)

_Add screenshots of the main window, playlist, dual subtitles, and settings once available._

# PrajnaPlayer

*A lightweight, keyboard‑friendly desktop audio player built with Python (Tkinter + VLC). It focuses on fast playlist navigation, reliable playback, and a clean UI.*

---

## ✨ Highlights
- Dual subtitles (EN + VI) with multiple pairing strategies and an optional “linger” display for readability.
- Session resume per music folder (`config_state/state_<hash>.json`) and “last folder” pointer (`config_state/state_recent.json`).
- Per‑folder static cache: `static.json` (atomic with `static.lock`) for fast re‑open.
- Random center image from `./assets/` (or choose your own), quick search, filters & sorting (A→Z by default).
- Clean design, responsive keyboard shortcuts.

## 📦 Requirements
- **Python** 3.9+ (tested on 3.12)
- **VLC** runtime (64‑bit recommended)
- Python packages: `python-vlc`, `pillow`, `mutagen`
  - `tkinter` comes with most Python installers
  - `pillow` for images, `mutagen` for audio metadata

> Install deps:
> ```bash
> pip install -r requirements.txt
> ```

## 🚀 Quick Start (Run from source)
```bash
git clone https://github.com/nghiencuuthuoc/PrajnaPlayer.git
cd PrajnaPlayer
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
# source .venv/bin/activate

pip install -r requirements.txt
python PrajnaPlayer_v16.5.2.py
```
Open a folder (Ctrl+O) containing your audio/video files. If subtitles exist, EN/VI pairs will be auto‑loaded; adjust with **Load Sub** (Ctrl+L). State files are auto‑saved under `config_state/`.

## 🧭 Folder layout at runtime
```
PrajnaPlayer/
├─ PrajnaPlayer_v16.5.2.py
├─ assets/                # optional images (prajna.png, buddha.jpg, …)
├─ config_state/          # auto‑created (portable state)
│  ├─ prajna_config.json  # UI + user prefs
│  ├─ state_recent.json   # last opened folder pointer
│  └─ state_<hash>.json   # per music folder (resume index/position/volume)
└─ <your-music-folder>/
   ├─ static.json         # cached track metadata
   └─ static.lock         # safe/atomic write lock
```

## ⌨️ Keyboard shortcuts (compact)
`Space` Play/Pause · `Enter` Play selected · `Ctrl+→/←` Next/Prev · `S` Stop · `R` Repeat · `H` Shuffle  
`Ctrl+O` Open folder · `Ctrl+J` Open `static.json` · `F5` Rescan · `Esc` Clear search  
`Ctrl+↑/↓` Volume ±5 · `Ctrl+K` Sub on/off · `Ctrl+L` Load sub  
`Ctrl+=`/`+`/`−` Font ± · `Ctrl+I` Set center image · `Ctrl+1/2/3` Toggle panels/playlist

## 🏗️ Build a Windows `.exe` (PyInstaller)

> These examples assume **Windows + VLC 64‑bit**. Adjust paths as needed.

1) Create & activate venv, install deps
```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt pyinstaller
```

2) *(Optional)* App icon  
Place `assets\prajna.ico` (your icon) in the repo.

3) Build

**A) Simple build** (VLC must be installed on target PC or copied next to the exe)
- **CMD (multi‑line with carets `^`)**
```bat
pyinstaller --noconfirm --clean --onefile --windowed ^
  --name PrajnaPlayer ^
  --icon assets\prajna.ico ^
  --add-data "assets;assets" ^
  PrajnaPlayer_v16.5.2.py
```
- **PowerShell (single line)**
```powershell
pyinstaller --noconfirm --clean --onefile --windowed --name PrajnaPlayer --icon assets\prajna.ico --add-data "assets;assets" PrajnaPlayer_v16.5.2.py
```

**B) Portable build bundled with VLC** (ship VLC DLLs + plugins)
Copy from your VLC install (e.g., `C:\Program Files\VideoLAN\VLC\`) and place **next to the exe** after build:
```
dist\PrajnaPlayer.exe
dist\vlc\libvlc.dll
dist\vlc\libvlccore.dll
dist\vlc\plugins\   (entire plugins folder)
```
Or embed via PyInstaller:
```bat
pyinstaller --noconfirm --clean --onefile --windowed ^
  --name PrajnaPlayer ^
  --icon assets\prajna.ico ^
  --add-data "assets;assets" ^
  --add-binary "C:\Program Files\VideoLAN\VLC\libvlc.dll;." ^
  --add-binary "C:\Program Files\VideoLAN\VLC\libvlccore.dll;." ^
  --add-data  "C:\Program Files\VideoLAN\VLC\plugins;plugins" ^
  PrajnaPlayer_v16.5.2.py
```

> Tip: Keeping a `vlc\` folder next to the exe is the most robust way to ensure `python-vlc` finds the plugins.

## 📥 Releases
Check the **Releases** page for prebuilt downloads (if available):  
https://github.com/nghiencuuthuoc/PrajnaPlayer/releases

## 🔧 Troubleshooting
- **“VLC not found / no audio”**: Match VLC (x64) with Python/exe architecture. For portable builds, keep `libvlc.dll`, `libvlccore.dll` and the whole `plugins` folder next to the exe.
- **Subtitles don’t pair**: Use filenames like `Talk.en.srt` + `Talk.vi.srt` in the same folder or keep the same stem as the media file.
- **State files**: Look in `config_state/`. Per‑folder state uses a hash of the absolute music‑folder path.

---

**Repository:** https://github.com/nghiencuuthuoc/PrajnaPlayer
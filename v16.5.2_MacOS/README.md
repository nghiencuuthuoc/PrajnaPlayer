# PrajnaPlayer v16.5.2 — README (macOS)

A lightweight desktop player focused on **talks/lectures** with:

- 🎯 **Dual subtitles (EN + VI)** with smart display/hold  
- 🔎 **Global subtitle index** (auto-pairs `*.en.vtt/srt` & `*.vi.vtt/srt`)  
- 🧠 **Session state** auto-save/restore per folder  
- 🗂️ **Static cache** (`static.json`) to speed rescans  
- 🖼️ **Random center image** from `assets/` (+ manual pick)  
- 🔁 **Repeat/Shuffle** and **Title (A→Z)** sorting by default  
- 🧰 **Packaged with VLC** (optional) — runs on machines without VLC installed  

---

## 0) Project structure

```
v16.5.2/
├── assets/                  # images for the center panel (random pick on start)
│   ├── 17_nalanda.png
│   └── phat_duoc_su_2.jpg
├── config_state/            # (dev only) local state while running from source
├── prajna.png               # app artwork (used to make .icns)
├── prajna.ico               # (Windows icon, optional)
└── PrajnaPlayer_v16.5.2.py  # main app
```

> When packaged for macOS, **runtime config/state** is stored at  
> `~/Library/Application Support/PrajnaPlayer/config_state/`

---

## 1) Run from source (macOS)

### Prerequisites
- Python **3.11+** (tested on 3.12)
- `pip install pillow mutagen python-vlc`
- VLC installed (`/Applications/VLC.app`) — *only needed when not bundling VLC.*

### Quick start
```bash
python3 PrajnaPlayer_v16.5.2.py
```

---

## 2) Build a macOS `.app` (recommended)

> This produces `dist/PrajnaPlayer_v16.5.2.app`.  
> We recommend **onedir** (standard macOS bundle). Onefile+windowed is deprecated on macOS.

### 2.1 Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install pyinstaller pillow mutagen python-vlc
```

### 2.2 Create the app icon (`.icns`)
```bash
mkdir -p prajna.iconset
sips -z 16 16     prajna.png --out prajna.iconset/icon_16x16.png
sips -z 32 32     prajna.png --out prajna.iconset/icon_16x16@2x.png
sips -z 32 32     prajna.png --out prajna.iconset/icon_32x32.png
sips -z 64 64     prajna.png --out prajna.iconset/icon_32x32@2x.png
sips -z 128 128   prajna.png --out prajna.iconset/icon_128x128.png
sips -z 256 256   prajna.png --out prajna.iconset/icon_128x128@2x.png
sips -z 256 256   prajna.png --out prajna.iconset/icon_256x256.png
sips -z 512 512   prajna.png --out prajna.iconset/icon_256x256@2x.png
sips -z 512 512   prajna.png --out prajna.iconset/icon_512x512.png
# If you have a 1024x1024 source:
# sips -z 1024 1024 prajna.png --out prajna.iconset/icon_512x512@2x.png
iconutil -c icns prajna.iconset -o prajna.icns
```

### 2.3 Build **with VLC bundled** (no install required on target Macs)
```bash
pyinstaller --noconfirm --clean --windowed \
  --name "PrajnaPlayer_v16.5.2" \
  --icon prajna.icns \
  --add-data "assets:assets" \
  --add-binary "/Applications/VLC.app/Contents/MacOS/lib/libvlc.dylib:." \
  --add-binary "/Applications/VLC.app/Contents/MacOS/lib/libvlccore.dylib:." \
  --add-data  "/Applications/VLC.app/Contents/MacOS/plugins:plugins" \
  ./PrajnaPlayer_v16.5.2.py
```

Result: `dist/PrajnaPlayer_v16.5.2.app`

> **Architectures:** building on Intel → x86_64 app; building on Apple Silicon → arm64 app.  
> For Apple Silicon users receiving an Intel build, the app can run via **Rosetta**.

### 2.4 First-run on macOS (Gatekeeper)
- Move `.app` to **Applications** (drag & drop), then **Right-click → Open → Open** (first run only).  
- To share: zip it
  ```bash
  ditto -c -k --sequesterRsrc --keepParent \
    dist/PrajnaPlayer_v16.5.2.app PrajnaPlayer_v16.5.2-macOS.zip
  ```

### 2.5 (Optional) Code-sign & notarize for distribution
```bash
codesign --force --deep --options runtime \
  --sign "Developer ID Application: Your Name (TEAMID)" \
  dist/PrajnaPlayer_v16.5.2.app

xcrun notarytool submit dist/PrajnaPlayer_v16.5.2.app \
  --keychain-profile "YourProfile" --wait
xcrun stapler staple dist/PrajnaPlayer_v16.5.2.app
```

---

## 3) Usage (in-app)

### Open & play
- **Open folder** of lectures: `Ctrl+O`
- **Open static.json** playlist: `Ctrl+J`
- **Rescan** current folder: `F5`
- **Play/Pause**: `Space`
- **Next/Prev**: `Ctrl+→` / `Ctrl+←`
- **Stop**: `S`

### Subtitles
- Toggle subtitles: `Ctrl+K`
- Load subtitle file manually: `Ctrl+L`
- Delay −/+ 5s: “Delay −5s / +5s” buttons
- Font −/+ : `Ctrl+-` / `Ctrl+=`
- Smart hold: configurable in settings (linger/min hold/per char)

> Auto pairing order:
> 1) exact `file.en.vtt/srt` + `file.vi.vtt/srt` in same folder  
> 2) strict pairs in folder  
> 3) global index (exact base)  
> 4) global index (closest base)  
> 5) fuzzy fallback

### Images
- Random image from `assets/` on start  
- **Random Img** button to shuffle  
- Choose custom image: `Ctrl+I`

### Sorting & filters
- Sort default **Title (A→Z)**
- Search box filters by title
- Folder filter appears automatically when multiple subfolders exist

### Repeat & Shuffle
- Toggle **Repeat**: `R`
- Toggle **Shuffle**: `H`
- When a track ends:  
  - Shuffle → next random track  
  - Repeat → wrap to first when reaching the end  
  - Otherwise → stop at end

---

## 4) State & Config (what gets saved?)

- `~/Library/Application Support/PrajnaPlayer/config_state/`
  - `prajna_config.json` — UI prefs, volumes, subtitle settings, window geometry
  - `state_recent.json` — last opened folder pointer
  - `state_<hash>.json` — per-folder session (current index, position, etc.)

- `static.json` (optional) — a *cache* file saved **in the media folder** to speed up rescans.  
  You can disable writing static via the “Static write” checkbox.

---

## 5) Troubleshooting

- **App opens but playback fails (VLC not found):**  
  We bundle `libvlc.dylib` and plugins via PyInstaller. If your environment is unusual, edit `_prepare_vlc_runtime()` to force the path:
  ```python
  os.environ["PYTHON_VLC_LIB_PATH"] = str(_bundle_dir() / "libvlc.dylib")
  os.environ["VLC_PLUGIN_PATH"] = str((_bundle_dir() / "plugins"))
  ```
  Rebuild the app.

- **PyInstaller warnings about Sparkle/Growl**  
  These are optional VLC plugins; warnings are safe to ignore.

- **Gatekeeper blocks app**  
  Use Right-click → Open the first time, or codesign/notarize (see 2.5).

---

## 6) Development notes

- The app uses a helper `_bundle_dir()` to load assets from PyInstaller’s `_MEIPASS` when bundled.
- Runtime data is written to:
  - macOS: `~/Library/Application Support/PrajnaPlayer/config_state/`
  - Windows/Linux (when running from source): alongside the script/executable in `config_state/`
- When building Windows exe, use `--add-data "assets;assets"` and `--icon prajna.ico`.  
  macOS uses `:` as the data separator and `.icns` for icons.

---

## 7) License

Add your preferred license (e.g., MIT) in `LICENSE`.

---

## 8) Credits

- VLC / libVLC (VideoLAN)  
- `python-vlc`  
- Pillow & Mutagen  
- Tkinter

---

### Badges

```md
[![Made with Python](https://img.shields.io/badge/Python-3.12-blue.svg)]()
[![PyInstaller](https://img.shields.io/badge/Packager-PyInstaller-green)]()
[![macOS](https://img.shields.io/badge/macOS-12%2B-black)]()
```

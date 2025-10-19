# PrajnaPlayer‑V3

A lightweight desktop music player built with **Python + Tkinter + python‑vlc**.  
Version **V3** adds a multi‑column track list, “Now Playing” highlight, powerful sorting, live search, and broader audio format support — while keeping the app portable and fast.

---

## ✨ Features

- **Multi‑format playback:** MP3, WAV, FLAC, M4A, AAC, OGG (via VLC).
- **Rich track table:** columns for **No.**, **Title**, **Artist**, **Album**, **Duration**, **Size**, **Modified**.
- **Live search/filter:** instant filtering by Title/Artist/Album.
- **“Now Playing”** banner + row highlight.
- **Sorting modes:** Newest/Oldest, Filename A‑Z/Z‑A, Size (largest/smallest).
- **Playback controls:** Play/Pause, Stop, Next/Prev, **Repeat** and **Shuffle**.
- **Seek bar** (drag to jump) + **elapsed/total time** display.
- **State persistence:** last folder, song index, volume, and position saved to `state.json` every 30s.
- **Resilience:**
  - If the saved folder is missing → the app skips and asks you to open a new folder.
  - If `state.json` is corrupted → it’s deleted automatically and recreated cleanly.

> ✅ Tip: Track durations may appear after 1–2 seconds while VLC parses metadata in the background.

---

## 🧰 Requirements

- **Python** 3.10+ (3.11/3.12 also OK)
- **VLC** desktop installed (provides `libvlc` that `python‑vlc` binds to)
- Python packages:
  - `python-vlc`
  - `Pillow`
  - `mutagen` *(optional, improves tags & duration parsing)*

Install with:

```bash
# (Recommended) from project root
pip install -r requirements.txt

# Or individually
pip install python-vlc Pillow mutagen
```

> **Windows:** Install VLC from https://www.videolan.org/ and keep the default path.  
> **Linux/macOS:** Use your package manager (e.g., `brew install vlc` on macOS) so `libvlc` is available.

---

## 🚀 Quick Start

### Option A — Run the Python script
```bash
# from the project root
python src/PrajnaPlayer_VLC.py
```
Then click **“📁 Open Folder”** and select your music folder.

### Option B — Use the Windows .BAT launchers
- `PrajnaPlayer_VLC.bat` or localized variants in the root folder.

---

## 🗂️ Project Structure (reference)

Below is the current folder layout captured from `tree.txt`:

```
Folder PATH listing for volume RnD1
Volume serial number is 7618-6B1E
E:.
|   ABOUT.md
|   PrajnaPlayer-Newest.zip
|   PrajnaPlayer_VLC.bat
|   PrajnaPlayer_VLC_FLAC.bat
|   PrajnaPlayer_VLC_PAT.bat
|   PrajnaPlayer_VLC_VN_Newest.bat
|   README.md
|   requirements.txt
|   title.txt
|   tree.txt
|   
+---assets
|       nct_icon.ico
|       nct_logo.png
|       phat.jpg
|       phat_duoc_su.jpg
|       phat_duoc_su_2.jpg
|       
+---code-archives
|       PrajnaPlayer.bat
|       PrajnaPlayer_Filename.bat
|       
+---image
|       screenshot.2025-04-17.PrajnaPlayer.png
|       
\---src
    |   PrajnaPlayer_VLC.py
    |   PrajnaPlayer_VLC_20250723_0944.py
    |   PrajnaPlayer_VLC_20250724_1006.py
    |   PrajnaPlayer_VLC_20250812_0953.py
    |   PrajnaPlayer_VLC_FLAC.py
    |   PrajnaPlayer_VLC_PAT.py
    |   PrajnaPlayer_VLC_VN_Newest.py
    |   theme_pharmapp_tk.py
    |   
    +---code-archives
    |       PrajnaPlayer.py
    |       PrajnaPlayer_20250716_1255.py
    |       PrajnaPlayer_Filename.py
    |       
    \---__pycache__
            theme_pharmapp_tk.cpython-312.pyc
```

Key items:
- `src/PrajnaPlayer_VLC.py` → main (latest) player script.
- `state.json` → auto‑generated; stores last session. Safe to delete if needed (the app will recreate it).
- `title.txt` → optional custom window title (first line used).
- `assets/` → optional images/icons for the header/logo.
- `requirements.txt` → Python dependencies.
- `*.bat` → Windows launchers.

---

## 🛠️ Configuration & Tips

- **Title branding:** Put your custom text in `title.txt` (single line).
- **Default sorting:** “Newest First”. Change via the **Sort by** dropdown.
- **Supported formats:** MP3, WAV, FLAC, M4A, AAC, OGG
- **Metadata:** If `mutagen` is installed, Artist/Album is read when available. Not all files contain tags.
- **Durations:** Filled by Mutagen when possible; otherwise parsed by VLC in the background.

---

## ❓ Troubleshooting

- **“VLC/LibVLC not found”** → Install VLC desktop or ensure `libvlc` is in PATH/LD_LIBRARY_PATH.
- **No audio / some files won’t play** → Your VLC build may lack certain codecs. Update VLC.
- **Duration shows empty** → Wait 1–2 seconds for background parsing; not all files report length.
- **Wrong or missing tags** → The file might not have embedded metadata. Edit tags or install `mutagen`.
- **state.json errors** → The app auto‑removes corrupt state. You can also delete it manually while the app is closed.

---

## 🧾 Changelog (V3)

- Added **Artist** and **Album** columns.
- Added **Search** box (filters Title/Artist/Album live).
- Added **Now Playing** banner and row highlight.
- Broader format support: MP3/WAV/FLAC/M4A/AAC/OGG.
- More sort options and improved default (**Newest First**).
- Robust `state.json` handling (auto‑delete on corruption).
- Safer resume when the previous folder is missing.

---

## 📄 License

MIT (or your preferred license).

---

## 🙏 Credits

- VLC & python‑vlc
- Pillow
- Mutagen
- Tkinter

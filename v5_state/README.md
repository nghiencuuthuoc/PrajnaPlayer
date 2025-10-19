# PrajnaPlayer v5 (PharmApp Edition)

A lightweight, keyboard-friendly desktop audio player built with Python and Tkinter. PrajnaPlayer focuses on fast playlist navigation, reliable playback, and a clean UI that fits the PharmApp aesthetic.

> **Status:** v11 (iterative releases tracked in versioned folders)

---

## ✨ Features

- **Simple, fast UI** – minimal chrome with clear transport controls.
- **Playlist-first workflow** – open a folder and play everything, or load individual files.
- **Session resume** – remembers your last session (e.g., folder, track, position) so you can pick up where you left off via a small state file.
- **Keyboard-friendly** – play/pause, next/previous, seek, and volume adjustments from the keyboard.
- **Portable** – no complex setup; just run the Python script.
- **Open license** – permissive CC0-1.0 so you can adapt it freely.

---

## 🗂 Repository Layout

```
.
├── PrajnaPlayer_v5.py        # Main application entry point
├── state.json                # Lightweight state store for session/UI persistence
├── phat_duoc_su_2.jpg        # Optional artwork used by the UI (sample asset)
├── v6/ v7/ v8/ v9/ v10/ v11/ # Iterative version folders (history / experiments)
└── LICENSE                   # CC0-1.0
```

> Versioned folders (e.g., `v6` … `v11`) contain incremental updates and experiments. The main file (`PrajnaPlayer_v5.py`) is the current launcher.

---

## 🔧 Requirements

- **Python**: 3.8+ (3.10+ recommended)
- **Tkinter**: included with standard Python installers (on Windows/macOS).  
- **(Optional) VLC backend**: If you prefer VLC-based playback, install:
  ```bash
  pip install python-vlc
  ```
  and ensure VLC is installed on your system.

> If you run into backend issues, start with the simplest path: use the included defaults and only add `python-vlc` when you need advanced codecs.

---

## 🚀 Run

```bash
# 1) Clone
git clone https://github.com/nghiencuuthuoc/PharmApp_PrajnaPlayer_v5_v11.git
cd PharmApp_PrajnaPlayer_v5_v11

# 2) (Optional) Create/activate a virtual environment

# 3) Install optional dependency if you want VLC playback
pip install python-vlc

# 4) Launch
python PrajnaPlayer_v5.py
```

---

## ⌨️ Keyboard Hints

PrajnaPlayer is designed to be used mostly from the keyboard. Typical shortcuts include:

- **Space** – Play/Pause  
- **N / P** – Next / Previous track  
- **← / →** – Seek backward / forward  
- **↑ / ↓** – Volume up / down  
- **Ctrl+O** – Open folder  
- **Esc** – Stop / close dialog

> Exact mappings may evolve by version; check on-screen hints or tooltips inside the app.

---

## 💾 Persistence

The app stores a tiny bit of UI/playback state in `state.json` (e.g., last opened folder, last playing track/time, window size). You can safely delete this file to reset the player’s memory.

---

## 🖼 Artwork

`phat_duoc_su_2.jpg` is a sample image used by the UI. You can replace it with your own artwork if you prefer.

---

## 🛠 Development Notes

- Code style favors readability and minimal external dependencies.
- The UI follows the **PharmApp** theme direction (clean, warm tones, space-efficient layout).
- Iterative versions are kept in `v*` folders for clarity and reproducibility.

---

## 🤝 Contributing

Issues and pull requests are welcome—bug fixes, small UX improvements, keybindings, and Windows/Linux packaging scripts are especially helpful.

---

## 📜 License

This project is released under **CC0-1.0** (public domain dedication). See [`LICENSE`](./LICENSE) for details.

---

## 🙏 Acknowledgments

- PharmApp community for design cues and iterative feedback.
- The Python and Tkinter ecosystems.
- Optional VLC playback powered by `python-vlc` + VLC.

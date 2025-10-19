# PrajnaPlayer

*A lightweight, keyboard‑friendly desktop audio player built with Python (Tkinter + VLC). It focuses on fast playlist navigation, reliable playback, and a clean UI.*

---

## English

### ✨ Highlights
- Dual subtitles (EN + VI) with multiple pairing strategies and a smart “linger” display for readability. citeturn3view0  
- Session resume per music folder (`config_state/state_<hash>.json`) and “last folder” pointer (`config_state/state_recent.json`). citeturn3view0  
- Per‑folder static cache: `static.json` (atomic with `static.lock`) for fast re‑open. citeturn3view0  
- Random center image from `./assets/` (or choose your own), quick search, filters & sorting (A→Z by default). citeturn3view0  

### 📦 Requirements
- Python 3.9+ (tested on 3.12) and a VLC runtime (64‑bit recommended). citeturn3view0  
- Python packages: `python-vlc`, `pillow`, `mutagen`. citeturn5view0

> Note: `tkinter` is bundled with most Python installers; `pillow` is for images; `mutagen` reads audio durations. citeturn3view0

### 🚀 Quick Start (Run from source)
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
Open a folder (Ctrl+O) containing your audio/video files. If subtitles exist, EN/VI pairs will be auto‑loaded; adjust with **Load Sub** (Ctrl+L). State is auto‑saved to `config_state/`. citeturn3view0

### 🧭 Folder Layout at Runtime
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
citeturn3view0

### ⌨️ Shortcuts (compact)
Space = Play/Pause · Enter = Play selected · Ctrl+→/← = Next/Prev · S = Stop · R = Repeat · H = Shuffle · Ctrl+O = Open Folder · Ctrl+J = Open `static.json` · F5 = Rescan · Esc = Clear search · Ctrl+↑/↓ = Volume ±5 · Ctrl+K = Sub on/off · Ctrl+L = Load sub · Ctrl+=/+/− = Font ± · Ctrl+I = Set center image · Ctrl+1/2/3 = Toggle panels/playlist. citeturn3view0

### 🏗️ Build a Windows `.exe` (PyInstaller)
> These commands assume you’re on Windows with **VLC 64‑bit** installed at the default path. Adjust paths as needed.

1) **Activate venv & install deps**
```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt pyinstaller
```

2) **Optional: set an app icon**  
Place `assets\prajna.ico` (your icon) in the repo.

3) **Build**  
- **Simple build** (requires VLC installed on the target machine or VLC folder copied next to the exe):
```bash
pyinstaller --noconfirm --clean --onefile --windowed ^
  --name PrajnaPlayer ^
  --icon assets\prajna.ico ^
  --add-data "assets;assets" ^
  PrajnaPlayer_v16.5.2.py
```
- **Bundle VLC runtime** (portable): copy the following from your VLC install and include them. The most robust approach is to ship a `vlc\` folder next to the exe:
```
PrajnaPlayer\dist\PrajnaPlayer.exe
PrajnaPlayer\dist\vlc\libvlc.dll
PrajnaPlayer\dist\vlc\libvlccore.dll
PrajnaPlayer\dist\vlc\plugins\  (entire plugins folder)
```
If you prefer embedding via PyInstaller:
```bash
pyinstaller --noconfirm --clean --onefile --windowed ^
  --name PrajnaPlayer ^
  --icon assets\prajna.ico ^
  --add-data "assets;assets" ^
  --add-binary "C:\Program Files\VideoLAN\VLC\libvlc.dll;." ^
  --add-binary "C:\Program Files\VideoLAN\VLC\libvlccore.dll;." ^
  --add-data  "C:\Program Files\VideoLAN\VLC\plugins;plugins" ^
  PrajnaPlayer_v16.5.2.py
```
> Tip: On first run, keep a `vlc\` folder next to the exe to ensure `python-vlc` can locate plugins.

### 📥 Download (Releases)
Grab ready‑made builds from the **Releases** page when available:  
<https://github.com/nghiencuuthuoc/PrajnaPlayer/releases>  
(As of 2025‑10‑19 there are no published releases yet.) citeturn4view0

### 🔧 Troubleshooting
- **“VLC not found / no audio”**: Make sure VLC architecture (x64) matches Python/your exe. If portable, keep `libvlc.dll`, `libvlccore.dll`, and the `plugins` folder next to the exe. citeturn3view0  
- **Subtitles not pairing**: Check that files follow patterns like `MyTalk.en.srt` + `MyTalk.vi.srt` or keep them in the same folder with a shared stem. citeturn3view0  
- **State files location**: See `config_state/` in the app folder; per‑folder state uses a hash of the absolute music‑folder path. citeturn3view0

---

## Tiếng Việt

### ✨ Điểm nổi bật
- Phụ đề đôi (Anh + Việt) với nhiều cách ghép, hiển thị “giữ chữ” thông minh giúp dễ đọc. citeturn3view0  
- Ghi nhớ phiên làm việc theo từng thư mục nhạc (`config_state/state_<hash>.json`) và thư mục mở gần nhất (`config_state/state_recent.json`). citeturn3view0  
- Cache tĩnh theo từng thư mục nội dung: `static.json` (ghi an toàn với `static.lock`) để mở lại cực nhanh. citeturn3view0  
- Ảnh trung tâm ngẫu nhiên từ `./assets/`, tìm kiếm nhanh, lọc & sắp xếp (mặc định A→Z). citeturn3view0  

### 📦 Yêu cầu
- Python 3.9+ (đã thử trên 3.12) và bộ chạy VLC (khuyến nghị 64‑bit). citeturn3view0  
- Gói Python: `python-vlc`, `pillow`, `mutagen`. citeturn5view0

> Lưu ý: `tkinter` có sẵn trong đa số bản cài Python; `pillow` xử lý ảnh; `mutagen` đọc thời lượng âm thanh. citeturn3view0

### 🚀 Chạy nhanh (từ mã nguồn)
```bash
git clone https://github.com/nghiencuuthuoc/PrajnaPlayer.git
cd PrajnaPlayer
python -m venv .venv
.venv\Scripts\activate   # Windows
# hoặc: source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
python PrajnaPlayer_v16.5.2.py
```
Mở thư mục chứa file audio/video (Ctrl+O). Nếu có phụ đề, app sẽ tự ghép EN/VI; có thể điều chỉnh bằng **Load Sub** (Ctrl+L). Trạng thái được lưu tự động vào `config_state/`. citeturn3view0

### 🧭 Cấu trúc thư mục khi chạy
Xem sơ đồ ở phần English (“Folder Layout at Runtime”). citeturn3view0

### ⌨️ Phím tắt (ngắn gọn)
Space = Play/Pause · Enter = Play mục chọn · Ctrl+→/← = Kế/Trước · S = Dừng · R = Lặp · H = Ngẫu nhiên · Ctrl+O = Mở thư mục · Ctrl+J = Mở `static.json` · F5 = Quét lại · Esc = Xóa tìm · Ctrl+↑/↓ = Âm lượng ±5 · Ctrl+K = Bật/tắt phụ đề · Ctrl+L = Nạp phụ đề · Ctrl+=/+/− = Phóng/Thu chữ · Ctrl+I = Chọn ảnh trung tâm · Ctrl+1/2/3 = Bật/tắt panel/playlist. citeturn3view0

### 🏗️ Đóng gói `.exe` cho Windows (PyInstaller)
1) Kích hoạt môi trường ảo & cài dependency:
```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt pyinstaller
```
2) (Tuỳ chọn) Thêm icon `assets\prajna.ico`  
3) Build:
```bash
pyinstaller --noconfirm --clean --onefile --windowed ^
  --name PrajnaPlayer ^
  --icon assets\prajna.ico ^
  --add-data "assets;assets" ^
  PrajnaPlayer_v16.5.2.py
```
- **Kèm VLC portable**: đặt thư mục `vlc\` cạnh file exe, gồm `libvlc.dll`, `libvlccore.dll` và `plugins\`. Hoặc dùng `--add-binary/--add-data` như ví dụ ở phần English.

### 📥 Tải về (Releases)
Trang phát hành bản dựng sẵn: <https://github.com/nghiencuuthuoc/PrajnaPlayer/releases>  
(Tại 2025‑10‑19 hiện chưa có bản phát hành.) citeturn4view0

### 🔧 Lỗi thường gặp
- **Không tìm thấy VLC / không có âm thanh**: Đảm bảo VLC (x64) khớp kiến trúc với Python/exe. Nếu portable, để `libvlc.dll`, `libvlccore.dll` và thư mục `plugins` cạnh file exe. citeturn3view0  
- **Không ghép được phụ đề**: Đặt tên theo mẫu `MyTalk.en.srt` + `MyTalk.vi.srt` trong cùng thư mục hoặc cùng “stem” với file media. citeturn3view0

---

**Repository:** https://github.com/nghiencuuthuoc/PrajnaPlayer citeturn2view0
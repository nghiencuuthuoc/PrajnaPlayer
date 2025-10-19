# PrajnaPlayer v16.5.2 — README (macOS, Tiếng Việt)

Trình phát nhẹ cho **bài giảng/pháp thoại** với các điểm nổi bật:

- 🎯 **Phụ đề kép EN + VI** (tự ghép cặp, hiển thị thông minh *smart-hold*)
- 🔎 **Chỉ mục phụ đề toàn cục** (tự tìm `*.en.vtt/srt` & `*.vi.vtt/srt`)
- 🧠 **Lưu/khôi phục phiên** theo từng thư mục nghe
- 🗂️ **Bộ nhớ tĩnh** `static.json` để quét nhanh
- 🖼️ **Ảnh trung tâm ngẫu nhiên** từ `assets/` (+ chọn tay)
- 🔁 **Repeat/Shuffle**, **sắp xếp A→Z mặc định**
- 🧰 Có thể **đóng gói kèm VLC** để chạy trên máy không cài VLC

---

## 0) Cấu trúc dự án

```
v16.5.2/
├── assets/                  # ảnh trung tâm (sẽ lấy ngẫu nhiên lúc mở app)
│   ├── 17_nalanda.png
│   └── phat_duoc_su_2.jpg
├── config_state/            # (dev) trạng thái khi chạy từ source
├── prajna.png               # ảnh nguồn tạo icon .icns
├── prajna.ico               # icon cho Windows (tùy chọn)
└── PrajnaPlayer_v16.5.2.py  # mã nguồn chính
```

> Khi đóng gói thành ứng dụng macOS, **cấu hình/trạng thái** được lưu tại:  
> `~/Library/Application Support/PrajnaPlayer/config_state/`

---

## 1) Chạy từ mã nguồn (macOS)

### Yêu cầu
- Python **3.11+** (đã thử 3.12)
- Cài thư viện: `pip install pillow mutagen python-vlc`
- Cài VLC (nếu **không** đóng gói kèm VLC): `/Applications/VLC.app`

### Chạy nhanh
```bash
python3 PrajnaPlayer_v16.5.2.py
```

---

## 2) Đóng gói ứng dụng `.app` cho macOS (khuyến nghị)

> Kết quả: `dist/PrajnaPlayer_v16.5.2.app` — chuẩn **onedir** cho macOS.  
> Lưu ý: chế độ **onefile + windowed** đã bị cảnh báo deprecated trên macOS.

### 2.1 Tạo môi trường & cài gói
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install pyinstaller pillow mutagen python-vlc
```

### 2.2 Tạo icon `.icns` từ `prajna.png`
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
# Nếu nguồn 1024x1024, thêm:
# sips -z 1024 1024 prajna.png --out prajna.iconset/icon_512x512@2x.png
iconutil -c icns prajna.iconset -o prajna.icns
```

### 2.3 Build **kèm VLC** (máy đích không cần cài VLC)
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
Kết quả: `dist/PrajnaPlayer_v16.5.2.app`

> **Kiến trúc CPU:** build trên Intel → app x86_64; build trên Apple Silicon → app arm64.  
> Nếu đưa bản Intel cho máy M1/M2, có thể chạy qua **Rosetta**.

### 2.4 Cài & chạy lần đầu
- Kéo thả `.app` vào **Applications** *(hoặc `cp -R dist/...app /Applications/`)*
- Lần đầu mở: **Right‑click → Open → Open** để vượt Gatekeeper.

### 2.5 Chia sẻ cho người khác (đóng gói .zip)
```bash
ditto -c -k --sequesterRsrc --keepParent \
  dist/PrajnaPlayer_v16.5.2.app PrajnaPlayer_v16.5.2-macOS.zip
```

### 2.6 (Tùy chọn) Ký số & Notarize
```bash
codesign --force --deep --options runtime \
  --sign "Developer ID Application: Your Name (TEAMID)" \
  dist/PrajnaPlayer_v16.5.2.app

xcrun notarytool submit dist/PrajnaPlayer_v16.5.2.app \
  --keychain-profile "YourProfile" --wait
xcrun stapler staple dist/PrajnaPlayer_v16.5.2.app
```

---

## 3) Sử dụng trong ứng dụng

### Mở & phát
- **Open Folder**: `Ctrl+O`
- **Open static.json**: `Ctrl+J`
- **Rescan**: `F5`
- **Play/Pause**: `Space`
- **Next/Prev**: `Ctrl+→` / `Ctrl+←`
- **Stop**: `S`

### Phụ đề
- Bật/tắt phụ đề: `Ctrl+K`
- Nạp file phụ đề: `Ctrl+L`
- Độ trễ −/+ 5s: các nút “Delay −5s / +5s”
- Cỡ chữ −/+ : `Ctrl+-` / `Ctrl+=`
- Smart-hold: điều chỉnh `linger/min hold/per char` trong cài đặt

> Thứ tự tự động ghép phụ đề:
> 1) đúng tên `file.en.vtt/srt` + `file.vi.vtt/srt` cùng thư mục  
> 2) cặp strict trong thư mục  
> 3) chỉ mục toàn cục (đúng base)  
> 4) chỉ mục toàn cục (gần đúng)  
> 5) dò mờ (fuzzy) trong thư mục

### Ảnh trung tâm
- Lấy ngẫu nhiên từ `assets/` khi mở app  
- Nút **Random Img** để đổi nhanh  
- Chọn ảnh tay: `Ctrl+I`

### Sắp xếp & lọc
- Mặc định **Title (A→Z)**
- Ô Search lọc theo tiêu đề
- Bộ lọc thư mục hiện khi có nhiều thư mục con

### Repeat & Shuffle
- **Repeat**: `R`
- **Shuffle**: `H`
- Khi hết bài:
  - Shuffle → chọn ngẫu nhiên bài khác  
  - Repeat → quay lại bài đầu danh sách  
  - Không repeat/shuffle → dừng ở cuối

---

## 4) Lưu cấu hình & trạng thái

- `~/Library/Application Support/PrajnaPlayer/config_state/`
  - `prajna_config.json` — cài đặt UI, âm lượng, phụ đề, kích thước cửa sổ
  - `state_recent.json` — thư mục mở gần nhất
  - `state_<hash>.json` — trạng thái theo thư mục (bài đang nghe, vị trí, …)

- `static.json` — *bộ nhớ tĩnh* (lưu ngay trong thư mục media) để lần sau quét nhanh hơn.  
  Có thể tắt ghi bằng checkbox **Static write**.

---

## 5) Khắc phục sự cố

- **Mở được app nhưng VLC không khởi tạo (hiếm):**  
  Đã bundle `libvlc.dylib` + plugins. Nếu môi trường lạ, thêm vào hàm `_prepare_vlc_runtime()` (nhánh macOS):
  ```python
  os.environ["PYTHON_VLC_LIB_PATH"] = str(_bundle_dir() / "libvlc.dylib")
  os.environ["VLC_PLUGIN_PATH"] = str(_bundle_dir() / "plugins")
  ```
  rồi build lại.

- **Cảnh báo Sparkle/Growl khi build:**  
  Là plugin thông báo của VLC, có thể **bỏ qua**.

- **Gatekeeper chặn mở app:**  
  Right‑click → Open (lần đầu), hoặc ký số & notarize (mục 2.6).

---

## 6) Ghi chú phát triển

- Đọc dữ liệu bundle qua `_bundle_dir()` (PyInstaller `_MEIPASS`).  
- Ghi cấu hình/trạng thái:
  - macOS: `~/Library/Application Support/PrajnaPlayer/config_state/`
  - Windows/Linux (chạy source): ngay cạnh script/exe trong thư mục `config_state/`
- Build Windows: `--add-data "assets;assets"` và `--icon prajna.ico` (Windows dùng dấu `;`, macOS dùng `:`).

---

## 7) Giấy phép

Thêm `LICENSE` (VD: MIT) vào repo.

---

## 8) Ghi công

- VLC / libVLC (VideoLAN)  
- `python-vlc`  
- Pillow & Mutagen  
- Tkinter

---

### Huy hiệu cho GitHub

```md
[![Made with Python](https://img.shields.io/badge/Python-3.12-blue.svg)]()
[![PyInstaller](https://img.shields.io/badge/Packager-PyInstaller-green)]()
[![macOS](https://img.shields.io/badge/macOS-12%2B-black)]()
```

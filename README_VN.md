# PrajnaPlayer (Tiếng Việt)

*Trình phát nhạc/phát thanh trên desktop gọn nhẹ, thân thiện phím tắt, viết bằng Python (Tkinter + VLC). Tập trung vào điều hướng playlist nhanh, phát ổn định và UI đơn giản.*

---

## ✨ Điểm nổi bật
- Phụ đề đôi (Anh + Việt) với nhiều cách ghép, có tuỳ chọn “giữ chữ” để dễ đọc.
- Ghi nhớ phiên theo **từng thư mục nhạc** (`config_state/state_<hash>.json`) và con trỏ **thư mục gần nhất** (`config_state/state_recent.json`).
- Cache tĩnh theo từng thư mục nội dung: `static.json` (ghi an toàn với `static.lock`) giúp mở lại rất nhanh.
- Ảnh trung tâm ngẫu nhiên từ `./assets/`, tìm kiếm nhanh, lọc & sắp xếp (mặc định A→Z).
- Thiết kế gọn, phím tắt phong phú.

## 📦 Yêu cầu
- **Python** 3.9+ (đã thử trên 3.12)
- **VLC** runtime (khuyến nghị 64‑bit)
- Gói Python: `python-vlc`, `pillow`, `mutagen`
  - `tkinter` thường có sẵn trong bộ cài Python
  - `pillow` xử lý ảnh, `mutagen` đọc metadata âm thanh

> Cài đặt thư viện:
> ```bash
> pip install -r requirements.txt
> ```

## 🚀 Chạy nhanh (từ mã nguồn)
```bash
git clone https://github.com/nghiencuuthuoc/PrajnaPlayer.git
cd PrajnaPlayer
python -m venv .venv
.venv\Scripts\activate   # Windows
# hoặc: source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
python PrajnaPlayer_v16.5.2.py
```
Mở thư mục chứa file audio/video (Ctrl+O). Nếu có phụ đề, app sẽ tự ghép EN/VI; có thể điều chỉnh bằng **Load Sub** (Ctrl+L). Trạng thái được lưu tự động vào `config_state/`.

## 🧭 Cấu trúc thư mục khi chạy
```
PrajnaPlayer/
├─ PrajnaPlayer_v16.5.2.py
├─ assets/                # ảnh tuỳ chọn (prajna.png, buddha.jpg, …)
├─ config_state/          # tạo tự động (trạng thái portable)
│  ├─ prajna_config.json  # tuỳ chỉnh UI + thói quen người dùng
│  ├─ state_recent.json   # con trỏ tới thư mục mở gần nhất
│  └─ state_<hash>.json   # trạng thái theo từng thư mục nhạc
└─ <thu-muc-nhac-cua-ban>/
   ├─ static.json         # cache metadata bài hát
   └─ static.lock         # khoá ghi an toàn
```

## ⌨️ Phím tắt (ngắn gọn)
`Space` Play/Pause · `Enter` Phát mục chọn · `Ctrl+→/←` Kế/Trước · `S` Dừng · `R` Lặp · `H` Ngẫu nhiên  
`Ctrl+O` Mở thư mục · `Ctrl+J` Mở `static.json` · `F5` Quét lại · `Esc` Xoá tìm  
`Ctrl+↑/↓` Âm lượng ±5 · `Ctrl+K` Bật/tắt phụ đề · `Ctrl+L` Nạp phụ đề  
`Ctrl+=`/`+`/`−` Phóng/Thu chữ · `Ctrl+I` Chọn ảnh trung tâm · `Ctrl+1/2/3` Bật/tắt panel/playlist

## 🏗️ Đóng gói `.exe` trên Windows (PyInstaller)

> Ví dụ dưới đây dành cho **Windows + VLC 64‑bit**. Hãy điều chỉnh đường dẫn tuỳ máy.

1) Tạo môi trường ảo & cài thư viện
```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt pyinstaller
```

2) *(Tuỳ chọn)* Thêm biểu tượng ứng dụng  
Đặt file `assets\prajna.ico` trong repo.

3) Build

**A) Build đơn giản** (máy đích cần có VLC hoặc bạn copy thư mục VLC cạnh file exe)
- **CMD (nhiều dòng dùng dấu `^`)**
```bat
pyinstaller --noconfirm --clean --onefile --windowed ^
  --name PrajnaPlayer ^
  --icon assets\prajna.ico ^
  --add-data "assets;assets" ^
  PrajnaPlayer_v16.5.2.py
```
- **PowerShell (một dòng)**
```powershell
pyinstaller --noconfirm --clean --onefile --windowed --name PrajnaPlayer --icon assets\prajna.ico --add-data "assets;assets" PrajnaPlayer_v16.5.2.py
```

**B) Build portable kèm VLC** (đóng gói DLL + plugins của VLC)
Chép từ cài đặt VLC (ví dụ `C:\Program Files\VideoLAN\VLC\`) và đặt **cạnh file exe** sau khi build:
```
dist\PrajnaPlayer.exe
dist\vlc\libvlc.dll
dist\vlc\libvlccore.dll
dist\vlc\plugins\   (toàn bộ thư mục plugins)
```
Hoặc nhúng qua PyInstaller:
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

> Mẹo: Cách ổn định nhất là để cả thư mục `vlc\` cạnh file `.exe` để `python-vlc` luôn tìm thấy plugins.

## 📥 Tải bản phát hành (Releases)
Xem trang Releases để tải bản dựng sẵn (nếu có):  
https://github.com/nghiencuuthuoc/PrajnaPlayer/releases

## 🔧 Lỗi thường gặp
- **Không tìm thấy VLC / không có âm thanh**: Bảo đảm kiến trúc VLC (x64) khớp với Python/exe. Nếu build portable, hãy đặt `libvlc.dll`, `libvlccore.dll` và cả thư mục `plugins` cạnh file `.exe`.
- **Không ghép được phụ đề**: Đặt tên theo mẫu `Talk.en.srt` + `Talk.vi.srt` trong cùng thư mục hoặc cùng “stem” với file media.
- **Vị trí lưu trạng thái**: Xem trong `config_state/`. Trạng thái theo thư mục dùng hash từ đường dẫn tuyệt đối của thư mục nhạc.

---

**Repository:** https://github.com/nghiencuuthuoc/PrajnaPlayer
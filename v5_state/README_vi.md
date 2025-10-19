# PrajnaPlayer v5 (Bản PharmApp)

Trình phát âm thanh gọn nhẹ, thân thiện với bàn phím, viết bằng Python + Tkinter. PrajnaPlayer tập trung vào điều khiển nhanh, danh sách phát tiện lợi, và giao diện sạch theo phong cách **PharmApp**.

> **Trạng thái:** v11 (các bản cập nhật tuần tự được lưu trong các thư mục phiên bản).

---

## ✨ Tính năng

- **UI đơn giản & nhanh** – tối giản, nút điều khiển rõ ràng.
- **Luồng làm việc ưu tiên playlist** – mở một thư mục để phát tất cả, hoặc chọn từng tệp.
- **Tiếp tục phiên làm việc** – nhớ thư mục, bài đang phát, thời điểm (seek), kích thước cửa sổ… qua một file trạng thái nhỏ.
- **Thân thiện với bàn phím** – play/pause, next/prev, tua, âm lượng.
- **Portable** – chạy trực tiếp bằng Python, không cấu hình phức tạp.
- **Giấy phép mở** – CC0-1.0, tự do chỉnh sửa và tái sử dụng.

---

## 🗂 Cấu trúc kho mã (ví dụ)

```
.
├── PrajnaPlayer_v5.py        # File chạy chính
├── state.json                # Lưu trạng thái phiên/UI
├── phat_duoc_su_2.jpg        # Ảnh minh hoạ UI (tuỳ chọn)
├── v6/ v7/ v8/ v9/ v10/ v11/ # Thư mục phiên bản theo giai đoạn
└── LICENSE                   # CC0-1.0
```

> Thư mục phiên bản (`v6` … `v11`) chứa các bước cập nhật/thử nghiệm. `PrajnaPlayer_v5.py` là trình chạy hiện tại.

---

## 🔧 Yêu cầu

- **Python**: 3.8+ (khuyến nghị 3.10+)
- **Tkinter**: đi kèm bản cài Python tiêu chuẩn (Windows/macOS).
- **(Tuỳ chọn) VLC backend**: nếu muốn phát qua VLC:
  ```bash
  pip install python-vlc
  ```
  và cài VLC trong hệ thống.

> Nếu gặp vấn đề codec, hãy chạy bản mặc định trước; chỉ cài `python-vlc` khi thật sự cần.

---

## 🚀 Cách chạy

```bash
# 1) Clone
git clone https://github.com/nghiencuuthuoc/PharmApp_PrajnaPlayer_v5_v11.git
cd PharmApp_PrajnaPlayer_v5_v11

# 2) (Tuỳ chọn) Tạo/kích hoạt môi trường ảo

# 3) Cài phụ thuộc VLC nếu muốn
pip install python-vlc

# 4) Khởi chạy
python PrajnaPlayer_v5.py
```

---

## ⌨️ Phím tắt (gợi ý)

- **Space** – Play/Pause  
- **N / P** – Bài kế / Bài trước  
- **← / →** – Tua lùi / Tua tới  
- **↑ / ↓** – Tăng / Giảm âm lượng  
- **Ctrl+O** – Mở thư mục  
- **Esc** – Dừng / Đóng hộp thoại

> Phím tắt có thể thay đổi theo từng phiên bản; xem gợi ý trong ứng dụng nếu có.

---

## 💾 Lưu trạng thái

Ứng dụng lưu một số thông tin nhỏ trong `state.json` (thư mục/bài gần nhất, vị trí phát, kích thước cửa sổ…). Xoá file này nếu muốn “reset” bộ nhớ của ứng dụng.

---

## 🖼 Hình minh hoạ

`phat_duoc_su_2.jpg` là ảnh mẫu dùng trong UI. Bạn có thể thay bằng ảnh riêng.

---

## 🛠 Ghi chú phát triển

- Ưu tiên mã dễ đọc, ít phụ thuộc bên ngoài.
- Giao diện theo chủ đề **PharmApp** (ấm, gọn, tiết kiệm không gian dọc).
- Lưu các bước cập nhật trong thư mục `v*` để dễ tái lập và so sánh.

---

## 🤝 Đóng góp

Chào đón issue và pull request—đặc biệt là sửa lỗi nhỏ, cải thiện UX/phím tắt, và script đóng gói cho Windows/Linux.

---

## 📜 Giấy phép

Phát hành theo **CC0-1.0** (public domain). Xem [`LICENSE`](./LICENSE).

---

## 🙏 Lời cảm ơn

- Cộng đồng PharmApp với các góp ý thiết kế và phản hồi theo phiên bản.
- Hệ sinh thái Python & Tkinter.
- (Tuỳ chọn) Phát qua VLC nhờ `python-vlc` + VLC.

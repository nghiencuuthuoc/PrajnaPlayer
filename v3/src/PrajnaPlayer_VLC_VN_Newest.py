# Trình phát nhạc PrajnaPlayer dùng python-vlc
# - Hiển thị bảng nhiều cột: STT, Tên bài hát, Thời gian, Dung lượng, Ngày giờ
# - Tô sáng bài đang phát + dòng trạng thái "Đang phát"
# - Nếu thư mục trong state.json không còn tồn tại -> bỏ qua, yêu cầu chọn mới
# - Nếu state.json bị hỏng (JSON lỗi) -> tự xóa và khởi tạo lại
# - Tự điền thời lượng bài hát nền bằng VLC (có thể trễ 1–2 giây)

import os
import json
import random
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import vlc
import time
from datetime import datetime

# ===== Quản lý trạng thái =====
TAP_TIN_TRANG_THAI = "state.json"

TRANG_THAI_MAC_DINH = {"folder": "", "index": 0, "volume": 80, "song": "", "position": 0}

def luu_trang_thai(thu_muc, chi_so, am_luong, bai_hat, vi_tri_giay):
    """Lưu trạng thái phát nhạc vào state.json"""
    try:
        with open(TAP_TIN_TRANG_THAI, "w", encoding="utf-8") as f:
            json.dump({
                "folder": thu_muc,
                "index": chi_so,
                "volume": am_luong,
                "song": bai_hat,
                "position": vi_tri_giay
            }, f, ensure_ascii=False)
    except Exception:
        pass

def tai_trang_thai():
    """Tải trạng thái; nếu JSON hỏng thì xóa và trả về mặc định"""
    if os.path.exists(TAP_TIN_TRANG_THAI):
        try:
            with open(TAP_TIN_TRANG_THAI, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            try:
                os.remove(TAP_TIN_TRANG_THAI)
                print("⚠️ state.json bị hỏng, đã xóa. Khởi tạo mới.")
            except Exception:
                pass
            return TRANG_THAI_MAC_DINH.copy()
    return TRANG_THAI_MAC_DINH.copy()

# ===== Hàm tiện ích =====
def dinh_dang_thoi_gian(giay):
    """Định dạng giây -> mm:ss"""
    if not giay or giay <= 0:
        return ""
    m = int(giay // 60)
    s = int(giay % 60)
    return f"{m:02}:{s:02}"

def dinh_dang_dung_luong(bytes_):
    """Định dạng bytes -> B/KB/MB/GB"""
    try:
        n = int(bytes_)
    except Exception:
        return ""
    for dv in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.0f} {dv}" if dv == "B" else f"{n:.1f} {dv}"
        n /= 1024.0
    return f"{n:.1f} PB"

# ===== Lớp giao diện & phát nhạc =====
class PrajnaPlayerUI:
    def __init__(self):
        self.root = tk.Tk()

        # Tiêu đề từ file title.txt (nếu có)
        try:
            with open("title.txt", "r", encoding="utf-8") as f:
                tieu_de = f.read().strip()
        except Exception:
            tieu_de = "PrajnaPlayer VLC"

        self.root.title(f"{tieu_de} || PrajnaPlayer VLC")
        self.root.geometry("820x640")

        # Logo (tùy chọn)
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "phat_duoc_su_2.jpg")
            logo_img = Image.open(logo_path)
            ti_le = 300 / logo_img.size[0]
            logo_img = logo_img.resize((300, int(logo_img.size[1] * ti_le)), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(logo_img)
            tk.Label(self.root, image=self.logo).pack(pady=6)
        except Exception as e:
            print("Lỗi logo:", e)

        # Nhãn trạng thái: Đang phát
        self.dang_phat_var = tk.StringVar(value="Đang phát: —")
        tk.Label(self.root, textvariable=self.dang_phat_var, fg="#0a7", anchor="w").pack(fill=tk.X, padx=8)

        # Dữ liệu
        self.ds_nhac = []   # list dict: {path, title, dur, size, mtime}
        self.chi_so_hien_tai = 0
        self.tong_thoi_luong = 1
        self.che_do_lap = False
        self.che_do_tron = False
        self.am_luong = tk.IntVar(value=80)
        self.che_do_sap_xep = tk.StringVar(value="Mới nhất trước")

        # VLC
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # Bảng danh sách (Treeview)
        cot = ("#", "title", "length", "size", "mtime")
        self.tree = ttk.Treeview(self.root, columns=cot, show="headings", selectmode="browse")
        self.tree.heading("#", text="STT")
        self.tree.heading("title", text="Tên bài hát")
        self.tree.heading("length", text="Thời gian")
        self.tree.heading("size", text="Dung lượng")
        self.tree.heading("mtime", text="Ngày giờ")
        self.tree.column("#", width=50, anchor="center", stretch=False)
        self.tree.column("title", width=420, anchor="w")
        self.tree.column("length", width=90, anchor="center", stretch=False)
        self.tree.column("size", width=100, anchor="e", stretch=False)
        self.tree.column("mtime", width=140, anchor="center", stretch=False)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        self.tree.bind("<Double-1>", self.khi_double_click)
        self.tree.tag_configure("dangphat", background="#e8f6ff")

        # Thanh tiến độ + nhãn thời gian
        self.tien_do = tk.DoubleVar()
        self.thanh_tien_do = ttk.Scale(self.root, from_=0, to=100, orient=tk.HORIZONTAL,
                                       variable=self.tien_do, command=self tua)
        self.thanh_tien_do.pack(fill=tk.X, padx=8)
        self.nhan_thoi_gian = tk.Label(self.root, text="00:00 / 00:00")
        self.nhan_thoi_gian.pack()

        # Âm lượng
        khung_am = tk.Frame(self.root)
        khung_am.pack()
        tk.Label(khung_am, text="Âm lượng").pack(side=tk.LEFT)
        tk.Scale(khung_am, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.am_luong,
                 command=self.dat_am_luong, length=200).pack(side=tk.LEFT, padx=6)

        # Sắp xếp
        khung_sx = tk.Frame(self.root)
        khung_sx.pack(pady=(4, 2))
        tk.Label(khung_sx, text="Sắp xếp").pack(side=tk.LEFT)
        self.hop_sx = ttk.Combobox(
            khung_sx, textvariable=self.che_do_sap_xep,
            values=["Mới nhất trước", "Tên Z-A", "Tên A-Z", "Cũ nhất trước", "Dung lượng: lớn → nhỏ", "Dung lượng: nhỏ → lớn"],
            width=22, state="readonly"
        )
        self.hop_sx.pack(side=tk.LEFT, padx=6)
        self.hop_sx.bind("<<ComboboxSelected>>", lambda e: self.sap_xep_lai())

        # Nút điều khiển
        self.tao_cac_nut()

        # Luồng cập nhật + trạng thái
        self.cap_nhat_nen()
        self.tai_trang_thai_cu()
        self.luu_trang_thai_dinhky()

    # ----- Nút -----
    def tao_cac_nut(self):
        f = tk.Frame(self.root)
        f.pack(pady=4)
        tk.Button(f, text="📁 Mở thư mục", command=self.mo_thu_muc).pack(side=tk.LEFT, padx=2)
        tk.Button(f, text="⏮️ Trước", command=self.bai_truoc).pack(side=tk.LEFT, padx=2)
        tk.Button(f, text="▶️ Phát/Tạm dừng", command=self.phat_tam_dung).pack(side=tk.LEFT, padx=2)
        tk.Button(f, text="⏭️ Kế tiếp", command=self.bai_sau).pack(side=tk.LEFT, padx=2)
        tk.Button(f, text="⏹ Dừng", command=self.dung).pack(side=tk.LEFT, padx=2)
        tk.Button(f, text="🔁 Lặp lại", command=self.chuyen_lap).pack(side=tk.LEFT, padx=2)
        tk.Button(f, text="🔀 Trộn", command=self.chuyen_tron).pack(side=tk.LEFT, padx=2)

    # ----- Tải dữ liệu -----
    def mo_thu_muc(self):
        thu_muc = filedialog.askdirectory()
        if thu_muc:
            self.tai_ds_nhac(thu_muc)
            if self.ds_nhac:
                self.phat_bai(0)

    def tai_ds_nhac(self, thu_muc):
        """Đọc danh sách file nhạc và đổ vào bảng"""
        try:
            files = [f for f in os.listdir(thu_muc) if f.lower().endswith(('.mp3', '.wav'))]
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở thư mục:\n{e}")
            return

        duong_dan = [os.path.join(thu_muc, f) for f in files]
        md = self.che_do_sap_xep.get()
        if md == "Tên A-Z":
            duong_dan.sort()
        elif md == "Tên Z-A":
            duong_dan.sort(reverse=True)
        elif md == "Mới nhất trước":
            duong_dan.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        elif md == "Cũ nhất trước":
            duong_dan.sort(key=lambda x: os.path.getmtime(x))
        elif md == "Dung lượng: lớn → nhỏ":
            duong_dan.sort(key=lambda x: os.path.getsize(x), reverse=True)
        elif md == "Dung lượng: nhỏ → lớn":
            duong_dan.sort(key=lambda x: os.path.getsize(x))

        self.ds_nhac = []
        for p in duong_dan:
            try:
                size = os.path.getsize(p)
                mtime = os.path.getmtime(p)
            except Exception:
                size, mtime = 0, 0.0
            self.ds_nhac.append({
                "path": p,
                "title": os.path.basename(p),
                "dur": None,            # sẽ điền sau
                "size": size,
                "mtime": mtime
            })
        self.thu_muc_nhac = thu_muc

        self.do_lai_bang()

        # Điền thời lượng nền (không chặn UI)
        threading.Thread(target=self._dien_thoi_luong_nen, daemon=True).start()

    def _dien_thoi_luong_nen(self):
        for idx, item in enumerate(self.ds_nhac):
            if item["dur"] is not None:
                continue
            try:
                media = self.instance.media_new(item["path"])
                media.parse_with_options(vlc.MediaParseFlag.local, timeout=1500)
                dur_ms = media.get_duration()
                dur = (dur_ms or 0) / 1000.0
                item["dur"] = dur if dur > 0 else None
            except Exception:
                item["dur"] = None
            self.root.after(0, lambda i=idx: self._cap_nhat_thoi_luong_hang(i))

    def _cap_nhat_thoi_luong_hang(self, index):
        iid = str(index)
        if not self.tree.exists(iid):
            return
        item = self.ds_nhac[index]
        self.tree.set(iid, "length", dinh_dang_thoi_gian(item["dur"]))

    def do_lai_bang(self):
        self.tree.delete(*self.tree.get_children())
        for i, it in enumerate(self.ds_nhac, start=1):
            iid = str(i - 1)  # lưu chỉ số gốc
            self.tree.insert(
                "", "end", iid=iid, values=(
                    i,
                    it["title"],
                    dinh_dang_thoi_gian(it["dur"]),
                    dinh_dang_dung_luong(it["size"]),
                    datetime.fromtimestamp(it["mtime"]).strftime("%Y-%m-%d %H:%M")
                )
            )

    def sap_xep_lai(self):
        if not getattr(self, "thu_muc_nhac", None):
            return
        self.tai_ds_nhac(self.thu_muc_nhac)

    # ----- Điều khiển phát -----
    def phat_bai(self, chi_so, vi_tri=0):
        if not self.ds_nhac:
            return
        self.chi_so_hien_tai = chi_so % len(self.ds_nhac)
        media = self.instance.media_new(self.ds_nhac[self.chi_so_hien_tai]["path"])
        self.player.set_media(media)
        self.player.play()
        time.sleep(0.2)

        # Lấy thời lượng từ player (phòng khi chưa parse xong)
        self.tong_thoi_luong = max(1, self.player.get_length() / 1000.0)
        self.thanh_tien_do.configure(to=self.tong_thoi_luong)
        self.player.set_time(int(max(0, float(vi_tri)) * 1000))
        self.player.audio_set_volume(self.am_luong.get())

        # Tô sáng hàng đang phát
        for iid in self.tree.get_children():
            self.tree.item(iid, tags=())
        cur_iid = str(self.chi_so_hien_tai)
        if self.tree.exists(cur_iid):
            self.tree.see(cur_iid)
            self.tree.selection_set(cur_iid)
            self.tree.item(cur_iid, tags=("dangphat",))

        # Cập nhật nhãn trạng thái
        tieu_de = self.ds_nhac[self.chi_so_hien_tai]["title"]
        self.dang_phat_var.set(f"Đang phát: {tieu_de}")

        luu_trang_thai(self.thu_muc_nhac, self.chi_so_hien_tai, self.am_luong.get(),
                       self.ds_nhac[self.chi_so_hien_tai]["path"], vi_tri)

    def phat_tam_dung(self):
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()

    def dung(self):
        self.player.stop()

    def bai_sau(self):
        if not self.ds_nhac:
            return
        if self.che_do_tron:
            self.phat_bai(random.randint(0, len(self.ds_nhac) - 1))
        else:
            self.phat_bai(self.chi_so_hien_tai + 1)

    def bai_truoc(self):
        if self.ds_nhac:
            self.phat_bai(self.chi_so_hien_tai - 1)

    def khi_double_click(self, _e):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        try:
            idx = int(iid)
        except Exception:
            idx = 0
        self.phat_bai(idx)

    def tua(self, val):
        try:
            self.player.set_time(int(float(val) * 1000))
        except Exception:
            pass

    def dat_am_luong(self, val):
        try:
            self.player.audio_set_volume(int(float(val)))
        except Exception:
            pass

    def chuyen_lap(self):
        self.che_do_lap = not self.che_do_lap
        messagebox.showinfo("Lặp lại", f"Đã {'BẬT' if self.che_do_lap else 'TẮT'} chế độ lặp.")

    def chuyen_tron(self):
        self.che_do_tron = not self.che_do_tron
        messagebox.showinfo("Trộn", f"Đã {'BẬT' if self.che_do_tron else 'TẮT'} chế độ trộn.")

    # ----- Luồng cập nhật -----
    def cap_nhat_nen(self):
        def vong_lap():
            while True:
                try:
                    if self.player.is_playing():
                        pos = self.player.get_time() / 1000.0
                        self.tien_do.set(pos)
                        self.nhan_thoi_gian.config(
                            text=f"{dinh_dang_thoi_gian(pos)} / {dinh_dang_thoi_gian(self.tong_thoi_luong)}"
                        )
                        # tự chuyển bài khi hết
                        if self.tong_thoi_luong > 1 and (self.tong_thoi_luong - pos) <= 0.8:
                            time.sleep(0.8)
                            if self.che_do_lap:
                                self.phat_bai(self.chi_so_hien_tai)
                            else:
                                self.bai_sau()
                    time.sleep(0.4)
                except Exception:
                    time.sleep(0.8)
        threading.Thread(target=vong_lap, daemon=True).start()

    # ----- Trạng thái -----
    def tai_trang_thai_cu(self):
        st = tai_trang_thai()
        thu_muc = st.get("folder", "")
        if thu_muc and os.path.isdir(thu_muc):
            try:
                self.tai_ds_nhac(thu_muc)
                self.am_luong.set(st.get("volume", 80))
                self.phat_bai(st.get("index", 0), st.get("position", 0))
            except Exception as e:
                print(f"⚠️ Lỗi tải trạng thái cũ: {e}")
        else:
            print("⚠️ Không tìm thấy thư mục lưu trước đó. Vui lòng chọn thư mục mới.")

    def luu_trang_thai_dinhky(self):
        try:
            if self.ds_nhac:
                pos = max(0, self.player.get_time() / 1000.0)
                luu_trang_thai(self.thu_muc_nhac, self.chi_so_hien_tai, self.am_luong.get(),
                               self.ds_nhac[self.chi_so_hien_tai]["path"], pos)
        except Exception:
            pass
        self.root.after(30000, self.luu_trang_thai_dinhky)

    # ----- Chạy ứng dụng -----
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PrajnaPlayerUI()
    app.run()

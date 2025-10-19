# theme_pharmapp_tk.py
import tkinter as tk
from tkinter import ttk

def apply_pharmapp_theme(root: tk.Tk | tk.Toplevel):
    """Apply PharmApp-style theme to Tkinter window and ttk widgets."""

    root.configure(bg="#fdf5e6")  # 🌕 Kem nhạt

    style = ttk.Style()
    style.theme_use("default")

    # 🪟 Frame và Label chung
    style.configure("TFrame", background="#fdf5e6")
    style.configure("TLabel", background="#fdf5e6", foreground="#2a2a2a", font=("Arial", 11))
    
    # 🔘 Nút
    style.configure("TButton", background="#f4a261", foreground="black", font=("Arial", 10, "bold"), borderwidth=0)
    style.map("TButton", background=[("active", "#e76f51")])

    # 📋 Treeview
    style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#b5838d", foreground="white")
    style.configure("Treeview", font=("Arial", 10), rowheight=25)
    style.map("Treeview", background=[("selected", "#e9c46a")])  # vàng khi chọn

    # 🟨 Entry & Combobox (nếu dùng)
    style.configure("TEntry", padding=5)
    style.configure("TCombobox", padding=5)

# how to use:
# from theme_pharmapp_tk import apply_pharmapp_theme
# apply_pharmapp_theme(root)
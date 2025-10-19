
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PharmApp SVG→Icon Studio (Tkinter)

Features
- PharmApp theme (bg #fdf5e6, text #2a2a2a, buttons #f4a261)
- Pick SVG files and/or a folder (recursive optional)
- Multi-color recolor pack (16 preset colors + custom HEX)
- Export options: recolored SVG, PNG (multi-size), ICO (multi-size)
- PNG/ICO sizes editable (defaults good for Win/macOS/HiDPI)
- Fill/Stroke recolor modes; preserve transparency or set solid background
- Live preview (requires cairosvg)
- Progress bar + log

Requirements
    pip install pillow cairosvg tinycss2 cssselect2 cairocffi

Usage
    python PharmApp_SVG_Icon_Studio.py

© 2025 Nghiên Cứu Thuốc // PharmApp. For educational use.
"""

import os, re, sys, threading, queue
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional

try:
    import cairosvg
except Exception:
    cairosvg = None

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --------------------------- THEME -----------------------------------------

def apply_pharmapp_theme(root: tk.Tk) -> None:
    root.title("PharmApp SVG→Icon Studio")
    bg = "#fdf5e6"  # canvas
    fg = "#2a2a2a"  # text
    btn_bg = "#f4a261"
    btn_fg = "#000000"
    btn_active = "#e76f51"

    root.configure(bg=bg)
    style = ttk.Style()
    try:
        style.theme_use("default")
    except Exception:
        pass

    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg, font=("Arial", 11))
    style.configure("TButton", padding=6)

    # Custom button using tk.Button (for bg color)
    def style_button(widget: tk.Button):
        widget.configure(bg=btn_bg, fg=btn_fg, activebackground=btn_active,
                         activeforeground=btn_fg, bd=0, font=("Arial", 10, "bold"))

    root.style_button = style_button  # attach helper

# ----------------------- DATA / DEFAULTS ----------------------------------

DEFAULT_PALETTE: Dict[str, str] = {
    "orange":"#f4a261","coral":"#e76f51","gold":"#e9c46a","blush":"#b5838d",
    "teal":"#2a9d8f","indigo":"#3a86ff","violet":"#6d28d9","pink":"#ec4899",
    "red":"#ef4444","green":"#22c55e","emerald":"#10b981","cyan":"#14b8a6",
    "sky":"#0ea5e9","bluegray":"#64748b","slate":"#334155","black":"#111827"
}

DEFAULT_SIZES = [16,20,24,32,40,48,64,96,128,256]

# ------------------------ SVG UTILS ---------------------------------------

SVG_FILL_RE = re.compile(r'fill="(?!none)(?!url\()([^\"]*)"', re.IGNORECASE)
SVG_STROKE_RE = re.compile(r'stroke="(?!none)(?!url\()([^\"]*)"', re.IGNORECASE)
SVG_ROOT_OPEN = re.compile(r"<svg([^>]*)>", re.IGNORECASE)


def sanitize_hex(color: str) -> str:
    c = color.strip()
    if not c:
        return "#000000"
    if not c.startswith('#'):
        c = '#' + c
    if len(c) == 4:  # #abc -> #aabbcc
        c = '#' + ''.join([ch*2 for ch in c[1:]])
    return c


def recolor_svg_text(svg_text: str, color_hex: str, mode: str = "fill+stroke") -> str:
    """Return a recolored svg string. mode in {fill+stroke, fill, stroke, none}."""
    color_hex = sanitize_hex(color_hex)
    s = svg_text

    if mode in ("fill+stroke", "fill"):
        s = SVG_FILL_RE.sub(f'fill="{color_hex}"', s)
        # ensure root has default fill if none
        if ' fill=' not in s.split('>')[0].lower():
            s = SVG_ROOT_OPEN.sub(rf'<svg\1 fill="{color_hex}">', s, count=1)

    if mode in ("fill+stroke", "stroke"):
        s = SVG_STROKE_RE.sub(f'stroke="{color_hex}"', s)

    return s


def export_png(svg_text: str, out_path: str, size: int, background: Optional[str] = None) -> None:
    if cairosvg is None:
        raise RuntimeError("cairosvg not installed")
    background = sanitize_hex(background) if background else None
    kwargs = {"bytestring": svg_text.encode("utf-8"),
              "write_to": out_path,
              "output_width": size,
              "output_height": size}
    # newer cairosvg supports background_color
    if background:
        try:
            kwargs["background_color"] = background
        except Exception:
            pass
    cairosvg.svg2png(**kwargs)


def export_ico_from_pngs(png_paths: List[str], out_ico: str) -> None:
    if Image is None:
        raise RuntimeError("Pillow not installed")
    if not png_paths:
        raise ValueError("No PNGs provided for ICO")
    # use largest as source, Pillow will generate sizes
    largest = sorted(png_paths, key=lambda p: int(os.path.splitext(os.path.basename(p))[0].split('_')[-1]))[-1]
    im = Image.open(largest).convert("RGBA")
    sizes = sorted({int(os.path.splitext(os.path.basename(p))[0].split('_')[-1]) for p in png_paths})
    im.save(out_ico, sizes=[(s, s) for s in sizes])

# ----------------------- APP STATE ----------------------------------------

@dataclass
class AppOptions:
    out_dir: str = "out"
    sizes: List[int] = field(default_factory=lambda: DEFAULT_SIZES.copy())
    export_svg: bool = True
    export_png: bool = True
    export_ico: bool = True
    recolor_mode: str = "fill+stroke"  # fill+stroke | fill | stroke | none
    bg_transparent: bool = True
    bg_color: str = "#000000"


# -------------------------- GUI ------------------------------------------

class IconStudioApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        apply_pharmapp_theme(root)

        self.files: List[str] = []
        self.palette: Dict[str, str] = DEFAULT_PALETTE.copy()
        self.selected_colors: Dict[str, tk.BooleanVar] = {k: tk.BooleanVar(value=True) for k in self.palette}
        self.opts = AppOptions()
        self.q = queue.Queue()
        self.worker: Optional[threading.Thread] = None

        self._build_ui()
        self._tick()

    # ---------------------- UI LAYOUT -----------------------------------
    def _build_ui(self):
        top = ttk.Frame(self.root); top.pack(fill='x', padx=10, pady=8)
        ttk.Label(top, text="PharmApp SVG→Icon Studio", font=("Arial", 16, "bold")).pack(side='left')
        self.cairo_label = ttk.Label(top, text=("cairosvg: OK" if cairosvg else "cairosvg: NOT INSTALLED"))
        self.cairo_label.pack(side='right')

        main = ttk.Frame(self.root); main.pack(fill='both', expand=True, padx=10, pady=5)
        left = ttk.Frame(main); left.pack(side='left', fill='both', expand=True, padx=(0,8))
        mid = ttk.Frame(main); mid.pack(side='left', fill='y', padx=(0,8))
        right = ttk.Frame(main); right.pack(side='left', fill='both', expand=True)

        # LEFT: file picker
        lf = ttk.LabelFrame(left, text="Source SVGs")
        lf.pack(fill='both', expand=True)
        btns = ttk.Frame(lf); btns.pack(fill='x', pady=4)
        b1 = tk.Button(btns, text="+ Add SVG files", command=self.add_files)
        self.root.style_button(b1); b1.pack(side='left', padx=3)
        b2 = tk.Button(btns, text="+ Add folder", command=self.add_folder)
        self.root.style_button(b2); b2.pack(side='left', padx=3)
        self.recursive = tk.BooleanVar(value=True)
        ttk.Checkbutton(btns, text="Recursive", variable=self.recursive).pack(side='left', padx=6)
        b3 = tk.Button(btns, text="Remove", command=self.remove_selected)
        self.root.style_button(b3); b3.pack(side='left', padx=3)
        b4 = tk.Button(btns, text="Clear", command=self.clear_files)
        self.root.style_button(b4); b4.pack(side='left', padx=3)

        self.listbox = tk.Listbox(lf, height=10, selectmode=tk.EXTENDED)
        self.listbox.pack(fill='both', expand=True, padx=4, pady=4)

        # MID: options
        of = ttk.LabelFrame(mid, text="Options")
        of.pack(fill='y')

        # Output dir
        od = ttk.Frame(of); od.pack(fill='x', pady=4)
        ttk.Label(od, text="Output folder").pack(anchor='w')
        self.out_var = tk.StringVar(value=self.opts.out_dir)
        row = ttk.Frame(od); row.pack(fill='x')
        e = ttk.Entry(row, textvariable=self.out_var, width=22); e.pack(side='left', fill='x', expand=True)
        b = tk.Button(row, text="Browse", command=self.choose_out_dir); self.root.style_button(b); b.pack(side='left', padx=4)

        # Sizes
        sz = ttk.Frame(of); sz.pack(fill='x', pady=6)
        ttk.Label(sz, text="PNG/ICO sizes (comma)").pack(anchor='w')
        self.size_var = tk.StringVar(value=','.join(map(str, self.opts.sizes)))
        ttk.Entry(sz, textvariable=self.size_var, width=22).pack(fill='x')

        # Export toggles
        tg = ttk.Frame(of); tg.pack(fill='x', pady=6)
        self.var_svg = tk.BooleanVar(value=self.opts.export_svg)
        self.var_png = tk.BooleanVar(value=self.opts.export_png)
        self.var_ico = tk.BooleanVar(value=self.opts.export_ico)
        ttk.Checkbutton(tg, text="Export recolored SVG", variable=self.var_svg).pack(anchor='w')
        ttk.Checkbutton(tg, text="Export PNG", variable=self.var_png).pack(anchor='w')
        ttk.Checkbutton(tg, text="Export ICO", variable=self.var_ico).pack(anchor='w')

        # Recolor mode
        rm = ttk.Frame(of); rm.pack(fill='x', pady=6)
        ttk.Label(rm, text="Recolor mode").pack(anchor='w')
        self.recolor_mode = tk.StringVar(value=self.opts.recolor_mode)
        for label, val in [("Fill+Stroke","fill+stroke"),("Fill only","fill"),("Stroke only","stroke"),("Leave original","none")]:
            ttk.Radiobutton(rm, text=label, value=val, variable=self.recolor_mode).pack(anchor='w')

        # Background
        bgf = ttk.Frame(of); bgf.pack(fill='x', pady=6)
        ttk.Label(bgf, text="PNG background").pack(anchor='w')
        self.bg_transparent = tk.BooleanVar(value=True)
        ttk.Radiobutton(bgf, text="Transparent", variable=self.bg_transparent, value=True).pack(anchor='w')
        rowbg = ttk.Frame(bgf); rowbg.pack(fill='x')
        ttk.Radiobutton(rowbg, text="Solid #", variable=self.bg_transparent, value=False).pack(side='left')
        self.bg_color = tk.StringVar(value="#ffffff")
        ttk.Entry(rowbg, textvariable=self.bg_color, width=10).pack(side='left', padx=6)

        # RIGHT: palette + preview + run
        rf = ttk.LabelFrame(right, text="Colors & Preview")
        rf.pack(fill='both', expand=True)

        pal = ttk.Frame(rf); pal.pack(fill='x', pady=4)
        ttk.Label(pal, text="Palette (tick colors to export)").pack(anchor='w')
        self.colors_frame = ttk.Frame(rf); self.colors_frame.pack(fill='x')
        self._render_palette()

        # Custom color add
        cc = ttk.Frame(rf); cc.pack(fill='x', pady=6)
        ttk.Label(cc, text="Add custom HEX (#rrggbb)").pack(anchor='w')
        self.custom_name = tk.StringVar(value="custom")
        self.custom_hex = tk.StringVar(value="#222222")
        rowc = ttk.Frame(cc); rowc.pack(fill='x')
        ttk.Entry(rowc, textvariable=self.custom_name, width=10).pack(side='left')
        ttk.Entry(rowc, textvariable=self.custom_hex, width=12).pack(side='left', padx=4)
        bc = tk.Button(rowc, text="Add", command=self.add_custom_color); self.root.style_button(bc); bc.pack(side='left')

        # Preview controls
        pv = ttk.Frame(rf); pv.pack(fill='x', pady=4)
        ttk.Label(pv, text="Preview (requires cairosvg)").pack(anchor='w')
        pvrow = ttk.Frame(pv); pvrow.pack(fill='x')
        self.preview_color = tk.StringVar(value=list(self.palette.values())[0])
        self.preview_size = tk.IntVar(value=128)
        self.preview_color_combo = ttk.Combobox(pvrow, values=[f"{k} {v}" for k,v in self.palette.items()], width=20)
        self.preview_color_combo.set(next(iter(self.palette)) + ' ' + self.palette[next(iter(self.palette))])
        self.preview_color_combo.pack(side='left')
        ttk.Entry(pvrow, textvariable=self.preview_size, width=6).pack(side='left', padx=4)
        bpv = tk.Button(pvrow, text="Render", command=self.render_preview)
        self.root.style_button(bpv); bpv.pack(side='left', padx=4)

        self.preview_label = ttk.Label(rf)
        self.preview_label.pack(fill='both', expand=True, pady=6)

        # Bottom: run + progress + log
        bottom = ttk.Frame(self.root); bottom.pack(fill='x', padx=10, pady=8)
        run_btn = tk.Button(bottom, text="▶ Convert", command=self.start_convert)
        self.root.style_button(run_btn); run_btn.pack(side='left')
        self.progress = ttk.Progressbar(bottom, length=280, mode='determinate')
        self.progress.pack(side='left', padx=10)
        self.status = ttk.Label(bottom, text="Idle")
        self.status.pack(side='left')

        logf = ttk.LabelFrame(self.root, text="Log")
        logf.pack(fill='both', expand=True, padx=10, pady=(0,10))
        self.log = tk.Text(logf, height=8, wrap='word', bg="#fffaf0")
        self.log.pack(fill='both', expand=True)
        self.log.configure(state='disabled')

    def _render_palette(self):
        # clear
        for w in self.colors_frame.winfo_children():
            w.destroy()
        # grid 4 columns
        col = 0; row = 0
        for name, hexv in self.palette.items():
            var = self.selected_colors.setdefault(name, tk.BooleanVar(value=True))
            f = ttk.Frame(self.colors_frame)
            f.grid(row=row, column=col, sticky='w', padx=4, pady=2)
            cb = ttk.Checkbutton(f, variable=var)
            cb.grid(row=0, column=0, padx=2)
            sw = tk.Canvas(f, width=18, height=18, highlightthickness=1, highlightbackground="#ccc")
            sw.create_rectangle(0,0,18,18, fill=hexv, outline="")
            sw.grid(row=0, column=1)
            ttk.Label(f, text=f"{name} {hexv}").grid(row=0, column=2, padx=4)
            col += 1
            if col >= 4:
                col = 0; row += 1

    # -------------------------- FILE OPS ---------------------------------
    def add_files(self):
        paths = filedialog.askopenfilenames(title="Choose SVG files", filetypes=[["SVG","*.svg"],["All","*.*"]])
        if not paths:
            return
        added = 0
        for p in paths:
            if p.lower().endswith('.svg') and p not in self.files:
                self.files.append(p)
                added += 1
        if added:
            self._refresh_listbox()

    def add_folder(self):
        d = filedialog.askdirectory(title="Choose a folder")
        if not d:
            return
        rec = self.recursive.get()
        for rootd, dirs, files in os.walk(d):
            for fn in files:
                if fn.lower().endswith('.svg'):
                    p = os.path.join(rootd, fn)
                    if p not in self.files:
                        self.files.append(p)
            if not rec:
                break
        self._refresh_listbox()

    def remove_selected(self):
        sel = list(self.listbox.curselection())[::-1]
        if not sel:
            return
        for idx in sel:
            try:
                self.files.pop(idx)
            except Exception:
                pass
        self._refresh_listbox()

    def clear_files(self):
        self.files.clear(); self._refresh_listbox()

    def _refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for p in self.files:
            self.listbox.insert(tk.END, p)

    def choose_out_dir(self):
        d = filedialog.askdirectory(title="Select output folder")
        if d:
            self.out_var.set(d)

    # -------------------------- PREVIEW ----------------------------------
    def _parse_size_entry(self) -> List[int]:
        try:
            sizes = [int(s.strip()) for s in self.size_var.get().split(',') if s.strip()]
            sizes = sorted(list({s for s in sizes if 8 <= s <= 1024}))
            if not sizes:
                sizes = DEFAULT_SIZES.copy()
        except Exception:
            sizes = DEFAULT_SIZES.copy()
        return sizes

    def add_custom_color(self):
        name = self.custom_name.get().strip() or "custom"
        hexv = sanitize_hex(self.custom_hex.get().strip() or "#222222")
        if name in self.palette:
            messagebox.showwarning("Palette", f"Color name '{name}' already exists. Renaming to '{name}_2'")
            name = name + "_2"
        self.palette[name] = hexv
        self.selected_colors[name] = tk.BooleanVar(value=True)
        self._render_palette()
        # also update preview combobox
        self.preview_color_combo.configure(values=[f"{k} {v}" for k,v in self.palette.items()])

    def render_preview(self):
        if cairosvg is None or Image is None or ImageTk is None:
            messagebox.showinfo("Preview", "Preview requires 'cairosvg' and 'Pillow'. Install them first.")
            return
        if not self.files:
            messagebox.showwarning("Preview", "Please add at least one SVG file.")
            return
        # take first selected or first item
        try:
            idxs = self.listbox.curselection()
            src = self.files[idxs[0]] if idxs else self.files[0]
        except Exception:
            src = self.files[0]
        try:
            svg_text = open(src, 'r', encoding='utf-8').read()
        except Exception as e:
            messagebox.showerror("Read error", str(e)); return

        sel = self.preview_color_combo.get().split()
        color_hex = sel[-1] if sel else list(self.palette.values())[0]
        mode = self.recolor_mode.get()
        svg_col = recolor_svg_text(svg_text, color_hex, mode)

        size = max(16, int(self.preview_size.get()))
        try:
            tmp_png = os.path.join(os.getcwd(), "__preview__.png")
            bg = None if self.bg_transparent.get() else sanitize_hex(self.bg_color.get())
            export_png(svg_col, tmp_png, size=size, background=bg)
            im = Image.open(tmp_png).convert('RGBA')
            ph = ImageTk.PhotoImage(im)
            self.preview_label.configure(image=ph)
            self.preview_label.image = ph
            try:
                os.remove(tmp_png)
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Preview error", str(e))

    # ------------------------ CONVERT RUNNER ------------------------------
    def start_convert(self):
        if not self.files:
            messagebox.showwarning("Convert", "No SVG files.")
            return
        out_dir = self.out_var.get().strip() or "out"
        os.makedirs(out_dir, exist_ok=True)

        sizes = self._parse_size_entry()
        export_svg = self.var_svg.get()
        export_png_flag = self.var_png.get()
        export_ico_flag = self.var_ico.get()
        mode = self.recolor_mode.get()
        bg = None if self.bg_transparent.get() else sanitize_hex(self.bg_color.get())

        # gather selected colors
        colors = [(name, self.palette[name]) for name, v in self.selected_colors.items() if v.get()]
        if not colors:
            messagebox.showwarning("Palette", "Please select at least one color.")
            return

        # build tasks
        tasks: List[Tuple[str, str, str]] = []  # (src_file, color_name, hex)
        for f in self.files:
            for name, hexv in colors:
                tasks.append((f, name, hexv))

        self.status.configure(text=f"Converting {len(tasks)} variants…")
        self.progress.configure(maximum=len(tasks))
        self.progress['value'] = 0
        self._log_clear()

        def worker():
            done = 0
            for src, cname, chex in tasks:
                try:
                    with open(src, 'r', encoding='utf-8') as fh:
                        svg_text = fh.read()
                    svg_col = recolor_svg_text(svg_text, chex, mode)

                    base = os.path.splitext(os.path.basename(src))[0]
                    safe = re.sub(r'[^A-Za-z0-9_-]+', '_', base)
                    subdir = os.path.join(out_dir, safe)
                    os.makedirs(subdir, exist_ok=True)

                    png_paths: List[str] = []

                    if export_svg:
                        svg_out = os.path.join(subdir, f"{safe}_{cname}.svg")
                        with open(svg_out, 'w', encoding='utf-8') as fo:
                            fo.write(svg_col)
                        self.q.put(("log", f"SVG → {os.path.relpath(svg_out)}"))

                    if export_png_flag:
                        if cairosvg is None:
                            self.q.put(("log", "[WARN] cairosvg missing: skip PNG"))
                        else:
                            for s in sizes:
                                png_out = os.path.join(subdir, f"{safe}_{cname}_{s}.png")
                                export_png(svg_col, png_out, size=s, background=bg)
                                png_paths.append(png_out)
                            self.q.put(("log", f"PNG x{len(png_paths)} → {os.path.relpath(subdir)}"))

                    if export_ico_flag:
                        if not png_paths:
                            # need at least one PNG to make ICO
                            if cairosvg is not None and sizes:
                                smax = max(sizes)
                                tmp_png = os.path.join(subdir, f"{safe}_{cname}_{smax}.png")
                                export_png(svg_col, tmp_png, size=smax, background=bg)
                                png_paths.append(tmp_png)
                        try:
                            if Image is None:
                                self.q.put(("log", "[WARN] Pillow missing: skip ICO"))
                            else:
                                ico_out = os.path.join(subdir, f"{safe}_{cname}.ico")
                                export_ico_from_pngs(png_paths, ico_out)
                                self.q.put(("log", f"ICO → {os.path.relpath(ico_out)}"))
                        except Exception as e:
                            self.q.put(("log", f"[ICO ERR] {e}"))

                except Exception as e:
                    self.q.put(("log", f"[ERR] {os.path.basename(src)} :: {e}"))
                finally:
                    done += 1
                    self.q.put(("progress", done))
            self.q.put(("done", done))

        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Convert", "A job is already running.")
            return
        self.worker = threading.Thread(target=worker, daemon=True)
        self.worker.start()

    def _tick(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "progress":
                    self.progress['value'] = payload
                elif kind == "log":
                    self._log(payload)
                elif kind == "done":
                    self.status.configure(text=f"Done ({payload} variants)")
        except queue.Empty:
            pass
        self.root.after(100, self._tick)

    def _log(self, msg: str):
        self.log.configure(state='normal')
        self.log.insert('end', msg + "\n")
        self.log.see('end')
        self.log.configure(state='disabled')

    def _log_clear(self):
        self.log.configure(state='normal')
        self.log.delete('1.0', 'end')
        self.log.configure(state='disabled')


# ---------------------------- MAIN ----------------------------------------

def main():
    root = tk.Tk()
    app = IconStudioApp(root)
    # nice minimum size
    root.minsize(980, 640)
    root.mainloop()


if __name__ == "__main__":
    main()

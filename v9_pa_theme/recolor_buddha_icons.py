import re, sys, os
# Optional: pip install cairosvg  (để xuất PNG các size)
try:
    import cairosvg
except Exception:
    cairosvg = None

PALETTE = {
    "orange":"#f4a261","coral":"#e76f51","gold":"#e9c46a","blush":"#b5838d",
    "teal":"#2a9d8f","indigo":"#3a86ff","violet":"#6d28d9","pink":"#ec4899",
    "red":"#ef4444","green":"#22c55e","emerald":"#10b981","cyan":"#14b8a6",
    "sky":"#0ea5e9","bluegray":"#64748b","slate":"#334155","black":"#111827"
}

def recolor(svg_text, hex_color):
    # thay mọi fill/stroke (trừ 'none') sang màu mới
    svg = re.sub(r'fill="(?!none)[^"]*"', f'fill="{hex_color}"', svg_text, flags=re.I)
    svg = re.sub(r'stroke="(?!none)[^"]*"', f'stroke="{hex_color}"', svg, flags=re.I)
    # nếu root <svg ...> chưa có fill mặc định, thêm để kế thừa
    if re.search(r'<svg[^>]*\sfill=', svg, flags=re.I) is None:
        svg = re.sub(r'<svg([^>]*)>', rf'<svg\1 fill="{hex_color}">', svg, count=1, flags=re.I)
    return svg

def main():
    if len(sys.argv) < 3:
        print("Usage: python recolor_buddha_icons.py <input.svg> <out_dir>")
        sys.exit(1)
    src, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    svg_text = open(src, "r", encoding="utf-8").read()

    for name, color in PALETTE.items():
        svg_out = recolor(svg_text, color)
        svg_path = os.path.join(out_dir, f"buddha_{name}.svg")
        open(svg_path, "w", encoding="utf-8").write(svg_out)
        if cairosvg:
            # xuất PNG đa kích thước (tuỳ chọn)
            for size in (16,32,64,128,256,512):
                png_path = os.path.join(out_dir, f"buddha_{name}_{size}.png")
                cairosvg.svg2png(bytestring=svg_out.encode("utf-8"),
                                 write_to=png_path, output_width=size, output_height=size)
    print("Done. SVG created; PNGs created if cairosvg is installed.")

if __name__ == "__main__":
    main()


# python recolor_buddha_icons.py buddha.svg out/
# https://chatgpt.com/c/68ef2bdf-6ee4-8323-860a-b1d79bef8cab
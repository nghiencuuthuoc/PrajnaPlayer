import sys, os, glob
from PIL import Image

def make_ico(png_512, ico_path):
    im = Image.open(png_512).convert("RGBA")
    sizes = [(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)]
    im.save(ico_path, sizes=sizes)

def main():
    if len(sys.argv) < 3:
        print("Usage: python make_ico_pack.py <png_folder> <out_ico_folder>")
        sys.exit(1)
    src, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    # tìm tất cả PNG 512px theo mẫu đã tạo: buddha_<color>_512.png
    for p in glob.glob(os.path.join(src, "buddha_*_512.png")):
        name = os.path.basename(p).replace("_512.png", "")
        ico_path = os.path.join(out_dir, f"{name}.ico")
        make_ico(p, ico_path)
    print("ICO pack created at:", out_dir)

if __name__ == "__main__":
    main()


# python make_ico_pack.py out out\ico
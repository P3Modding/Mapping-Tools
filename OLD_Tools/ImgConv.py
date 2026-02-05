from PIL import Image
from tkinter import Tk, filedialog, messagebox
import os
import struct

# Fixed size
FIXED_WIDTH = 640
FIXED_HEIGHT = 472

def classify_pixel(r, g, b):
    """Classify pixel as 0x00 (sea/blue) or 0x01 (land/black)."""
    if b > r and b > g and b > 100:
        return 0x00  # sea
    elif (r + g + b) / 3 < 50:
        return 0x01  # land
    else:
        return 0x01  # everything else treated as land

def bmp_to_dat(bmp_path):
    """Convert BMP → nav_matrix.dat using fixed 640x472 size."""
    img = Image.open(bmp_path).convert("RGB")
    img = img.resize((FIXED_WIDTH, FIXED_HEIGHT))  # force fixed resolution
    pixels = list(img.getdata())

    # Create binary data with header (width + height)
    binary_data = bytearray()
    binary_data += struct.pack("<HH", FIXED_WIDTH, FIXED_HEIGHT)  # 2 bytes each

    for r, g, b in pixels:
        binary_data.append(classify_pixel(r, g, b))

    # Always save as nav_matrix.dat in the same directory as the input file
    output_dir = os.path.dirname(bmp_path)
    dat_path = os.path.join(output_dir, "nav_matrix.dat")

    with open(dat_path, "wb") as f:
        f.write(binary_data)

    print(f"✅ Conversion complete: {dat_path}")
    messagebox.showinfo("Done", f"File saved as:\n{dat_path}")

def dat_to_bmp(dat_path):
    """Convert DAT → BMP (auto reads header but enforces 640x472 display)."""
    with open(dat_path, "rb") as f:
        data = f.read()

    if len(data) < 4:
        print("❌ Invalid DAT file: too small to contain header.")
        return

    # Read width & height (but we can also enforce our fixed size)
    width, height = struct.unpack("<HH", data[:4])
    print(f"Detected size in header: {width}x{height}")

    pixel_data = data[4:]
    expected_size = FIXED_WIDTH * FIXED_HEIGHT

    if len(pixel_data) != expected_size:
        print(f"⚠️ Warning: pixel data size ({len(pixel_data)}) does not match expected {FIXED_WIDTH}x{FIXED_HEIGHT}")
        return

    img = Image.new("RGB", (FIXED_WIDTH, FIXED_HEIGHT))
    pixels = img.load()

    for i, value in enumerate(pixel_data):
        x = i % FIXED_WIDTH
        y = i // FIXED_WIDTH
        if value == 0x00:
            pixels[x, y] = (0, 0, 255)   # sea (blue)
        elif value == 0x01:
            pixels[x, y] = (0, 0, 0)     # land (black)
        else:
            pixels[x, y] = (255, 0, 255) # unknown (magenta)

    bmp_path = os.path.splitext(dat_path)[0] + "_reconstructed.bmp"
    img.save(bmp_path)
    print(f"✅ Image reconstructed: {bmp_path}")
    messagebox.showinfo("Done", f"Image saved as:\n{bmp_path}")

def main():
    root = Tk()
    root.withdraw()

    choice = messagebox.askquestion(
        "Image Conversion",
        "Do you want to convert from BMP to DAT?\n(Choose 'No' for DAT → BMP)"
    )

    if choice == "yes":
        bmp_path = filedialog.askopenfilename(
            title="Select a BMP file",
            filetypes=[("Bitmap files", "*.bmp")]
        )
        if bmp_path:
            bmp_to_dat(bmp_path)
        else:
            print("No file selected.")
    else:
        dat_path = filedialog.askopenfilename(
            title="Select a DAT file",
            filetypes=[("DAT files", "*.dat")]
        )
        if dat_path:
            dat_to_bmp(dat_path)
        else:
            print("No file selected.")

if __name__ == "__main__":
    main()

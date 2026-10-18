import os
import sys
import socket
import requests
from PIL import Image

orig_getaddrinfo = socket.getaddrinfo
def ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = ipv4_getaddrinfo

dest_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data", "crop_heldout_set")
os.makedirs(dest_dir, exist_ok=True)
print("Held-out destination directory:", dest_dir)

heldout_sources = [
    (
        "heldout_01_rice_brown_spot.jpg",
        "https://raw.githubusercontent.com/MHassaanButt/Rice-Disease-Classfication/master/Dataset/Brown%20spot/DSC_0108.jpg",
        "Paddy / Rice",
        "plant_disease",
        "Rice Brown Spot (Bipolaris oryzae)"
    ),
    (
        "heldout_02_rice_bacterial_blight.jpg",
        "https://raw.githubusercontent.com/MHassaanButt/Rice-Disease-Classfication/master/Dataset/Bacterial%20leaf%20blight/DSC_0365.JPG",
        "Paddy / Rice",
        "plant_disease",
        "Bacterial Leaf Blight (Xanthomonas oryzae)"
    ),
    (
        "heldout_03_tomato_septoria_spot.jpg",
        "https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Septoria_leaf_spot/002533c1-722b-44e5-9d2e-91f7747b2543___Keller.St_CG%201831.JPG",
        "Tomato",
        "plant_disease",
        "Tomato Septoria Leaf Spot (Septoria lycopersici)"
    ),
    (
        "heldout_04_tomato_healthy.jpg",
        "https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___healthy/000146ff-92a4-4db6-90ad-8fce2ae4fddd___GH_HL%20Leaf%20259.1.JPG",
        "Tomato",
        "healthy",
        "Healthy Tomato Leaf"
    ),
    (
        "heldout_05_corn_common_rust.jpg",
        "https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Corn_(maize)___Common_rust_/RS_Rust%201563.JPG",
        "Maize",
        "plant_disease",
        "Maize Common Rust (Puccinia sorghi)"
    ),
    (
        "heldout_06_corn_healthy.jpg",
        "https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Corn_(maize)___healthy/00031d74-076e-4aef-b040-e068cd3576eb___R.S_HL%208315%20copy%202.jpg",
        "Maize",
        "healthy",
        "Healthy Maize Foliage"
    ),
]

for filename, url, crop, category, condition in heldout_sources:
    out_path = os.path.join(dest_dir, filename)
    print(f"Downloading {filename}...")
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            with open(out_path, "wb") as f:
                f.write(r.content)
            img = Image.open(out_path)
            print(f"  -> SUCCESS: {filename}, Size: {img.size}, Bytes: {len(r.content)}")
        else:
            print(f"  -> FAILED: HTTP {r.status_code}")
    except Exception as e:
        print(f"  -> ERROR: {e}")

# Non-crop specimen
from PIL import ImageDraw, ImageFilter
pen_img = Image.new("RGB", (320, 320), color=(180, 130, 90))
draw = ImageDraw.Draw(pen_img)
draw.line([(60, 260), (260, 60)], fill=(20, 30, 90), width=14)
draw.polygon([(260, 60), (280, 40), (270, 70)], fill=(180, 180, 190))
pen_path = os.path.join(dest_dir, "heldout_07_non_crop_pen.jpg")
pen_img.save(pen_path, format="JPEG", quality=90)
print(f"  -> Generated {pen_path}")

# Blurry specimen
blur_img = Image.new("RGB", (320, 320), color=(110, 130, 90))
draw = ImageDraw.Draw(blur_img)
draw.ellipse([80, 80, 240, 240], fill=(80, 150, 70))
blur_img = blur_img.filter(ImageFilter.GaussianBlur(radius=35))
blur_path = os.path.join(dest_dir, "heldout_08_blurry_unidentifiable.jpg")
blur_img.save(blur_path, format="JPEG", quality=75)
print(f"  -> Generated {blur_path}")

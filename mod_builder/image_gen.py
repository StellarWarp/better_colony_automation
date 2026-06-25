import os
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from game_paths import GAME_ROOT

def resize_dds_batch(input_folder, output_folder, length = 50):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".dds"):
            with Image.open(os.path.join(input_folder, filename)) as img:
                new_size = (length, length)
                resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
                resized_img.save(os.path.join(output_folder, filename))
                print(f"已处理: {filename} -> {new_size}")


INPUT_DIR = str(GAME_ROOT / "gfx" / "interface" / "icons" / "districts" / "district_specialization_icons")
OUTPUT_DIR_50 = r"../gfx/interface/bca_districts/large"
OUTPUT_DIR_25 = r"../gfx/interface/bca_districts/small"
resize_dds_batch(INPUT_DIR, OUTPUT_DIR_50, length=50)
resize_dds_batch(INPUT_DIR, OUTPUT_DIR_25, length=25)

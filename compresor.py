import os
from PIL import Image

def compress_in_place_or_copy(input_dir, output_dir, max_width=1920, quality=75):
    """
    Aggressively compresses JPEG/PNG images, keeping their original formats
    while stripping metadata and optimizing structure.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png']:
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)

            try:
                with Image.open(input_path) as img:
                    # Capture original size for the final report
                    orig_size = os.path.getsize(input_path) / 1024

                    # 1. Resize if unnecessarily large (keeps aspect ratio)
                    width, height = img.size
                    if width > max_width:
                        ratio = max_width / float(width)
                        new_height = int(float(height) * float(ratio))
                        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                    # 2. Format-specific optimization
                    if ext in ['.jpg', '.jpeg']:
                        # Convert to RGB to ensure compatibility
                        if img.mode != 'RGB':
                            img = img.convert('RGB')

                        # Save JPEG with aggressive but clean settings
                        img.save(
                            output_path,
                            'JPEG',
                            quality=quality,
                            optimize=True,     # Recompute huffman tables (smaller size)
                            progressive=True   # Loads progressively on slow websites
                        )

                    elif ext == '.png':
                        # Quantize PNG to 8-bit paletted image (massive savings for graphics/logos)
                        # We use adaptive palette to preserve colors
                        img_optimized = img.quantize(colors=256, method=Image.Quantizing.FASTOCTREE)

                        img_optimized.save(
                            output_path,
                            'PNG',
                            optimize=True      # Tries harder to find smaller compression blocks
                        )

                    new_size = os.path.getsize(output_path) / 1024
                    savings = ((orig_size - new_size) / orig_size) * 100
                    print(f"Compressed {filename}: {orig_size:.1f}KB -> {new_size:.1f}KB | Saved {savings:.1f}%")

            except Exception as e:
                print(f"Error processing {filename}: {e}")

# --- RUN THE COMPRESSION ---
if __name__ == "__main__":
    INPUT_FOLDER = "./media/destinations"
    OUTPUT_FOLDER = "./same_format_optimized"

    print("Starting same-format compression...")
    # Using quality=75 for JPEGs strikes an incredibly strong balance for the web
    compress_in_place_or_copy(INPUT_FOLDER, OUTPUT_FOLDER, max_width=1920, quality=75)
    print("Done!")
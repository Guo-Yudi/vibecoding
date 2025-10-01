import cv2
import os
from PIL import Image
from PIL.ExifTags import TAGS
def get_exif_date(image_path):
    """Extracts the capture date from the image's EXIF data."""
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        if exif_data:
            for tag, value in exif_data.items():
                tag_name = TAGS.get(tag, tag)
                if tag_name == 'DateTimeOriginal':
                    return value.split(' ')[0].replace(':', '-')
    except Exception as e:
        print(f"Error reading EXIF data: {e}")
    return None

def add_watermark(image_path, output_path, text, font_size, color, position):
    """Adds a text watermark to an image."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"Error: Could not read image from {image_path}")
            return

        h, w, _ = img.shape
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = font_size / 20.0
        thickness = 2

        text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
        text_w, text_h = text_size

        if position == 'top-left':
            pos = (10, text_h + 10)
        elif position == 'center':
            pos = ((w - text_w) // 2, (h + text_h) // 2)
        elif position == 'bottom-right':
            pos = (w - text_w - 10, h - 10)
        else:
            print("Error: Invalid position specified.")
            return

        cv2.putText(img, text, pos, font, font_scale, color, thickness, cv2.LINE_AA)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, img)
        print(f"Watermarked image saved to {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    # Get image path from user
    image_path = input("Enter the path to the image: ")

    # Get font size
    while True:
        try:
            font_size_str = input("Enter font size (default: 20): ")
            if not font_size_str:
                font_size = 20
                break
            font_size = int(font_size_str)
            break
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Get color
    while True:
        try:
            color_str = input("Enter color as B,G,R (e.g., 255,255,255 for white, default is white): ")
            if not color_str:
                color = (255, 255, 255)
                break
            color = tuple(map(int, color_str.split(',')))
            if len(color) != 3:
                raise ValueError
            break
        except (ValueError, TypeError):
            print("Invalid format. Please enter three numbers separated by commas (e.g., 255,0,0).")

    # Get position
    positions = ['top-left', 'center', 'bottom-right']
    while True:
        position = input(f"Enter position ({'/'.join(positions)}, default: bottom-right): ")
        if not position:
            position = 'bottom-right'
            break
        if position in positions:
            break
        else:
            print(f"Invalid position. Please choose one of: {', '.join(positions)}")


    image_dir = os.path.dirname(image_path)
    save_dir = os.path.join(image_dir, 'save')

    watermark_text = get_exif_date(image_path)
    if not watermark_text:
        print("Could not find date information in EXIF data. Using current date.")
        from datetime import datetime
        watermark_text = datetime.now().strftime("%Y-%m-%d")

    file_name_base, file_ext = os.path.splitext(os.path.basename(image_path))
    output_image_path = os.path.join(save_dir, f"{file_name_base}{file_ext}")
    
    counter = 1
    while os.path.exists(output_image_path):
        output_image_path = os.path.join(save_dir, f"{file_name_base}({counter}){file_ext}")
        counter += 1
    
    add_watermark(image_path, output_image_path, watermark_text, font_size, color, position)

if __name__ == "__main__":
    main()
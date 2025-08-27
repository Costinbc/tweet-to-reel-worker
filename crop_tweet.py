import cv2
import numpy as np
import os
from PIL import Image, ImageDraw
import sys


def generate_rounded_mask(input_image, output_path):
    image = Image.open(input_image)
    width, height = image.size
    radius = 30
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)
    mask.save(output_path)


def pad_image_reel(input_image, color, output_path):
    image = Image.open(input_image)
    width, height = image.size
    target_width, target_height = 1080, height

    if color == "white" or "blur":
        bg_color = (0, 0, 0, 0)
    elif color == "black":
        bg_color = (0, 0, 0, 255)
    else:
        raise ValueError("Color must be 'white', 'black', or 'blur'")
    padded_image = Image.new("RGBA", (target_width, target_height), bg_color)
    offset_x = (target_width - width) // 2
    offset_y = (target_height - height) // 2
    padded_image.paste(image, (offset_x, offset_y))

    padded_image.save(output_path)
    print(f"✅ Padded image saved to: {output_path}")


def apply_mask(image_path, mask_path, output_path):
    try:
        image = Image.open(image_path).convert("RGBA")
        mask = Image.open(mask_path).convert("L")

        if image.size != mask.size:
            mask = mask.resize(image.size, Image.LANCZOS)

        image.putalpha(mask)
        image.save(output_path, format="PNG")
        print(f"Created transparent image {output_path}")
        return output_path
    except Exception as e:
        print(f"Error creating transparent image: {e}")
        raise


def extract_tweet_card(input_path, output_path=None, tweet_type="video", reel_type=None):
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Could not open image at {input_path}")

    if tweet_type == "video":
        width_crop = 40
    else:
        width_crop = 7

    height, width = img.shape[:2]

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([40, 255, 255])

    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    inverted_mask = cv2.bitwise_not(yellow_mask)

    contours, _ = cv2.findContours(inverted_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        print("No contours found in the image.")

    largest_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest_contour)

    margin = 0
    x = max(0, x - margin)
    y = max(0, y - margin)
    w = min(width - x, w + 2*margin)
    h = min(height - y, h + 2*margin)

    tweet_card = img[y + 7:y+h - 50, x+width_crop:x+w-width_crop]

    if output_path is None:
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}_card_only.png"

    if tweet_type == "video":
        img_pil = Image.fromarray(cv2.cvtColor(tweet_card, cv2.COLOR_BGR2RGB))
        original_width, original_height = img_pil.size


        inner_width = min(original_width, 900)
        new_height = int(original_height * (inner_width / original_width))
        resized = img_pil.resize((inner_width, new_height), Image.LANCZOS)

        padding = 800

        if reel_type == "blur" or reel_type == "white":
            color = "white"
        elif reel_type == "black":
            color = "black"
        else:
            raise ValueError("reel_type must be 'white', 'black', or 'blur'")

        canvas = Image.new("RGB", (padding, new_height), color)
        offset_x = (padding - inner_width) // 2
        canvas.paste(resized, (offset_x, 0))
        canvas.save(output_path)

    if tweet_type == "photo":
        bgr_tweet = tweet_card
        b, g, r = cv2.split(bgr_tweet)
        alpha = np.ones(b.shape, dtype=b.dtype) * 255
        rgba_tweet = cv2.merge((b, g, r, alpha))

        cv2.imwrite(output_path, rgba_tweet)

    return output_path

def pad_photo(input_path, output_path=None):
    img = Image.open(input_path)
    src_width, src_height = img.size
    src_ratio = src_width / src_height

    target_height = 1350
    target_width = 1080
    target_ratio = target_width / target_height

    if src_ratio > target_ratio:
        new_width = target_width
        new_height = int(new_width / src_ratio)
    else:
        new_height = target_height
        new_width = int(new_height * src_ratio)

    img = img.resize((new_width, new_height), Image.LANCZOS)

    canvas = Image.new("RGB", (target_width, target_height), "white")

    offset_x = (target_width - new_width) // 2
    offset_y = (target_height - new_height) // 2
    canvas.paste(img, (offset_x, offset_y))

    if output_path is None:
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}_padded.jpg"

    canvas.save(output_path)
    print(f"✅ Padded image saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python crop_tweet.py <crop_action> [<reel_type>] <input_image_path> <output_image_path>")
        sys.exit(1)

    crop_action = sys.argv[1]
    reel_type = sys.argv[2]
    input_image_path = os.path.abspath(sys.argv[3])

    if crop_action == "tweet_card":
        output_image_path = os.path.abspath(sys.argv[4])
        extract_tweet_card(input_image_path, output_image_path, "video", reel_type)
    elif crop_action == "photo_card":
        output_image_path = os.path.abspath(sys.argv[4])
        extract_tweet_card(input_image_path, output_image_path, "photo")
    elif crop_action == "pad_photo":
        output_image_path = os.path.abspath(sys.argv[4])
        pad_photo(input_image_path, output_image_path)
    elif crop_action == "pad_image_reel":
        output_image_path = os.path.abspath(sys.argv[4])
        pad_image_reel(input_image_path, reel_type, output_image_path)
    elif crop_action == "generate_mask":
        output_image_path = os.path.abspath(sys.argv[4])
        generate_rounded_mask(input_image_path, output_image_path)
    elif crop_action == "apply_mask":
        if len(sys.argv) < 5:
            print("Usage: python crop_tweet.py apply_mask <reel_type> <input_image_path> <mask_path> <output_image_path>")
            sys.exit(1)
        output_image_path = os.path.abspath(sys.argv[5])
        mask_path = os.path.abspath(sys.argv[4])
        apply_mask(input_image_path, mask_path, output_image_path)
    else:
        print("Invalid crop action.")
        sys.exit(2)

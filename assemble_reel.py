import subprocess
import os
import sys
from PIL import Image, ImageDraw


LAYOUTS = {
    "video_top"   : "[v_scaled][img_padded]vstack_cuda[stacked];",
    "video_bottom": "[img_padded][v_scaled]vstack_cuda[stacked];"
}

def assemble(layout, background, cropped, image, video, output):
    img_branch = "[1:v]hwupload_cuda[img_on_gpu];[img_on_gpu]pad_cuda=w=1080:h=ih:x=(1080-iw)/2:y=0:color=0x00000000[img_padded];"

    if background == "blur":
        bg_filter = "[0:v]hwupload_cuda,scale_npp=w=1080:h=1920:force_original_aspect_ratio=increase,crop=w=1080:h=1920:x=0:y=0,gblur_cuda=sigma=20[bg];"
    else:
        bg_filter = "color=c=white:s=1080x1920,hwupload_cuda[bg];"

    if cropped:
        vid_filter = "[0:v]hwupload_cuda,crop_cuda=w='min(iw,ih)':h='min(iw,ih)',scale_npp=w=1080:h=1080[v_scaled];"
    else:
        vid_filter = "[0:v]hwupload_cuda,scale_npp=w=1080:h=-2[v_scaled];"

    try:
        stack_filter = LAYOUTS[layout]
    except KeyError:
        raise ValueError(f"unsupported layout '{layout}'")

    fc = "".join([
        bg_filter,
        vid_filter,
        img_branch,
        stack_filter,
        "[bg][stacked]overlay_cuda=x=(W-w)/2:y=((H-h)/2+70)[final]"
    ])

    cmd = [
        "ffmpeg",
        "-y",
        "-hwaccel", "cuda",
        "-hwaccel_output_format", "cuda",
        "-i", video,
        "-i", image,
        "-filter_complex", fc,
        "-map", "[final]",
        "-map", "0:a?",
        "-c:v", "h264_nvenc",
        "-preset", "p5",
        "-qp", "23",
        "-c:a", "copy",
        "-shortest",
        output
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print("ffmpeg error", e.stderr)
        raise

if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Usage: python assemble_reel.py <layout> <background> <crop> <image> <video> <output>")
        sys.exit(1)

    reel_layout = sys.argv[1]
    reel_background = sys.argv[2]
    reel_crop = sys.argv[3]
    image_path = os.path.abspath(sys.argv[4])
    video_path = os.path.abspath(sys.argv[5])
    output_path = os.path.abspath(sys.argv[6])

    if not os.path.exists(image_path):
        print(f"Image file '{image_path}' does not exist.")
        sys.exit(1)

    if not os.path.exists(video_path):
        print(f"Video file '{video_path}' does not exist.")
        sys.exit(1)

    print("received arguments:")
    print(f"Layout: {reel_layout}")
    print(f"Background: {reel_background}")
    print(f"Crop: {reel_crop}")
    print(f"Image path: {image_path}")
    print(f"Video path: {video_path}")
    print(f"Output path: {output_path}")

    # if reel_background == "white":
    #     print("Creating the reel with white background...")
    #     assemble_reel_white(image_path, video_path, output_path)
    # elif reel_type == "blur":
    #     print("Generating rounded mask...")
    #     mask_path = os.path.splitext(image_path)[0] + "_mask.png"
    #     generate_rounded_mask(image_path, mask_path)
    #     print("Creating the reel with blurred background...")
    #     assemble_reel_blur(image_path, video_path, mask_path, output_path)
    # else:
    #     print("Invalid reel type. Use 'white' or 'blur'.")
    #     sys.exit(1)

    print(f"Creating the reel with layout '{reel_layout}' and background '{reel_background}'...")
    mask_path = None
    if reel_background == "blur":
        mask_path = os.path.splitext(image_path)[0] + "_mask.png"
        generate_rounded_mask(image_path, mask_path)
    if reel_crop == "cropped":
        assemble(reel_layout, reel_background, True, image_path, video_path, output_path, mask_path)
    elif reel_crop == "uncropped":
        assemble(reel_layout, reel_background, False, image_path, video_path, output_path, mask_path)
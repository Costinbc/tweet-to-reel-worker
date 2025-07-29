import subprocess
import os
import sys
from PIL import Image, ImageDraw


LAYOUTS = {
    "video_top": "[vid][img_padded]vstack=inputs=2[stacked]",
    "video_bottom": "[img_padded][vid]vstack=inputs=2[stacked]"
}

def assemble(layout, background, cropped, image, video, output, mask=None):

    if cropped:
        vid_filter = "[0:v]crop='min(iw,ih)':'min(iw,ih)',scale=1080:1080[vid]"
    else:
        vid_filter = "[0:v]scale=1080:-2[vid]"

    if background == "blur":
        bg_filter = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,boxblur=35:1[bg]"
        )
    else:
        bg_filter = "color=white:s=1080x1920:d=5[bg]"

    img_branch = "[1:v]format=rgba[img];"
    if mask is not None:
        img_branch += (
            "[2:v]scale=iw:ih[mask];"
            "[img][mask]alphamerge[rounded];"
            "[rounded]pad=1080:ih:(ow-iw)/2:0:color=0x00000000[img_padded]"
        )
    else:
        img_branch += (
            "[img]pad=1080:ih:(ow-iw)/2:0:color=0x00000000[img_padded]"
        )

    try:
        stack_filter = LAYOUTS[layout]
    except KeyError:
        raise ValueError(f"unsupported layout '{layout}'")

    final_composition = (
        "[bg][stacked]overlay=(W-w)/2:((H-h)/2+70)[final_cpu];"
        "[final_cpu]hwupload_cuda[final_gpu]"
    )

    fc = ";".join([
        bg_filter,
        vid_filter,
        img_branch,
        stack_filter,
        final_composition
    ])

    cmd = ["ffmpeg",
           "-y",
           "-i", video,
           "-i", image]
    if mask is not None:
        cmd += ["-i", mask]

    cmd += [
        "-filter_complex", fc,
        "-map", "[final_gpu]",
        "-map", "0:a?",
        "-c:v", "h264_nvenc",
        "-c:a", "copy",
        "-preset", "p5",
        "-qp", "23",
        "-shortest", output
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
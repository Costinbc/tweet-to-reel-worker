import subprocess
import os
import sys
from PIL import Image, ImageDraw
from crop_tweet import generate_rounded_mask

LAYOUTS = {
    "video_top":    "[vid][img_padded]overlay_cuda=x='(main_w-overlay_w)/2':y=main_h[stacked];",
    "video_bottom": "[img_padded][vid]overlay_cuda=x='(main_w-overlay_w)/2':y=main_h[stacked];"
}

# facem background-ul separat in alta functie.
def create_background(background_type, input_video, output_path):
    if background_type == "white":
        bg_filter = (
            "color=c=white:s=1080x1920:d=5[bg];"
            "[bg]format=yuv420p,hwupload_cuda[bg_final]"
        )
    elif background_type == "blur":
        bg_filter = (
            "[0:v]hwupload_cuda,"
            "scale_cuda=1080:1920:force_original_aspect_ratio=increase:"
            "format=yuv444p,"
            "bilateral_cuda=window_size=15:sigmaS=8:sigmaR=75,"
            "scale_cuda=format=yuv420p[bg_final]"
        )
    else:
        raise ValueError("background must be 'white' or 'blur'")

    cmd = [
        "/usr/local/bin/ffmpeg", "-y",
        "-i", input_video,
        "-filter_complex", bg_filter,
        "-map", "[bg_final]",
        "-c:v", "h264_nvenc",
        "-preset", "p5",
        "-qp", "23",
        output_path
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as err:
        err_text = (err.stderr or b"").lower()
        if b"nvenc" in err_text:
            cmd[cmd.index("h264_nvenc")] = "libx264"
            cmd = [x for x in cmd if x not in ("-qp", "23")] + ["-crf", "23"]
            subprocess.run(cmd, check=True)

# in apply_mask() facem si padding pentru imagine
def apply_mask(image_path, mask_path, output_path):
    try:
        image = Image.open(image_path).convert("RGBA")
        mask = Image.open(mask_path).convert("L")

        if image.size != mask.size:
            mask = mask.resize(image.size, Image.LANCZOS)

        image.putalpha(mask)
        image.save(output_path, "PNG")
        print(f"Created transparent image {output_path}")
        return output_path
    except Exception as e:
        print(f"Error creating transparent image: {e}")
        raise


def assemble(layout, background, cropped, image, video, output, mask=None):
    masked_image_path = os.path.splitext(image)[0] + "_masked.png"
    masked_image = apply_mask(image, mask, masked_image_path) if mask else image

    just_background = True

    if just_background:
        create_background(background, video, output)
    else:

        img_branch = (
            "[1:v]format=yuv420p,pad=1080:ih:(1080-iw)/2:0:color=0x00000000,"
            "hwupload_cuda[img_padded];"
        )

        if background == "blur":
            video_split = "[0:v]split=2[v_for_bg][v_src];"
            bg_in = "[v_for_bg]"
            main_in = "[v_src]"
        else:
            video_split = ""
            bg_in = None
            main_in = "[0:v]"

        if background == "white":
            bg_filter = "color=c=white:s=1080x1920,format=yuv420p,hwupload_cuda[bg_final];"
        elif background == "blur":
            bg_filter = (
                f"{bg_in}hwupload_cuda,"
                "scale_cuda=1080:1920:force_original_aspect_ratio=increase,"
                "format=yuva444p,bilateral_cuda=window_size=15:sigmaS=8:sigmaR=75,"
                "scale_cuda=format=yuva420p[bg_final];"
            )
        else:
            raise ValueError("background must be 'white' or 'blur'")

        if cropped:
            vid_filter = (
                f"{main_in}"
                "crop='min(iw,ih)': 'min(iw,ih)',"
                "scale=1080:1080,format=yuv420p,"
                "hwupload_cuda[vid];"
            )
        else:
            vid_filter = (
                f"{main_in}"
                "scale=1080:-2,format=yuv420p,"
                "hwupload_cuda[vid];"
            )

        try:
            stack_filter = LAYOUTS[layout]
        except KeyError:
            raise ValueError(f"unsupported layout '{layout}'")

        overlay_filter = (
            "[bg_final][stacked]overlay_cuda="
            "x=(main_w-overlay_w)/2:y=(main_h-overlay_h)/2+70[final]"
        )

        fc = "".join([img_branch, video_split, vid_filter, bg_filter, stack_filter, overlay_filter])

        cmd = [
            "/usr/local/bin/ffmpeg", "-y",
            "-hwaccel", "cuda",
            "-hwaccel_output_format", "cuda",
            "-i", video,
            "-i", image,
            "-filter_complex", fc,
            "-map", "[final]",
            "-map", "0:a?",
            "-c:v", "h264_nvenc",
            "-c:a", "copy",
            "-preset", "p5",
            "-qp", "23",
            "-shortest",
            output
        ]

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as err:
            if b"nvenc" in err.stderr.lower():
                cmd[cmd.index("h264_nvenc")] = "libx264"
                cmd = [x for x in cmd if x not in ("-qp", "23")] + ["-crf", "23"]
                subprocess.run(cmd, check=True)

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


    print(f"Creating the reel with layout '{reel_layout}' and background '{reel_background}'...")
    mask_path = None
    if reel_background == "blur":
        mask_path = os.path.splitext(image_path)[0] + "_mask.png"
        generate_rounded_mask(image_path, mask_path)
    if reel_crop == "cropped":
        assemble(reel_layout, reel_background, True, image_path, video_path, output_path, mask_path)
    elif reel_crop == "uncropped":
        assemble(reel_layout, reel_background, False, image_path, video_path, output_path, mask_path)
import subprocess
import os
import sys

LAYOUTS = {
    "video_top":
        "[vid_cpu][img_cpu]"
        "vstack=inputs=2[stack_cpu];",
    "video_bottom":
        "[img_cpu][vid_cpu]"
        "vstack=inputs=2[stack_cpu];",
    "video_overlay_top":
        "[vid_cpu][img_cpu]"
        "overlay="
          "x='(main_w-overlay_w)/2':"
          "y='300':"
          "eval=init"
        "[stack_cpu];",
    "video_overlay_bottom":
        "[vid_cpu][img_cpu]"
        "overlay="
          "x='(main_w-overlay_w)/2':"
          "y='main_h - overlay_h - 300':"
          "eval=init"
        "[stack_cpu];",
}


def estimate_time(duration, background_type):
    estimated_time = duration / 1.7 if background_type == "blur" else duration / 2.5
    return estimated_time


def decide_layout(video_width, video_height, layout):
    video_aspect = video_height / video_width

    if layout == "video_top":
        if video_aspect > 1.2:
            return "video_overlay_top"
        else:
            return layout
    elif layout == "video_bottom":
        if video_aspect > 1.2:
            return "video_overlay_bottom"
        else:
            return layout


def create_background(background_type, input_video, output_path):
    if background_type == "blur":
        bg_filter = (
            "[0:v]hwupload_cuda,"
            "scale_cuda=w=360:h=640:force_original_aspect_ratio=increase,"
            "hwdownload,format=yuv420p,"
            "crop=360:640:x=(in_w-out_w)/2:y=(in_h-out_h)/2,"
            "hwupload_cuda,"
            "scale_cuda=w='2*floor(iw/8/2)':h='2*floor(ih/8/2)':interp_algo=bilinear,"
            "bilateral_cuda=window_size=16:sigmaS=12.0:sigmaR=120.0,"
            "scale_cuda=w=1080:h=1920:format=nv12"
            "[bg_final]"
        )
    else:
        raise ValueError("background must be 'white' or 'blur'")

    cmd = [
        "/usr/local/bin/ffmpeg", "-y",
        "-i", input_video,
        "-filter_complex", bg_filter,
        "-map", "[bg_final]",
        "-c:v", "h264_nvenc",
        "-preset","p2",
        "-b:v","6M",
        output_path
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as err:
        print(f"Error during background creation: {err}")
        raise


def assemble(layout, background, cropped, image, video, output, background_path=None):

    if background == "blur":
        background_path = os.path.splitext(video)[0] + "_bg.mp4"
        create_background("blur", video, background_path)
    elif background == "white" or background == "black":
        if background_path is None:
            print("No background path provided for white background.")
        elif not os.path.exists(background_path):
            print(f"Background file '{background_path}' does not exist.")
            raise FileNotFoundError(f"Background file '{background_path}' not found.")

    img_branch = (
        "[1:v]format=rgba,"
        "pad=w=1080:h=ih:x='(1080-iw)/2':y=0:color=0x00000000[img_cpu];"
    )
    if background == "blur":
        bg_branch = "[2:v]scale_cuda=format=yuv420p[bg_gpu];"
    elif background == "white" or background == "black":
        bg_branch = (
            "[2:v]format=yuv420p,"
            "hwupload_cuda[bg_gpu];"
        )
    else:
        raise ValueError("background must be 'white', 'black' or 'blur'")

    if cropped:
        vid_filter = (
            "[0:v]"
            "crop='min(iw,ih)':'min(iw,ih)',"
            "scale=1080:1080[vid_cpu];"
        )
    else:
        vid_filter = (
            "[0:v]"
            "scale=1080:-2[vid_cpu];"
        )

    try:
        stack_filter = LAYOUTS[layout]
    except KeyError:
        raise ValueError(f"unsupported layout '{layout}'")

    post_stack = (
        "[stack_cpu]format=yuva420p,hwupload_cuda[stack_gpu];"
        "[bg_gpu][stack_gpu]"
        "overlay_cuda=x='(W-w)/2':y='(H-h)/2'[final]"
    )

    fc = "".join([img_branch, bg_branch, vid_filter, stack_filter, post_stack])

    if background == "blur":
        background_input = ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda", "-i", background_path]
    else:
        background_input = ["-loop", "1", "-i", background_path]

    cmd = [
        "/usr/local/bin/ffmpeg", "-y",
        "-i", video,
        "-loop","1","-i", image,
        *background_input,
        "-filter_complex", fc,
        "-map", "[final]",
        "-map", "0:a?",
        "-c:v", "h264_nvenc",
        "-c:a", "copy",
        "-preset","p2",
        "-b:v","6M",
        "-shortest",
        output
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as err:
        print(f"Error during assembly: {err}")
        raise

if __name__ == "__main__":
    if len(sys.argv) < 7:
        print("Usage: python assemble_reel.py <layout> <background> <crop> <image> <video> <output> [background_path]")
        sys.exit(1)

    reel_layout = sys.argv[1]
    reel_background = sys.argv[2]
    reel_crop = sys.argv[3]
    image_path = os.path.abspath(sys.argv[4])
    video_path = os.path.abspath(sys.argv[5])
    output_path = os.path.abspath(sys.argv[6])
    bg_path = sys.argv[7] if len(sys.argv) > 7 else None

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
    if reel_crop == "cropped":
        assemble(reel_layout, reel_background, True, image_path, video_path, output_path, background_path=bg_path)
    elif reel_crop == "uncropped":
        assemble(reel_layout, reel_background, False, image_path, video_path, output_path, background_path=bg_path)
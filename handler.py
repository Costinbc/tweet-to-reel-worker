from assemble_reel import assemble, estimate_time, decide_layout
from probe_video import probe_video
from screenshot_ors import download_tweet_image
from crop_tweet import extract_tweet_card
from video_dl import download_tweet_video
from crop_tweet import generate_rounded_mask
from crop_tweet import apply_mask
import runpod, os, uuid, requests


def handler(job):
    """Handler function that will be used to process jobs."""
    job_input = job.get("input", {})

    required = {"upload_url", "public_url", "tweet_url"}
    if not required.issubset(job_input):
        return {"status": "warm", "seen_keys": list(job_input.keys())}

    print("Received job input:", job_input)

    job_upload_url = job_input["upload_url"]
    public_url = job_input["public_url"]
    tweet_url = job_input["tweet_url"]
    layout = job_input["layout"]
    only_video = job_input.get("only_video", "false")
    hide_quoted_tweet = job_input.get("hide_quoted_tweet", "false")
    background = job_input["background"]
    cropped = job_input["cropped"]

    if only_video == "true":
        only_video = True
    else:
        only_video = False

    if hide_quoted_tweet == "true":
        hide_quoted_tweet = True
    else:
        hide_quoted_tweet = False

    tweet_id = tweet_url.split("/")[-1].split("?")[0]

    job_id = str(uuid.uuid4())

    downloads_dir = f"/tmp/{job_id}_downloads"
    results_dir = f"/tmp/{job_id}_results"
    backgrounds_dir = f"../backgrounds"
    os.makedirs(downloads_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    img_raw = os.path.join(downloads_dir, f"{tweet_id}.png")
    video_path = os.path.join(downloads_dir, f"{tweet_id}_video.mp4")
    reel_output = os.path.join(results_dir, f"{job_id}_reel.mp4")
    img_final = os.path.join(results_dir, f"{job_id}_photo.png")


    download_tweet_video(tweet_url, video_path)

    video_probe = probe_video(video_path)

    duration = video_probe.get("duration", 0.0)
    if duration <= 0.0:
        return {"status": "error", "message": "Failed to retrieve video duration."}
    width = video_probe.get("width", 0)
    height = video_probe.get("height", 0)
    if width <= 0 or height <= 0:
        return {"status": "error", "message": "Failed to retrieve video dimensions."}

    time_estimate = estimate_time(duration, only_video)
    runpod.serverless.progress_update(job, f"Estimated time: {time_estimate} seconds")
    if not cropped:
        layout = decide_layout(width, height, layout)

    if not only_video:
        download_tweet_image("video", False, hide_quoted_tweet, background, tweet_url, tweet_id, img_raw)

        extract_tweet_card(img_raw, img_final, "video", background)
        mask_path = os.path.splitext(img_final)[0] + "_mask.png"
        generate_rounded_mask(img_final, mask_path)
        apply_mask(img_final, mask_path, img_final)

        if background == "blur":
            assemble(layout=layout, background=background, cropped=cropped, image=img_final, video=video_path, output=reel_output)
        elif background == "white":
            background_path = os.path.join(backgrounds_dir, "white_background_1080x1920.png")
            assemble(layout=layout, background=background, cropped=cropped, image=img_final, video=video_path, output=reel_output, background_path=background_path)
        elif background == "black":
            background_path = os.path.join(backgrounds_dir, "black_background_1080x1920.png")
            assemble(layout=layout, background=background, cropped=cropped, image=img_final, video=video_path, output=reel_output, background_path=background_path)
    else:
        if background == "blur":
            assemble(layout=layout, background=background, cropped=cropped, image=None, video=video_path, output=reel_output)
        elif background == "white":
            background_path = os.path.join(backgrounds_dir, "white_background_1080x1920.png")
            assemble(layout=layout, background=background, cropped=cropped, image=None, video=video_path, output=reel_output, background_path=background_path)
        elif background == "black":
            background_path = os.path.join(backgrounds_dir, "black_background_1080x1920.png")
            assemble(layout=layout, background=background, cropped=cropped, image=None, video=video_path, output=reel_output, background_path=background_path)

    with open(reel_output, "rb") as f:
        requests.put(job_upload_url, data=f, headers={"Content-Type": "video/mp4"})

    return {"status": "done", "url": public_url}


runpod.serverless.start({"handler": handler})

from assemble_reel import assemble
from screenshot_ors import download_tweet_image
from crop_tweet import extract_tweet_card, pad_image_reel
from video_dl import download_tweet_video
from crop_tweet import generate_rounded_mask
from crop_tweet import apply_mask
from PIL import Image
import runpod, os, uuid, requests


def handler(job):
    """Handler function that will be used to process jobs."""
    job_input = job.get("input", {})

    required = {"upload_url", "public_url", "tweet_url"}
    if not required.issubset(job_input):
        return {"status": "warm", "seen_keys": list(job_input.keys())}

    job_upload_url = job_input["upload_url"]
    public_url = job_input["public_url"]
    tweet_url = job_input["tweet_url"]
    layout = job_input["layout"]
    background = job_input["background"]
    cropped = job_input["cropped"]

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
    download_tweet_image("video", tweet_url, tweet_id, img_raw)

    extract_tweet_card(img_raw, img_final, "video", background)

    if background == "blur":
        mask_path = os.path.splitext(img_final)[0] + "_mask.png"
        generate_rounded_mask(img_final, mask_path)
        apply_mask(img_final, mask_path, img_final)
        pad_image_reel(img_final, img_final)
        assemble(layout, background, cropped, img_final, video_path, reel_output)
    elif background == "white":
        pad_image_reel(img_final, img_final)
        background_path = os.path.join(backgrounds_dir, "white_background_1080x1920.png")
        assemble(layout, background, cropped, img_final, video_path, reel_output, background_path=background_path)

    with open(reel_output, "rb") as f:
        requests.put(job_upload_url, data=f, headers={"Content-Type": "video/mp4"})

    return {"status": "done", "url": public_url}


runpod.serverless.start({"handler": handler})

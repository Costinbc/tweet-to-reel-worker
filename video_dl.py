import sys
import os
import yt_dlp

def download_tweet_video(tweet_url):
    tweet_id = tweet_url.split("/")[-1]
    script_path = os.path.abspath(__file__)
    project_root = os.path.abspath(os.path.join(script_path, "..", ".."))
    output_path = os.path.join(project_root, f"downloads/{tweet_id}_video.mp4")

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([tweet_url])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python video_dl.py <tweet_url>")
        sys.exit(1)

    tweet_url = sys.argv[1]
    download_tweet_video(tweet_url)

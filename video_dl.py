import sys
import os
import yt_dlp

def download_tweet_video(tweet_url, output_path=None):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        "ffmpeg_location": "/usr/bin/ffmpeg"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([tweet_url])

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python video_dl.py <tweet_url> <output_path>")
        sys.exit(1)

    tweet_url = sys.argv[1]
    output_path = sys.argv[2]
    download_tweet_video(tweet_url, output_path)

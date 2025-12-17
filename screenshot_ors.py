import orshot
import sys
import os
from dotenv import load_dotenv
load_dotenv()

def download_tweet_image(tweet_type, show_replied_to_tweet, hide_quoted_tweet, color, link, id, output_path):
    ors = orshot.Orshot(os.environ.get("ORSHOT_API_KEY"))
    tweet_url = link
    tweet_id = id

    if tweet_type == "photo":
        hide_media = False
    else:
        hide_media = True

    if color == "white" or color == "blur":
        tweet_background_color = "#fff"
        tweet_text_color = "#111"
    elif color == "black":
        tweet_background_color = "#000"
        tweet_text_color = "#fff"
    else:
        tweet_background_color = "#1da1f2"
        tweet_text_color = "#fff"

    modifications = {
        "tweetUrl": tweet_url,
        "tweetId": tweet_id,
        "hideMetrics": True,
        "hideVerifiedIcon": False,
        "tweetFontSize": 2,
        "tweetBackgroundColor": tweet_background_color,
        "hideQuoteTweet": hide_quoted_tweet, # for now it's 'Quote' instead of 'Quoted' but hope the API will change it
        "tweetTextColor": tweet_text_color,
        "showRepliedToTweet": show_replied_to_tweet,
        "hideDateTime": True,
        "hideMedia": hide_media,
        "hideShadow": True,
        "backgroundColor": "#fff000",
        "backgroundImageUrl": "",
        "padding": 0,
        "width": 1000
    }

    response = ors.render_from_template({
    "template_id": "tweet-image",
    "response_type": "binary",
    "response_format": "png",
    "modifications": modifications
    })

    script_path = os.path.abspath(__file__)
    project_root = os.path.abspath(os.path.join(script_path, "..", ".."))
    downloads_dir = os.path.join(project_root, "downloads")
    os.makedirs(downloads_dir, exist_ok=True)

    with open(output_path, 'wb') as file:
        file.write(response.content)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python screenshot_ors.py <type> [showRepliedToTweet] <hideQuotedTweet> <color> <tweet_url> <output_path>")
        sys.exit(1)

    tweet_type = sys.argv[1]
    show_replied_to_tweet = False
    hide_quoted_tweet = False
    if tweet_type == 'photo':
        show_replied_to_tweet = True if sys.argv[2] == 'true' else False
        hide_quoted_tweet = True if sys.argv[3] == 'true' else False
        tweet_color = sys.argv[4]
        tweet_url = sys.argv[5]
        output_path = sys.argv[6]
    else:
        hide_quoted_tweet = True if sys.argv[2] == 'true' else False
        tweet_color = sys.argv[3]
        tweet_url = sys.argv[4]
        output_path = sys.argv[5]

    tweet_id = tweet_url.split('/')[-1]

    print("Downloading tweet image...")
    download_tweet_image(tweet_type, show_replied_to_tweet, hide_quoted_tweet, tweet_color, tweet_url, tweet_id, output_path)
    print(f"Done! Tweet image saved as {output_path}")

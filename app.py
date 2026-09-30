from flask import Flask, redirect
import requests
import re

app = Flask(__name__)

PLAYER_URL = (
    "https://player.field59.com/v4/channel/wapa/"
    "07679d068d54d4a6b52e3a42e27aa151d502b09a"
)


def get_wapa_url():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 13) "
            "AppleWebKit/537.36 "
            "Chrome/140 Safari/537.36"
        ),
        "Referer": "https://wapa.tv/envivo",
    }

    response = requests.get(
        PLAYER_URL,
        headers=headers,
        timeout=15
    )

    response.raise_for_status()

    # Find the current Field59 M3U8
    match = re.search(
        r'"m3u8"\s*:\s*"([^"]+\.m3u8)"',
        response.text
    )

    # Backup: look for "url"
    if not match:
        match = re.search(
            r'"url"\s*:\s*"([^"]+\.m3u8)"',
            response.text
        )

    if not match:
        raise RuntimeError(
            "Could not find a WAPA M3U8 URL."
        )

    return match.group(1)


@app.route("/")
def home():
    return "WAPA updater is running."


@app.route("/wapa.m3u8")
def wapa():

    try:
        # Get the newest signed Field59 URL
        current_url = get_wapa_url()

        # Redirect directly to it
        return redirect(
            current_url,
            code=302
        )

    except Exception as e:
        return (
            f"WAPA updater error: {e}",
            503
        )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080
    )

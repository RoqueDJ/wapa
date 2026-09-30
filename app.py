from flask import Flask, redirect
import requests
import re

app = Flask(__name__)

PLAYER_URL_41 = (
    "https://player.field59.com/v4/channel/wapa/"
    "07679d068d54d4a6b52e3a42e27aa151d502b09a"
)

PLAYER_URL_42 = (
    "https://player.field59.com/v4/channel/wapa/"
    "d80b343a9963f0ea3c810ddda1be9731237cc082"
)


def get_wapa_url(player_url, feed):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 13) "
            "AppleWebKit/537.36 "
            "Chrome/140 Safari/537.36"
        ),
        "Referer": "https://wapa.tv/envivo/",
    }

    response = requests.get(
        player_url,
        headers=headers,
        timeout=15
    )

    response.raise_for_status()

    pattern = (
        r'"(?:m3u8|url)"\s*:\s*"'
        r'(https://live\.field59\.com/[^"]*/wapa/'
        + re.escape(feed)
        + r'/playlist\.m3u8)"'
    )

    match = re.search(pattern, response.text)

    if not match:
        raise RuntimeError(
            f"Could not find {feed} in Field59 response."
        )

    return match.group(1)


@app.route("/")
def home():
    return "WAPA updater is running."


@app.route("/WAPA-TV-4-1.m3u8")
def wapa41():
    try:
        return redirect(
            get_wapa_url(PLAYER_URL_41, "wapa1"),
            code=302
        )
    except Exception as e:
        return f"WAPA 4.1 updater error: {e}", 503


@app.route("/WAPA-TV-4-2.m3u8")
def wapa42():
    try:
        return redirect(
            get_wapa_url(PLAYER_URL_42, "wapa2"),
            code=302
        )
    except Exception as e:
        return f"WAPA 4.2 updater error: {e}", 503


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080
    )

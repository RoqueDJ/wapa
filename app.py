from flask import Flask, redirect
import requests
import re

app = Flask(__name__)

PLAYER_URL = (
    "https://player.field59.com/v4/channel/wapa/"
    "07679d068d54d4a6b52e3a42e27aa151d502b09a"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13) "
        "AppleWebKit/537.36 "
        "Chrome/140 Safari/537.36"
    ),
    "Referer": "https://wapa.tv/envivo",
}


def get_wapa_url():
    response = requests.get(
        PLAYER_URL,
        headers=HEADERS,
        timeout=15
    )

    response.raise_for_status()

    # Look for the M3U8 inside the Field59 player configuration.
    match = re.search(
        r'"m3u8"\s*:\s*"([^"]+\.m3u8)"',
        response.text
    )

    if not match:
        match = re.search(
            r'"url"\s*:\s*"([^"]+\.m3u8)"',
            response.text
        )

    if not match:
        raise RuntimeError(
            "WAPA is currently between scheduled live events."
        )

    return match.group(1)


@app.route("/")
def home():
    return "WAPA 4.1 event-stream updater is running."


@app.route("/WAPA-TV-4-1.m3u8")
def wapa():
    try:
        current_url = get_wapa_url()

        return redirect(
            current_url,
            code=302
        )

    except Exception as e:
        return (
            f"WAPA 4.1 is currently unavailable.\n\n"
            f"{e}",
            503
        )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080
    )

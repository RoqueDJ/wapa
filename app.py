from flask import Flask, redirect
import requests
import re

app = Flask(__name__)

PLAYER_URL = (
    "https://player.field59.com/v4/channel/wapa/"
    "07679d068d54d4a6b52e3a42e27aa151d502b09a"
)

SCHEDULE_URL = (
    "https://player.field59.com/v4/schedule/wapa/"
    "9f91970fb55d5a5b1b18adeaf20fb8fd3f33e565"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13) "
        "AppleWebKit/537.36 "
        "Chrome/140 Safari/537.36"
    ),
    "Referer": "https://wapa.tv/envivo",
}


def test_stream(url):
    try:
        r = requests.get(
            url,
            headers=HEADERS,
            timeout=10,
            stream=True
        )

        return r.status_code == 200

    except Exception:
        return False


def get_player_url():
    response = requests.get(
        PLAYER_URL,
        headers=HEADERS,
        timeout=15
    )
    response.raise_for_status()

    match = re.search(
        r'"m3u8"\s*:\s*"([^"]+\.m3u8)"',
        response.text
    )

    if not match:
        match = re.search(
            r'"url"\s*:\s*"([^"]+\.m3u8)"',
            response.text
        )

    if match:
        return match.group(1)

    return None


def get_schedule_urls():
    response = requests.get(
        SCHEDULE_URL,
        headers=HEADERS,
        timeout=15
    )
    response.raise_for_status()

    urls = re.findall(
        r"<url>\s*<!\[CDATA\[(.*?)\]\]>\s*</url>",
        response.text,
        re.DOTALL
    )

    return [url.strip() for url in urls]


@app.route("/")
def home():
    return "WAPA 4.1 updater is running."


@app.route("/WAPA-TV-4-1.m3u8")
def wapa():

    try:
        # Try the channel player URL.
        player_url = get_player_url()

        if player_url and test_stream(player_url):
            return redirect(player_url, code=302)

        # Try URLs listed in the WAPA schedule.
        schedule_urls = get_schedule_urls()

        for url in schedule_urls:
            if "/wapa/wapa1/" in url and test_stream(url):
                return redirect(url, code=302)

        return (
            "WAPA 4.1: no currently valid stream was found.",
            503
        )

    except Exception as e:
        return f"WAPA updater error: {e}", 503


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080
    )

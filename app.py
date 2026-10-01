from flask import Flask
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
        # Get the current M3U8 URL from the Field59 player.
        player_url = get_player_url()

        if not player_url:
            return (
                "Field59 player returned no M3U8 URL.",
                503
            )

        # Test the URL without following redirects.
        response = requests.get(
            player_url,
            headers=HEADERS,
            timeout=10,
            allow_redirects=False
        )

        return (
            f"URL:\n"
            f"{player_url}\n\n"
            f"HTTP status: {response.status_code}\n\n"
            f"Headers:\n"
            f"{dict(response.headers)}\n\n"
            f"Body:\n"
            f"{response.text[:1000]}",
            response.status_code
        )

    except Exception as e:
        return (
            f"ERROR:\n{e}",
            503
        )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080
    )

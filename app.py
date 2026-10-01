from flask import Flask, redirect
import requests
import re
from datetime import datetime, timezone

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


def get_scheduled_url():
    response = requests.get(
        SCHEDULE_URL,
        headers=HEADERS,
        timeout=15
    )
    response.raise_for_status()

    xml = response.text
    now = datetime.now(timezone.utc)

    instances = re.findall(
        r"<instance>.*?"
        r"<url>\s*<!\[CDATA\[(.*?)\]\]>\s*</url>.*?"
        r"<begin>\s*<!\[CDATA\[(.*?)\]\]>\s*</begin>.*?"
        r"<end>\s*<!\[CDATA\[(.*?)\]\]>\s*</end>.*?"
        r"</instance>",
        xml,
        re.DOTALL
    )

    for url, begin, end in instances:
        begin_dt = datetime.strptime(
            begin.strip(),
            "%Y-%m-%d %H:%M"
        ).replace(tzinfo=timezone.utc)

        end_dt = datetime.strptime(
            end.strip(),
            "%Y-%m-%d %H:%M"
        ).replace(tzinfo=timezone.utc)

        if begin_dt <= now < end_dt:
            return url.strip()

    return None


@app.route("/")
def home():
    return "WAPA 4.1 updater is running."


@app.route("/WAPA-TV-4-1.m3u8")
def wapa():
    try:
        # First try the live Field59 channel player.
        player_url = get_player_url()

        if player_url:
            return redirect(player_url, code=302)

        # If that doesn't provide a stream, try the schedule.
        scheduled_url = get_scheduled_url()

        if scheduled_url:
            return redirect(scheduled_url, code=302)

        return "No WAPA 4.1 stream is currently available.", 503

    except Exception as e:
        return f"WAPA updater error: {e}", 503


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080
    )

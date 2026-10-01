from flask import Flask, redirect
import requests
import re
from datetime import datetime, timezone

app = Flask(__name__)

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


def get_schedule():
    response = requests.get(
        SCHEDULE_URL,
        headers=HEADERS,
        timeout=15
    )
    response.raise_for_status()
    return response.text


def get_current_wapa_url():
    xml = get_schedule()

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
        current_url = get_current_wapa_url()

        if not current_url:
            return (
                "WAPA 4.1 is currently between scheduled live events.",
                503
            )

        return redirect(current_url, code=302)

    except Exception as e:
        return f"WAPA updater error: {e}", 503


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080
    )

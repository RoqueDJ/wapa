from flask import Flask, redirect
import requests
import re

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


def get_streams():
    xml = get_schedule()

    urls = re.findall(
        r"<url>\s*<!\[CDATA\[(.*?)\]\]>\s*</url>",
        xml,
        re.DOTALL
    )

    # Only WAPA 4.1 streams
    streams = []

    for url in urls:
        url = url.strip()

        if "/wapa/wapa1/" in url:
            streams.append(url)

    return streams


def test_stream(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10,
            allow_redirects=False,
            stream=True
        )

        return response.status_code

    except Exception:
        return None


@app.route("/")
def home():
    return "WAPA 4.1 updater is running."


@app.route("/WAPA-TV-4-1.m3u8")
def wapa():

    try:
        streams = get_streams()

        if not streams:
            return (
                "No WAPA 4.1 streams were found in the schedule.",
                503
            )

        results = []

        for url in streams:

            status = test_stream(url)

            results.append(
                f"{status} - {url}"
            )

            if status == 200:
                return redirect(url, code=302)

        return (
            "No working WAPA 4.1 stream found.\n\n"
            + "\n".join(results),
            503
        )

    except Exception as e:
        return (
            f"WAPA updater error:\n{e}",
            503
        )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080
    )

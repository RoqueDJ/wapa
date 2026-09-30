from flask import Flask, Response
import requests
import re
import time
import threading

app = Flask(__name__)

PLAYER_URL = (
    "https://player.field59.com/v4/channel/wapa/"
    "07679d068d54d4a6b52e3a42e27aa151d502b09a"
)

REFRESH_SECONDS = 300

current_url = None
last_refresh = 0
lock = threading.Lock()


def fetch_wapa_url():
    global current_url, last_refresh

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
            "No WAPA M3U8 was found in Field59 response"
        )

    with lock:
        current_url = match.group(1)
        last_refresh = time.time()

    print("Updated WAPA URL:")
    print(current_url)

    return current_url


def refresh_loop():
    while True:
        try:
            fetch_wapa_url()
        except Exception as e:
            print("Refresh error:", e)

        time.sleep(REFRESH_SECONDS)


@app.route("/")
def home():
    return "WAPA updater is running."


@app.route("/wapa.m3u8")
def playlist():

    global current_url

    try:
        # Get a URL immediately if we don't have one yet.
        if current_url is None:
            fetch_wapa_url()

        return Response(
            "#EXTM3U\n"
            "#EXTINF:-1,WAPA-TV\n"
            f"{current_url}\n",
            mimetype="application/x-mpegURL"
        )

    except Exception as e:
        return Response(
            "#EXTM3U\n"
            f"# ERROR: {e}\n",
            status=503,
            mimetype="application/x-mpegURL"
        )


if __name__ == "__main__":

    # Start automatic background updater.
    thread = threading.Thread(
        target=refresh_loop,
        daemon=True
    )

    thread.start()

    app.run(
        host="0.0.0.0",
        port=8080
    )

from flask import Flask, Response
import requests
import re
import time

app = Flask(__name__)

PLAYER_URL = (
    "https://player.field59.com/v4/channel/wapa/"
    "07679d068d54d4a6b52e3a42e27aa151d502b09a"
)

CACHE_SECONDS = 60

cached_url = None
cached_at = 0


def get_wapa_url():
    global cached_url, cached_at

    now = time.time()

    # Reuse the current URL briefly instead of requesting Field59
    # for every IPTV player request.
    if cached_url and now - cached_at < CACHE_SECONDS:
        return cached_url

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 13) "
            "AppleWebKit/537.36 Chrome/140 Safari/537.36"
        ),
        "Referer": "https://wapa.tv/envivo",
    }

    r = requests.get(
        PLAYER_URL,
        headers=headers,
        timeout=15
    )
    r.raise_for_status()

    # The Field59 configuration contains:
    # "m3u8":"https://live.field59.com/..."
    match = re.search(
        r'"m3u8"\s*:\s*"([^"]+\.m3u8)"',
        r.text
    )

    if not match:
        # Some versions may expose it as "url" instead.
        match = re.search(
            r'"url"\s*:\s*"([^"]+\.m3u8)"',
            r.text
        )

    if not match:
        raise RuntimeError(
            "Could not find WAPA M3U8 in Field59 response"
        )

    url = match.group(1)

    cached_url = url
    cached_at = now

    return url


@app.route("/")
def home():
    return "WAPA stream updater is running."


@app.route("/wapa.m3u8")
def wapa():

    try:
        url = get_wapa_url()

        # Redirect the IPTV player to the currently valid
        # Field59 playlist.
        return Response(
            "#EXTM3U\n"
            f"#EXTINF:-1,WAPA-TV\n"
            f"{url}\n",
            mimetype="application/x-mpegURL"
        )

    except Exception as e:
        return Response(
            "#EXTM3U\n"
            f"# WAPA updater error: {e}\n",
            status=503,
            mimetype="application/x-mpegURL"
        )


@app.route("/stream")
def stream():

    try:
        return Response(
            get_wapa_url(),
            mimetype="text/plain"
        )

    except Exception as e:
        return Response(
            str(e),
            status=503
        )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080
    )

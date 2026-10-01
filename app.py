from flask import Flask
import requests

app = Flask(__name__)

WAPA_URL = (
    "https://live.field59.com/wapa/wapa1/playlist.m3u8"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13) "
        "AppleWebKit/537.36 "
        "Chrome/140 Safari/537.36"
    ),
    "Referer": "https://wapa.tv/envivo",
}


@app.route("/")
def home():
    return "WAPA 4.1 test server is running."


@app.route("/WAPA-TV-4-1.m3u8")
def wapa():
    try:
        response = requests.get(
            WAPA_URL,
            headers=HEADERS,
            timeout=15,
            allow_redirects=False
        )

        return (
            f"URL:\n"
            f"{WAPA_URL}\n\n"
            f"HTTP status: {response.status_code}\n\n"
            f"Headers:\n"
            f"{dict(response.headers)}\n\n"
            f"Body:\n"
            f"{response.text[:2000]}"
        ), response.status_code

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

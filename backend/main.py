from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import yt_dlp
import os

app = FastAPI(title="YouTube Audio Harvester")

DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def get_playlist_info(url):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            return None

        if info.get("entries") is None:
            return {
                "title": info.get("title", "Single Song"),
                "count": 1,
                "is_playlist": False,
            }

        entries = [
            entry
            for entry in info.get("entries", [])
            if entry is not None
        ]

        return {
            "title": info.get("title", "YouTube Playlist"),
            "count": len(entries),
            "is_playlist": True,
        }

    except Exception as e:
        print(f"Could not read playlist: {e}")
        return None


def download_audio(url, amount):
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }
        ],
        "outtmpl": os.path.join(
            DOWNLOAD_DIR,
            "%(title)s.%(ext)s"
        ),
        "noplaylist": False,
        "playlistend": amount,
        "ignoreerrors": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return True

    except Exception as e:
        print(f"Download error: {e}")
        return False


@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>YouTube Audio Harvester</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #111;
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }

        .container {
            width: 90%;
            max-width: 700px;
            background: #1c1c1c;
            padding: 40px;
            border-radius: 18px;
            box-shadow: 0 0 30px rgba(0,0,0,.5);
        }

        h1 {
            text-align: center;
            margin-bottom: 10px;
        }

        .subtitle {
            text-align: center;
            color: #aaa;
            margin-bottom: 30px;
        }

        input {
            width: 100%;
            box-sizing: border-box;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #444;
            background: #111;
            color: white;
            font-size: 16px;
        }

        button {
            width: 100%;
            margin-top: 15px;
            padding: 15px;
            border: none;
            border-radius: 10px;
            background: #e62117;
            color: white;
            font-size: 17px;
            cursor: pointer;
        }

        button:hover {
            opacity: .9;
        }

        #result {
            margin-top: 25px;
            padding: 20px;
            border-radius: 10px;
            background: #252525;
            display: none;
        }

        .download {
            background: #168a45;
        }

        .error {
            color: #ff6b6b;
        }
    </style>
</head>

<body>

<div class="container">

    <h1>🎵 YouTube Audio Harvester</h1>

    <div class="subtitle">
        Download YouTube songs and playlists as MP3
    </div>

    <input
        id="url"
        type="text"
        placeholder="Paste YouTube URL here..."
    >

    <button onclick="inspect()">
        Inspect URL
    </button>

    <div id="result"></div>

</div>

<script>

async function inspect() {

    const url = document.getElementById("url").value.trim();
    const result = document.getElementById("result");

    if (!url) {
        alert("Please enter a YouTube URL.");
        return;
    }

    result.style.display = "block";
    result.innerHTML = "⏳ Inspecting YouTube URL...";

    try {

        const response = await fetch(
            "/inspect?url=" + encodeURIComponent(url)
        );

        const data = await response.json();

        if (!data.success) {
            result.innerHTML =
                '<div class="error">' +
                data.message +
                '</div>';

            return;
        }

        if (!data.is_playlist) {

            result.innerHTML = `
                <h3>${data.title}</h3>

                <p>This is a single song.</p>

                <button
                    class="download"
                    onclick="downloadSongs(1)">
                    Download Song
                </button>
            `;

        } else {

            result.innerHTML = `
                <h3>${data.title}</h3>

                <p>
                    Songs available:
                    <strong>${data.count}</strong>
                </p>

                <input
                    id="amount"
                    type="number"
                    min="1"
                    max="${data.count}"
                    value="${data.count}"
                >

                <button
                    class="download"
                    onclick="downloadSongs(
                        document.getElementById('amount').value
                    )">
                    Download Songs
                </button>
            `;
        }

    } catch (error) {

        result.innerHTML =
            '<div class="error">' +
            'Could not connect to the server.' +
            '</div>';
    }
}


async function downloadSongs(amount) {

    const url = document.getElementById("url").value.trim();
    const result = document.getElementById("result");

    result.innerHTML =
        "⏳ Downloading... Please keep this page open.";

    try {

        const response = await fetch("/download", {

            method: "POST",

            headers: {
                "Content-Type":
                    "application/x-www-form-urlencoded"
            },

            body:
                "url=" + encodeURIComponent(url) +
                "&amount=" + encodeURIComponent(amount)
        });

        const data = await response.json();

        if (data.success) {

            result.innerHTML = `
                <h3>✅ Download complete</h3>

                <p>
                    Your MP3 files have been saved in:
                </p>

                <strong>downloads</strong>
            `;

        } else {

            result.innerHTML =
                '<div class="error">' +
                data.message +
                '</div>';
        }

    } catch (error) {

        result.innerHTML =
            '<div class="error">' +
            'Download failed.' +
            '</div>';
    }
}

</script>

</body>
</html>
"""


@app.get("/inspect")
def inspect(url: str):

    info = get_playlist_info(url)

    if not info:
        return {
            "success": False,
            "message": "Unable to read this YouTube URL."
        }

    return {
        "success": True,
        "title": info["title"],
        "count": info["count"],
        "is_playlist": info["is_playlist"],
    }


@app.post("/download")
def download(url: str = Form(...), amount: int = Form(...)):

    if amount < 1:
        return {
            "success": False,
            "message": "Invalid number of songs."
        }

    success = download_audio(url, amount)

    if success:
        return {
            "success": True
        }

    return {
        "success": False,
        "message": "The download failed."
    }
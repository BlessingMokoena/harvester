from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
import yt_dlp
import os
import shutil
import tempfile
import uuid
import zipfile

app = FastAPI(title="YouTube Audio Harvester")

DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_ytdlp_base_options():
    """
    Common yt-dlp configuration for Harvester.
    Authentication is added separately depending on environment.
    """

    return {
        "format": "bestaudio/best",

        # YouTube JavaScript runtime
        "js_runtimes": {
            "deno": {}
        },

        # yt-dlp's JavaScript challenge solver
        "remote_components": ["ejs:github"],

        # YouTube PO-token provider
        "extractor_args": {
            "youtubepot-bgutilhttp": {
                "base_url": "http://127.0.0.1:4416"
            }
        },

        "quiet": False,
        "no_warnings": False,
    }


def add_authentication(ydl_opts):
    """
    Authentication strategy:

    LOCAL:
        Use the logged-in Firefox YouTube session.

    RENDER:
        Use a YouTube cookie file mounted as a Render Secret File.
    """

    render_cookie_file = "/etc/secrets/youtube_cookies.txt"
    local_cookie_file = "/tmp/youtube_cookies.txt"

    if os.path.exists(render_cookie_file):
        print("Authentication: Render cookie file")

        shutil.copyfile(render_cookie_file, local_cookie_file)

        ydl_opts["cookiefile"] = local_cookie_file

    else:
        print("Authentication: Local Firefox browser cookies")

        ydl_opts["cookiesfrombrowser"] = ("firefox",)

def get_playlist_info(url):
    """
    Inspect a YouTube URL without downloading anything.
    Uses the authenticated Firefox session locally.
    """

    ydl_opts = get_ytdlp_base_options()

    ydl_opts.update({
        "quiet": True,
        "no_warnings": False,
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True,
    })

    add_authentication(ydl_opts)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            return {
                "title": "Unknown",
                "count": 0,
                "is_playlist": False,
            }

        entries = info.get("entries")

        if entries:
            entries = [entry for entry in entries if entry]

            return {
                "title": info.get("title", "YouTube Playlist"),
                "count": len(entries),
                "is_playlist": True,
            }

        return {
            "title": info.get("title", "YouTube Video"),
            "count": 1,
            "is_playlist": False,
        }

    except Exception as e:
        print(f"Inspection error: {e}")

        return {
            "title": "Unable to inspect URL",
            "count": 0,
            "is_playlist": False,
            "error": str(e),
        }


def download_audio(url, amount, output_dir):
    """
    Download YouTube audio as MP3.
    """

    ydl_opts = get_ytdlp_base_options()

    ydl_opts.update({
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],

        "outtmpl": os.path.join(
            output_dir,
            "%(playlist_index)s - %(title)s.%(ext)s"
        ),

        "noplaylist": False,

        "ignoreerrors": False,

        "quiet": False,

        "no_warnings": False,

        "verbose": True,
    })

    add_authentication(ydl_opts)

    if amount:
        ydl_opts["playlistend"] = amount

    print("========================================")
    print("Starting yt-dlp download")
    print(f"URL: {url}")
    print(f"Amount: {amount}")
    print(f"Output: {output_dir}")
    print("========================================")

    print("========== YT-DLP CONFIG ==========")

    safe_config = dict(ydl_opts)

    # Never print authentication information
    safe_config.pop("cookiesfrombrowser", None)

    print(safe_config)

    print("===================================")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


@app.get("/", response_class=HTMLResponse)
def home():

    return """
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>YouTube Audio Harvester</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background:
        linear-gradient(
            135deg,
            #111827,
            #1e293b
        );

    color: white;

    display: flex;
    justify-content: center;
    align-items: center;

    padding: 20px;
}

.container {

    width: 100%;
    max-width: 700px;

    background: rgba(255,255,255,0.08);

    border: 1px solid
        rgba(255,255,255,0.15);

    border-radius: 20px;

    padding: 35px;

    box-shadow:
        0 20px 60px
        rgba(0,0,0,0.4);

    backdrop-filter: blur(15px);
}

h1 {
    text-align: center;
    margin-top: 0;
}

.subtitle {
    text-align: center;
    color: #cbd5e1;
    margin-bottom: 30px;
}

label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
}

input {

    width: 100%;

    padding: 14px;

    border-radius: 10px;

    border: 1px solid
        rgba(255,255,255,0.2);

    background: rgba(0,0,0,0.3);

    color: white;

    font-size: 16px;

    margin-bottom: 15px;
}

button {

    width: 100%;

    padding: 14px;

    border: none;

    border-radius: 10px;

    background: #2563eb;

    color: white;

    font-size: 16px;

    font-weight: bold;

    cursor: pointer;

    transition: 0.2s;
}

button:hover {
    background: #1d4ed8;
}

button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

#result {

    margin-top: 25px;

    padding: 20px;

    border-radius: 12px;

    background:
        rgba(0,0,0,0.25);

    display: none;
}

.status {

    margin-top: 15px;

    color: #cbd5e1;

    text-align: center;
}

.download-section {

    margin-top: 20px;
}

.download-section input {
    margin-top: 10px;
}

.success {
    color: #4ade80;
}

.error {
    color: #f87171;
}

.info {
    color: #60a5fa;
}

</style>

</head>

<body>

<div class="container">

<h1>🎵 YouTube Audio Harvester</h1>

<p class="subtitle">
Download YouTube videos as high-quality MP3 audio
</p>

<label>
YouTube URL
</label>

<input
    id="url"
    type="text"
    placeholder="Paste YouTube URL here..."
>

<button
    id="inspectButton"
    onclick="inspectURL()"
>
Inspect URL
</button>

<div id="result"></div>

</div>

<script>

let currentInfo = null;


async function inspectURL() {

    const url =
        document.getElementById("url").value.trim();

    const result =
        document.getElementById("result");

    const button =
        document.getElementById("inspectButton");


    if (!url) {

        result.style.display = "block";

        result.innerHTML =
            '<div class="error">Please enter a YouTube URL.</div>';

        return;
    }


    button.disabled = true;

    result.style.display = "block";

    result.innerHTML =
        '<div class="info">⏳ Inspecting YouTube URL...</div>';


    try {

        const response =
            await fetch(
                "/inspect?url=" +
                encodeURIComponent(url)
            );


        const data =
            await response.json();


        if (data.error) {

            throw new Error(data.error);

        }


        currentInfo = data;


        if (data.is_playlist) {

            result.innerHTML = `

                <h3>📋 Playlist detected</h3>

                <p>
                    <strong>${escapeHtml(data.title)}</strong>
                </p>

                <p>
                    Songs available:
                    <strong>${data.count}</strong>
                </p>

                <div class="download-section">

                    <label>
                        Number of songs
                    </label>

                    <input
                        id="amount"
                        type="number"
                        min="1"
                        max="${data.count}"
                        value="${data.count}"
                    >

                    <button
                        onclick="downloadSongs()"
                    >
                        ⬇️ Download Songs
                    </button>

                </div>

                <div
                    id="downloadStatus"
                    class="status"
                ></div>
            `;

        } else {

            result.innerHTML = `

                <h3>🎵 Song detected</h3>

                <p>
                    <strong>${escapeHtml(data.title)}</strong>
                </p>

                <button
                    onclick="downloadSongs()"
                >
                    ⬇️ Download Song
                </button>

                <div
                    id="downloadStatus"
                    class="status"
                ></div>
            `;
        }

    } catch (error) {

        result.innerHTML =
            '<div class="error">' +
            '❌ ' +
            escapeHtml(error.message) +
            '</div>';

    } finally {

        button.disabled = false;

    }
}


async function downloadSongs() {

    const url =
        document.getElementById("url").value.trim();


    let amount = 1;


    if (currentInfo && currentInfo.is_playlist) {

        amount =
            parseInt(
                document.getElementById("amount").value
            );


        if (
            !amount ||
            amount < 1 ||
            amount > currentInfo.count
        ) {

            alert(
                "Please enter a valid number of songs."
            );

            return;
        }
    }


    const status =
        document.getElementById("downloadStatus");


    status.className = "status info";

    status.innerHTML =
        "⏳ Preparing your download...";


    try {

        const response =
            await fetch("/download", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/x-www-form-urlencoded"
                },

                body:
                    "url=" +
                    encodeURIComponent(url) +
                    "&amount=" +
                    encodeURIComponent(amount)
            });


        if (!response.ok) {

            let message =
                "Download failed.";

            try {

                const error =
                    await response.json();

                if (error.detail) {
                    message = error.detail;
                }

            } catch (_) {}

            throw new Error(message);
        }


        const blob =
            await response.blob();


        const downloadURL =
            window.URL.createObjectURL(blob);


        const link =
            document.createElement("a");


        link.href = downloadURL;


        const disposition =
            response.headers.get(
                "Content-Disposition"
            );


        let filename =
            currentInfo &&
            currentInfo.is_playlist
                ? "harvester-download.zip"
                : "harvested-song.mp3";


        if (disposition) {

            const match =
                disposition.match(
                    /filename="?([^"]+)"?/
                );

            if (match) {
                filename = match[1];
            }
        }


        link.download = filename;


        document.body.appendChild(link);

        link.click();

        link.remove();


        window.URL.revokeObjectURL(
            downloadURL
        );


        status.className =
            "status success";

        status.innerHTML =
            "✅ Download started! Check your browser's Downloads folder.";

    } catch (error) {

        status.className =
            "status error";

        status.innerHTML =
            "❌ " +
            escapeHtml(error.message);
    }
}


function escapeHtml(text) {

    const div =
        document.createElement("div");

    div.textContent =
        text || "";

    return div.innerHTML;
}

</script>

</body>

</html>
"""


@app.get("/inspect")
def inspect(url: str):

    result = get_playlist_info(url)

    return JSONResponse(result)


@app.post("/download")
def download(
    url: str = Form(...),
    amount: int = Form(...)
):
    temp_dir = os.path.join(
        DOWNLOAD_DIR,
        str(uuid.uuid4())
    )

    os.makedirs(temp_dir, exist_ok=True)

    try:
        print(f"Starting download: {url}")
        print(f"Requested amount: {amount}")

        # Download the requested audio files
        download_audio(
            url,
            amount,
            temp_dir
        )

        # Find downloaded files
        files = []

        for root, dirs, filenames in os.walk(temp_dir):
            for filename in filenames:

                filepath = os.path.join(
                    root,
                    filename
                )

                if os.path.isfile(filepath):
                    files.append(filepath)

        if not files:
            raise Exception(
                "No audio files were downloaded."
            )

        print(f"Downloaded files: {len(files)}")

        # -------------------------------------------------
        # SINGLE SONG
        # -------------------------------------------------

        
        # -------------------------------------------------
        # MULTIPLE SONGS
        # -------------------------------------------------

        zip_name = os.path.join(
            DOWNLOAD_DIR,
            f"harvester_{uuid.uuid4().hex}.zip"
        )

        print(f"Creating ZIP: {zip_name}")

        # IMPORTANT:
        # The 'with' block completely closes/finalizes
        # the ZIP before FileResponse starts sending it.
        with zipfile.ZipFile(
            zip_name,
            mode="w",
            compression=zipfile.ZIP_DEFLATED
        ) as zip_file:

            for file_path in files:

                arcname = os.path.basename(file_path)

                print(f"Adding to ZIP: {arcname}")

                zip_file.write(
                    file_path,
                    arcname=arcname
                )

        # -------------------------------------------------
        # VERIFY ZIP BEFORE SENDING
        # -------------------------------------------------

        print("Verifying ZIP...")

        if not os.path.exists(zip_name):
            raise Exception(
                "ZIP file was not created."
            )

        zip_size = os.path.getsize(zip_name)

        print(
            f"ZIP created successfully: "
            f"{zip_size} bytes"
        )

        if zip_size == 0:
            raise Exception(
                "ZIP file is empty."
            )

        # Test the ZIP integrity
        with zipfile.ZipFile(zip_name, "r") as test_zip:

            bad_file = test_zip.testzip()

            if bad_file is not None:
                raise Exception(
                    f"ZIP verification failed. "
                    f"Corrupt file: {bad_file}"
                )

            print(
                f"ZIP verification successful. "
                f"Contains {len(test_zip.namelist())} files."
            )

        # -------------------------------------------------
        # CLEAN TEMP DOWNLOAD DIRECTORY
        # -------------------------------------------------

        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )

        print("Temporary download directory removed.")

        # -------------------------------------------------
        # RETURN ZIP
        # -------------------------------------------------

        print("Sending ZIP to browser...")

        return FileResponse(
            path=zip_name,
            media_type="application/zip",
            filename="harvester-download.zip"
        )

    except Exception as e:

        print(f"Download error: {e}")

        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )

        raise Exception(
            f"Download failed: {str(e)}"
        )


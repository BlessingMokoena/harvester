import yt_dlp
import os


def get_playlist_info(url):
    # Check the playlist/mix before downloading anything
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'skip_download': True,
        'ignoreerrors': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            return None

        # If it is a single song/video
        if info.get('entries') is None:
            return {
                'title': info.get('title', 'Single Song'),
                'count': 1,
                'is_playlist': False
            }

        # Remove unavailable/deleted songs
        entries = [
            entry for entry in info.get('entries', [])
            if entry is not None
        ]

        return {
            'title': info.get('title', 'YouTube Playlist'),
             'count': len(entries),
            'is_playlist': True
        }

    except Exception as e:
        print(f"--- Could not read the playlist: {e} ---")
        return None


def ask_how_many(total):
    while True:
        answer = input(
            f"\nHow many songs do you want to download? (1-{total} or ALL): "
        ).strip().lower()

        if answer == 'all':
            return total

        try:
            amount = int(answer)

            if 1 <= amount <= total:
                return amount

            print(f"Please enter a number between 1 and {total}.")

        except ValueError:
            print("Please enter a valid number or type ALL.")


def perform_harvest(url, amount):
    # Define the parameters of your seizure
    ydl_opts = {
        'format': 'bestaudio/best',          # Seek the highest quality audio
        'postprocessors': [{                 # The conversion ritual
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',         # Force the outcome to be MP3
        }],
        'outtmpl': 'downloads/%(title)s.%(ext)s', # Where the spoils are kept

        'noplaylist': False,                 # Do not stop at one; take the whole list

        # NEW: Only download the number of songs selected
        'playlistend': amount,

        'quiet': False,                      # Let me report the progress to you
        'no_warnings': False,

        # Continue past unavailable/private videos
        'ignoreerrors': True,
    }

    # Ensure the storage chamber exists
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\n--- Commencing the harvest of: {url} ---")
            print(f"--- Downloading {amount} song(s) ---\n")

            ydl.download([url])

            print(
                "\n--- The harvest is complete. "
                "Your spoils are in the 'downloads' folder. ---"
            )

    except Exception as e:
        print(f"--- An error occurred during the ritual: {e} ---")


if __name__ == "__main__":

    # Provide the link you wish to plunder
    target_url = input(
        "Enter the YouTube URL (Song or Playlist): "
    ).strip()

    if target_url:

        # FIRST: Find out how many songs are available
        print("\n--- Inspecting playlist/mix... Please wait ---\n")

        playlist_info = get_playlist_info(target_url)

        if playlist_info:

            print("--------------------------------------------")
            print(f"Playlist/Mix: {playlist_info['title']}")
            print(f"Songs available: {playlist_info['count']}")
            print("--------------------------------------------")

            # Single song
            if not playlist_info['is_playlist']:
                print("\nThis is a single song.")
                amount = 1

            # Playlist/Mix
            else:
                amount = ask_how_many(playlist_info['count'])

            print(f"\nYou selected: {amount} song(s)")

            confirmation = input(
                "Start downloading? (Y/N): "
            ).strip().lower()

            if confirmation == 'y':
                perform_harvest(target_url, amount)
            else:
                print("\n--- Harvest cancelled. ---")

        else:
            print(
                "\n--- Unable to determine the playlist information. "
                "Nothing was downloaded. ---"
            )

    else:
        print("You must provide a target to be harvested.")
        
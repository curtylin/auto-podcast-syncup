import os
import platform
from pathlib import Path
import feedparser
import requests

podcasts = {
  "Morning Brew Daily" : "https://feeds.megaphone.fm/MOBI8777994188",
  "THIS CAR POD! with Doug DeMuro & Friends!" : "https://feeds.megaphone.fm/TBIEA9794787572",
  "Science Vs" : "https://feeds.megaphone.fm/sciencevs",
  "The Journal." : "https://video-api.wsj.com/podcast/rss/wsj/the-journal",
  "Planet Money" : "https://feeds.npr.org/510289/podcast.xml",
  "The Indicator from Planet Money" : "https://feeds.npr.org/510325/podcast.xml"
}


# ================= Configuration =================
PODCAST_RSS_URL = podcasts["Planet Money"]
TARGET_SUBFOLDER = "Podcasts"  # Folder created on the headphones
LIMIT = 3  # Number of latest episodes to keep synced
# =================================================


def find_headphones_directory():
  system = platform.system()
  print(f"Detecting OS: {system}")

  potential_paths = []

  if system == "Windows":
    potential_paths = [
        Path(f"{letter}:/{TARGET_SUBFOLDER}") for letter in "DEFGHIJKLMNOPQRSTUVWXYZ"
    ]

  elif system == "Darwin":  # macOS
    volumes_dir = Path("/Volumes")
    if volumes_dir.exists():
      potential_paths = [
          vol / TARGET_SUBFOLDER for vol in volumes_dir.iterdir() if vol.is_dir()
      ]

  elif system == "Linux":
    try:
      username = os.getlogin()
      media_dirs = [Path(f"/media/{username}"), Path(f"/run/media/{username}")]
      for m_dir in media_dirs:
        if m_dir.exists():
          potential_paths.extend(
              [dev / TARGET_SUBFOLDER for dev in m_dir.iterdir() if dev.is_dir()]
          )
    except Exception:
      pass

  # Check if any detected headphone path actually exists
  for path in potential_paths:
    if path.parent.exists() and path.parent != Path("/"):
      path.mkdir(parents=True, exist_ok=True)
      return path

  return None


def sanitize_filename(title):
  invalid_chars = '<>:"/\\|?*'
  for char in invalid_chars:
    title = title.replace(char, "")
  return title.strip()


def sync_podcasts():
  # Try to find the headphones first
  output_dir = find_headphones_directory()

  # Fallback to a local "output" directory in the repository if not found
  if not output_dir:
    print(
        "\n[Notice] Swimming headphones drive not found."
        "\n[Test Mode] Falling back to local './output' directory for testing."
    )
    output_dir = Path("./output")
    output_dir.mkdir(parents=True, exist_ok=True)
  else:
    print(f"Found headphones storage at: {output_dir}")

  print(f"Parsing feed: {PODCAST_RSS_URL}")
  feed = feedparser.parse(PODCAST_RSS_URL)

  if not feed.entries:
    print("No entries found in the RSS feed.")
    return

  downloaded_count = 0

  for entry in feed.entries:
    if downloaded_count >= limit:
      break

    audio_url = None
    if "enclosures" in entry:
      for enclosure in entry.enclosures:
        if (
            "audio" in enclosure.get("type", "")
            or enclosure.get("href", "").endswith(".mp3")
        ):
          audio_url = enclosure.get("href")
          break

    if not audio_url:
      continue

    safe_title = sanitize_filename(entry.get("title", "episode"))
    filename = f"{safe_title}.mp3"
    filepath = output_dir / filename

    if filepath.exists():
      print(f"Already exists ({output_dir.name}): {filename}")
      downloaded_count += 1
      continue

    print(f"Downloading/Syncing: {entry.get('title')}...")
    try:
      response = requests.get(audio_url, stream=True, timeout=30)
      response.raise_for_status()

      with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
          if chunk:
            f.write(chunk)

      print(f"Successfully saved to: {filepath}")
      downloaded_count += 1

    except Exception as e:
      print(f"Failed to download {audio_url}: {e}")

  print(
      "\nProcess complete! If headphones were connected, don't forget to safely"
      " eject."
  )


if __name__ == "__main__":
  sync_podcasts()

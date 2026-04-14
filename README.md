# 🎧 SpotDL Metadata Fix

A lightweight fix for extracting metadata from Spotify and resolving tracks to YouTube Music URLs.

---

## 🚀 Features

- 🔍 Fetches track metadata from Spotify
- 🎵 Retrieves ISRC codes
- 🔗 Matches tracks with YouTube Music
- ⚡ Async-based workflow for speed

---

## 📦 Installation

```bash
pip install -r requirements.txt
```

---

## 🛠 Usage

```python
import asyncio

spdlRip = SpotdlRip()

asyncio.run(spdlRip.initialize())

url = asyncio.run(
    spdlRip.spotify_to_ytmusic(
        track_id="36FavZo5vgqTybFH09871o"
    )
)

print(url)
```

---

## 📌 Example Output

```text
2026-04-14 11:42:45,030 | INFO | [SpotdlRip] (AUTH) AccessToken: ********
2026-04-14 11:42:45,030 | INFO | [SpotdlRip] (AUTH) ClientToken: ********

2026-04-14 11:42:45,031 | INFO | [SpotdlRip] (Processing) Processing 36FavZo5vgqTybFH09871o...
2026-04-14 11:42:46,833 | INFO | Metadata received:
{
  'id': '36FavZo5vgqTybFH09871o',
  'name': 'Gyal a Whine',
  'artists': ['DJ Flash', 'A-Lectro', 'Leftside'],
  'album_name': 'Gyal a Whine',
  'duration': 135,
  'is_explicit': False
}

2026-04-14 11:42:49,381 | INFO | ISRC: QT65Z2588610

2026-04-14 11:42:51,121 | INFO | Found on YouTube Music:
https://music.youtube.com/watch?v=eCf5c7zNjgM
```

---

## 📖 How It Works

1. Authenticate with Spotify
2. Fetch track metadata
3. Extract ISRC
4. Search in YouTube Music
5. Return best match URL

---

## ⚠️ Notes

- Results depend on YouTube Music availability
- Async usage is recommended for performance
- Use at your own risk, I am not responsible for any violation of Spotify's rules, this example is for educational purposes only.

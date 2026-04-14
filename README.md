This project is a SpotDL fix for getting metadata from Spotify.

Usage:
spdlRip = SpotdlRip()
asyncio.run(spdlRip.initialize())
url = asyncio.run(spdlRip.spotify_to_ytmusic(track_id="36FavZo5vgqTybFH09871o"))
print(url)

Output:
2026-04-14 11:42:45,030 | INFO | [SpotdlRip] (AUTH) AccessToken: BQCP7h3jlHx27HnJVKaPAHIM5FJQN_aRmojg10U5GdCoY6umMhmM3T3vquSu6_DWbtWcZ2J1tgCKn045WZgG75bF8VXDggTywrBPtICw4yE-psvm6uMrd-_oNLAUwGHepjJeJYmUKIo
2026-04-14 11:42:45,030 | INFO | [SpotdlRip] (AUTH) ClientToken: AADpHR4LFdyCoWZk2taj0BSENKUJNhoqTmkJlgAMLNKQ50Q43eRp6P0gDA2iTTVTRto3Uz67KWJiaTyKhbqp0mxEKlAY36nIxsq6mvgWwSsd7RDX0YLIahGtkimoT1R6vPUPVPr1dWY6HtDoNha+r8EmYf9ehijYROdAXM5Zu+rQIZAUcplT3eznXT9QjDkcOc2tvRoU/wKKPYdnXDC+3/6mEOruKxuevYj8EyjsgQVYQ5OzsUNSyMDO3jwU1CO4WX+QAjRrVeD4Yu5mkPj0PiwW5tcnrLPSzyeRYlrB6CvsbG1pvqfoJNDEPH+weOa0lON6N25vXOYYrCwzUVsaiCA7rQRmB4s4zOA=
2026-04-14 11:42:45,031 | INFO | [SpotdlRip] (Processing) Processing 36FavZo5vgqTybFH09871o:
2026-04-14 11:42:45,031 | INFO | [SpotdlRip] (Processing) Getting metadata for 36FavZo5vgqTybFH09871o...
2026-04-14 11:42:46,833 | INFO | [SpotdlRip] (Processing) Metadata for 36FavZo5vgqTybFH09871o received: {'id': '36FavZo5vgqTybFH09871o', 'name': 'Gyal a Whine', 'artists': ['DJ Flash', 'A-Lectro', 'Leftside'], 'album_name': 'Gyal a Whine', 'duration': 135, 'is_explicit': False}
2026-04-14 11:42:46,834 | INFO | [SpotdlRip] (Processing) Searching for ISRC of 36FavZo5vgqTybFH09871o...
2026-04-14 11:42:49,381 | INFO | [SpotdlRip] (Processing) ISRC for 36FavZo5vgqTybFH09871o received: QT65Z2588610
2026-04-14 11:42:49,381 | INFO | [SpotdlRip] (Searching) Searching for 36FavZo5vgqTybFH09871o in YouTube Music...
2026-04-14 11:42:51,121 | INFO | [SpotdlRip] (Searching) 36FavZo5vgqTybFH09871o found on YouTube Music: https://music.youtube.com/watch?v=eCf5c7zNjgM
https://music.youtube.com/watch?v=eCf5c7zNjgM
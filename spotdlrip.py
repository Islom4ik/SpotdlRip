import asyncio
import base64
import json
import logging
import sys
import traceback
from functools import partial

import re
from typing import Dict, Optional

import aiohttp
import pyotp
from spotdl.providers.audio.ytmusic import YouTubeMusic
from spotdl.types.song import Song

class SpotdlRip:
    def __init__(self, logs=True):
        self.access_token = None
        self.client_token = None
        self.client_id = None
        self.device_id = None
        self.client_version = None
        self.cookies = {}
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        if logs:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s | %(levelname)s | %(message)s",
                stream=sys.stdout,
                force=True
            )

    async def initialize(self):
        await self.get_session_info()
        await self.get_access_token()
        await self.get_client_token()

        logging.info(msg=f'[SpotdlRip] (AUTH) AccessToken: {self.access_token}')
        logging.info(msg=f'[SpotdlRip] (AUTH) ClientToken: {self.client_token}')
        return True if self.access_token and self.client_token else False

    def generate_totp(self):
        secret = "GM3TMMJTGYZTQNZVGM4DINJZHA4TGOBYGMZTCMRTGEYDSMJRHE4TEOBUG4YTCMRUGQ4DQOJUGQYTAMRRGA2TCMJSHE3TCMBY"
        version = 61

        totp = pyotp.TOTP(secret)
        code = totp.now()

        return code, version

    async def get_session_info(self):
        url = "https://open.spotify.com"

        headers = {
            "User-Agent": self.user_agent
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, cookies=self.cookies) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"session initialization failed: HTTP {resp.status}")

                body = await resp.text()

                match = re.search(
                    r'<script id="appServerConfig" type="text/plain">([^<]+)</script>',
                    body
                )

                if match:
                    try:
                        decoded = base64.b64decode(match.group(1))
                        cfg = json.loads(decoded)
                        self.client_version = cfg.get("clientVersion")
                    except Exception:
                        pass

                for cookie in resp.cookies.values():
                    if cookie.key == "sp_t":
                        self.device_id = cookie.value

                    self.cookies[cookie.key] = cookie.value

    async def get_access_token(self):
        totp_code, version = self.generate_totp()

        url = "https://open.spotify.com/api/token"

        params = {
            "reason": "init",
            "productType": "web-player",
            "totp": totp_code,
            "totpVer": str(version),
            "totpServer": totp_code
        }

        headers = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/json;charset=UTF-8"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"access token request failed: HTTP {resp.status}")

                data = await resp.json()

                self.access_token = data.get("accessToken")
                self.client_id = data.get("clientId")

                for cookie in resp.cookies.values():
                    self.cookies[cookie.key] = cookie.value
                    if cookie.key == "sp_t":
                        self.device_id = cookie.value

    async def get_client_token(self):
        if not self.client_id or not self.device_id or not self.client_version:
            await self.get_session_info()
            await self.get_access_token()

        payload = {
            "client_data": {
                "client_version": self.client_version,
                "client_id": self.client_id,
                "js_sdk_data": {
                    "device_brand": "unknown",
                    "device_model": "unknown",
                    "os": "windows",
                    "os_version": "NT 10.0",
                    "device_id": self.device_id,
                    "device_type": "computer",
                },
            }
        }

        url = "https://clienttoken.spotify.com/v1/clienttoken"

        headers = {
            "Authority": "clienttoken.spotify.com",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": self.user_agent
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:

                if resp.status != 200:
                    raise RuntimeError(f"client token request failed: HTTP {resp.status}")

                data = await resp.json()

        if data.get("response_type") != "RESPONSE_GRANTED_TOKEN_RESPONSE":
            raise RuntimeError("invalid client token response")

        granted = data.get("granted_token", {})
        self.client_token = granted.get("token")

        return self.client_token

    def extract_cover_image(self, cover_data: dict) -> dict | None:
        if not cover_data:
            return None

        sources = []

        if isinstance(cover_data.get("sources"), list):
            sources = cover_data["sources"]

        else:
            square = cover_data.get("squareCoverImage", {})
            img = square.get("image", {})
            data = img.get("data", {})
            sources = data.get("sources", [])

        if not sources:
            return None

        filtered = []

        for s in sources:

            if not isinstance(s, dict):
                continue

            url = s.get("url")
            if not url:
                continue

            width = s.get("width") or s.get("maxWidth", 0)
            height = s.get("height") or s.get("maxHeight", 0)

            if (width > 64 and height > 64) or (width == 0 and height == 0 and url):
                filtered.append({
                    "url": url,
                    "width": width,
                    "height": height
                })

        if not filtered:
            return None

        filtered.sort(key=lambda x: x["width"])

        small = None
        medium = None
        fallback = None
        image_id = None

        for source in filtered:

            url = source["url"]
            width = source["width"]

            if width == 300:
                small = url
            elif width == 640:
                medium = url
            elif width == 0:
                fallback = url

            if not image_id:

                if "ab67616d0000b273" in url:
                    image_id = url.split("ab67616d0000b273")[-1]

                elif "ab67616d00001e02" in url:
                    image_id = url.split("ab67616d00001e02")[-1]

                elif "/image/" in url:

                    part = url.split("/image/")[-1].split("?")[0]

                    prefixes = [
                        "ab67616d0000b273",
                        "ab67616d00001e02",
                        "ab67616d00004851"
                    ]

                    for p in prefixes:
                        if p in part:
                            image_id = part.split(p)[-1]
                            break

        large = None

        if image_id:
            large = "https://i.scdn.co/image/ab67616d000082c1" + image_id

        result = {}

        if small:
            result["small"] = small

        if medium:
            result["medium"] = medium

        if large:
            result["large"] = large

        if not result and fallback:
            result = {
                "small": fallback,
                "medium": fallback,
                "large": fallback
            }

        return result if result else None

    def extract_artists(self, artists_data: dict) -> list[dict]:
        if type(artists_data).__name__ != 'dict': return []
        items = artists_data.get("items", [])

        artists = []

        for item in items:
            if not isinstance(item, dict):
                continue

            profile = item.get("profile", {})

            artists.append({
                "name": profile.get("name")
            })

        return artists

    def filter_track(self, data, album_fetch_data=None):
        data_map = data.get("data", {})
        track_data = data_map.get("trackUnion", {})

        if not track_data:
            return {}

        artists = self.extract_artists(track_data.get("artists", {}))

        if not artists:
            artists = []

            for item in track_data.get("firstArtist", {}).get("items", []):
                profile = item.get("profile", {})
                if profile:
                    artists.append({"name": profile.get("name")})

            for item in track_data.get("otherArtists", {}).get("items", []):
                profile = item.get("profile", {})
                if profile:
                    artists.append({"name": profile.get("name")})

        if not artists:
            album_data = track_data.get("albumOfTrack", {})
            artists = self.extract_artists(album_data.get("artists", {}))

        album_data = track_data.get("albumOfTrack", {})

        duration_ms = track_data.get("duration", {}).get("totalMilliseconds", 0)
        if duration_ms: duration_ms = duration_ms // 1000

        artist_names = [a["name"] for a in artists]

        content_rating = track_data.get("contentRating", {})
        is_explicit = content_rating.get("label") == "EXPLICIT"

        filtered = {
            "id": track_data.get("id"),
            "name": track_data.get("name"),
            "artists": artist_names,
            "album_name": album_data.get("name"),
            "duration": duration_ms,
            "is_explicit": is_explicit,
        }

        return filtered

    def filter_album(self, data):
        album_data = data.get("data", {}).get("albumUnion", {})

        if not album_data:
            return {}

        artists = self.extract_artists(album_data.get("artists", {}))
        album_artists_string = ", ".join(a["name"] for a in artists)

        cover_obj = self.extract_cover_image(album_data.get("coverArt", {}))

        cover = None
        if cover_obj:
            cover = (
                    cover_obj.get("small")
                    or cover_obj.get("medium")
                    or cover_obj.get("large")
            )

        tracks = []

        for item in album_data.get("tracksV2", {}).get("items", []):

            track = item.get("track", {})

            if not track:
                continue

            artists_data = track.get("artists", {})
            track_artists = self.extract_artists(artists_data)

            track_artist_names = [a["name"] for a in track_artists]

            duration_ms = track.get("duration", {}).get("totalMilliseconds", 0)
            if duration_ms: duration_ms = duration_ms // 1000

            track_uri = track.get("uri", "")
            track_id = track_uri.split(":")[-1] if ":" in track_uri else ""

            artist_ids = []
            for artist in artists_data.get("items", []):
                uri = artist.get("uri", "")
                if ":" in uri:
                    artist_ids.append(uri.split(":")[-1])

            disc_number = track.get("discNumber", 1) or 1

            is_explicit = track.get("contentRating", {}).get("label") == "EXPLICIT"

            tracks.append({
                "id": track_id,
                "name": track.get("name"),
                "artists": ", ".join(track_artist_names),
                "artistIds": artist_ids,
                "duration": duration_ms,
                "plays": track.get("playcount"),
                "is_explicit": is_explicit,
                "disc_number": disc_number
            })

        release_date = album_data.get("date", {}).get("isoString")

        if release_date and "T" in release_date:
            release_date = release_date.split("T")[0]

        album_uri = album_data.get("uri", "")
        album_id = album_uri.split(":")[-1] if ":" in album_uri else ""

        total_discs = album_data.get("discs", {}).get("totalCount", 1)

        return {
            "id": album_id,
            "name": album_data.get("name"),
            "artists": album_artists_string,
            "cover": cover,
            "releaseDate": release_date,
            "count": len(tracks),
            "tracks": tracks,
            "discs": {
                "totalCount": total_discs
            },
            "label": album_data.get("label")
        }

    async def get_album_info(self, album_id: str):
        url = "https://api-partner.spotify.com/pathfinder/v1/query"

        headers = {
            "User-Agent": self.user_agent,
            "Authorization": f"Bearer {self.access_token}",
            "client-token": self.client_token,
            "origin": "https://open.spotify.com",
            "referer": "https://open.spotify.com",
            "content-type": "application/json"
        }

        all_items = []
        offset = 0
        limit = 1000
        total_count = None
        data = None

        async with aiohttp.ClientSession() as session:

            while True:

                payload = {
                    "variables": {
                        "uri": f"spotify:album:{album_id}",
                        "locale": "",
                        "offset": offset,
                        "limit": limit
                    },
                    "operationName": "getAlbum",
                    "extensions": {
                        "persistedQuery": {
                            "version": 1,
                            "sha256Hash": "b9bfabef66ed756e5e13f68a942deb60bd4125ec1f1be8cc42769dc0259b4b10"
                        }
                    }
                }

                async with session.post(url, headers=headers, json=payload) as resp:
                    response = await resp.json()

                if data is None:
                    data = response

                album_data = response.get("data", {}).get("albumUnion", {})
                tracks_data = album_data.get("tracksV2", {})
                items = tracks_data.get("items", [])

                if not items:
                    break

                all_items.extend(items)

                if total_count is None:
                    total_count = tracks_data.get("totalCount", len(items))

                if len(all_items) >= total_count or len(items) < limit:
                    break

                offset += limit

        if data and all_items:
            album_union = data.setdefault("data", {}).setdefault("albumUnion", {})
            tracks_v2 = album_union.setdefault("tracksV2", {})

            tracks_v2["items"] = all_items
            tracks_v2["totalCount"] = len(all_items)

        filtered_data = self.filter_album(data)

        json_data = json.dumps(filtered_data)
        result = json.loads(json_data)

        return result

    async def get_track_info(self, track_id:str):
        url = "https://api-partner.spotify.com/pathfinder/v1/query"

        headers = {
            "User-Agent": self.user_agent,
            "Authorization": f"Bearer {self.access_token}",
            "client-token": self.client_token,
            "origin": "https://open.spotify.com",
            "referer": "https://open.spotify.com",
            "content-type": "application/json"
        }

        payload = {
            "variables": {
                "uri": f"spotify:track:{track_id}"
            },
            "operationName": "getTrack",
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "612585ae06ba435ad26369870deaae23b5c8800a256cd8a57e08eddc25a37294"
                }
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()

        album_fetch_data = None
        try:
            track_union = data["data"]["trackUnion"]
            album_of_track = track_union["albumOfTrack"]

            album_id = ""

            if album_of_track.get("id"):
                album_id = album_of_track["id"]

            elif album_of_track.get("uri"):
                uri = album_of_track["uri"]
                if ":" in uri:
                    album_id = uri.split(":")[-1]

            if album_id:

                album_response = await self.get_album_info(album_id=album_id)

                if album_response:

                    tracks_items = []

                    if album_response.get("tracks"):
                        for t in album_response["tracks"]:
                            tracks_items.append({
                                "track": {
                                    "discNumber": t.get("disc_number"),
                                    "id": t.get("id"),
                                    "uri": f"spotify:track:{t.get('id')}"
                                }
                            })

                    album_fetch_data = {
                        "data": {
                            "albumUnion": {
                                "discs": {
                                    "totalCount": album_response["discs"]["totalCount"]
                                },
                                "tracks": {
                                    "items": tracks_items,
                                    "totalCount": album_response["count"]
                                },
                                "artists": album_response["artists"],
                                "label": album_response["label"]
                            }
                        }
                    }

        except Exception:
            pass

        filtered_data = self.filter_track(data, album_fetch_data)

        json_data = json.dumps(filtered_data)

        result = json.loads(json_data)

        return result

    async def get_track_isrc(self, track_id:str):
        try:
            headers = {
                'accept': '*/*',
                'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'priority': 'u=1, i',
                'referer': 'https://phpstack-822472-6184058.cloudwaysapps.com/?',
                'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-storage-access': 'active',
                'user-agent': self.user_agent,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url="https://phpstack-822472-6184058.cloudwaysapps.com/api/spotify.php", params={"q": f"https://open.spotify.com/track/{track_id}"}, headers=headers) as response:
                    data = await response.json()
                    return data.get('isrc')
        except:
            traceback.print_exc()
            return None

    def spotify_metadata_to_ytmusic_url(self, spotify_meta: Dict, only_verified: Optional[bool] = None, search_query: Optional[str] = None) -> Optional[str]:
        name = spotify_meta.get("name")
        artists = spotify_meta.get("artists")

        if not name:
            raise ValueError("spotify_meta['name'] is required")

        if not artists or not isinstance(artists, (list, tuple)):
            raise ValueError("spotify_meta['artists'] must be a non-empty list or tuple")

        song = Song.from_missing_data(
            name=name,
            artists=list(artists),
            artist=spotify_meta.get("artist") or artists[0],
            album_name=spotify_meta.get("album_name"),
            duration=spotify_meta.get("duration"),
            explicit=spotify_meta.get("explicit"),
            isrc=spotify_meta.get("isrc"),
            song_id=spotify_meta.get("song_id"),
        )

        provider = YouTubeMusic(search_query=search_query)

        if only_verified is None:
            only_verified = bool(spotify_meta.get("isrc"))

        return provider.search(song, only_verified=only_verified)

    async def spotify_to_ytmusic(self, track_id:str, only_verified:bool=True):
        logging.info(msg=f'[SpotdlRip] (Processing) Processing {track_id}:')
        logging.info(msg=f'[SpotdlRip] (Processing) Getting metadata for {track_id}...')
        track_info = await self.get_track_info(track_id=track_id)
        logging.info(msg=f'[SpotdlRip] (Processing) Metadata for {track_id} received: {track_info}')
        logging.info(msg=f'[SpotdlRip] (Processing) Searching for ISRC of {track_id}...')
        track_isrc = await self.get_track_isrc(track_id=track_id)
        logging.info(msg=f'[SpotdlRip] (Processing) ISRC for {track_id} received: {track_isrc}')
        logging.info(msg=f'[SpotdlRip] (Searching) Searching for {track_id} in YouTube Music...')
        result = await asyncio.get_running_loop().run_in_executor(None, partial(self.spotify_metadata_to_ytmusic_url, spotify_meta={"name": track_info['name'], "artists": track_info['artists'], "album_name": track_info['album_name'], "duration": track_info.get('duration', 0), "explicit": track_info.get('is_explicit', False), "isrc": track_isrc, "song_id": track_id}, only_verified=only_verified))
        if result:
            logging.info(msg=f'[SpotdlRip] (Searching) {track_id} found on YouTube Music: {result}')
            return result
        else:
            logging.info(msg=f'[SpotdlRip] (Searching) {track_id} Not Found! Try again later or use it again with only_verified=False')
            return None

if __name__ == '__main__':
    spdlRip = SpotdlRip()
    asyncio.run(spdlRip.initialize())
    url = asyncio.run(spdlRip.spotify_to_ytmusic(track_id="36FavZo5vgqTybFH09871o"))
    print(url)
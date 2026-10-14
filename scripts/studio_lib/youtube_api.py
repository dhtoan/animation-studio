"""Minimal YouTube Data API v3 + YouTube Analytics API v2 client (stdlib only).

Credentials are read from the environment only and never written to disk by this
module:
  YT_API_KEY             Data API key (public data: search, videos, channels, comments)
  YT_ANALYTICS_TOKEN     OAuth 2.0 access token with yt-analytics.readonly
                         (+ yt-analytics-monetary.readonly for revenue) for the
                         authenticated channel. Obtain it with your own OAuth client;
                         this tool deliberately ships no client secret.

Design ported (re-implemented, with fixes) from nikhilbhansali/youtube-data-skills
(MIT): quota accounting, batching by 50, date window ending 3 days ago,
`estimatedRevenue / views * 1000` as RPM. Fixes: region/language targeting,
median-baseline outliers, Shorts at <= 180 s, unknown stays None.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import statistics
import urllib.error
import urllib.parse
import urllib.request

DATA = "https://www.googleapis.com/youtube/v3/"
ANALYTICS = "https://youtubeanalytics.googleapis.com/v2/reports"
COST = {"search": 100, "videos": 1, "channels": 1, "playlistItems": 1, "commentThreads": 1}


class QuotaExceeded(RuntimeError):
    pass


class DataAPI:
    def __init__(self, key: str | None = None, budget: int = 8000, opener=None):
        self.key = key or os.environ.get("YT_API_KEY")
        if not self.key:
            raise RuntimeError("YT_API_KEY not set (Data API key needed for live collection)")
        self.budget = budget
        self.used = 0
        self._open = opener or (lambda url: urllib.request.urlopen(url, timeout=30).read())

    def _get(self, endpoint: str, **params) -> dict:
        cost = COST[endpoint]
        if self.used + cost > self.budget:
            raise QuotaExceeded(f"quota budget {self.budget} would be exceeded ({self.used}+{cost})")
        params = {k: v for k, v in params.items() if v is not None}
        params["key"] = self.key
        url = DATA + endpoint + "?" + urllib.parse.urlencode(params)
        self.used += cost
        try:
            return json.loads(self._open(url))
        except urllib.error.HTTPError as e:  # never echo the key
            raise RuntimeError(f"YouTube Data API {endpoint} HTTP {e.code}") from None

    def search(self, q: str, published_after: str, order: str = "viewCount", duration: str | None = "long",
               max_results: int = 50) -> list[dict]:
        r = self._get("search", part="snippet", type="video", q=q, order=order, maxResults=max_results,
                      publishedAfter=published_after, regionCode="US", relevanceLanguage="en",
                      videoDuration=duration)
        return [{"id": it["id"]["videoId"], "title": it["snippet"]["title"], "channelId": it["snippet"]["channelId"],
                 "channel": it["snippet"]["channelTitle"], "published": it["snippet"]["publishedAt"]}
                for it in r.get("items", []) if it.get("id", {}).get("videoId")]

    def videos(self, ids: list[str]) -> dict[str, dict]:
        out = {}
        for i in range(0, len(ids), 50):
            r = self._get("videos", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]))
            for it in r.get("items", []):
                st = it.get("statistics", {})
                out[it["id"]] = {
                    "views": int(st["viewCount"]) if "viewCount" in st else None,
                    "likes": int(st["likeCount"]) if "likeCount" in st else None,
                    "comments": int(st["commentCount"]) if "commentCount" in st else None,
                    "duration_s": iso_duration(it["contentDetails"]["duration"]),
                    "published": it["snippet"]["publishedAt"], "title": it["snippet"]["title"],
                    "channelId": it["snippet"]["channelId"]}
        return out

    def channels(self, ids: list[str]) -> dict[str, dict]:
        out = {}
        for i in range(0, len(ids), 50):
            r = self._get("channels", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]))
            for it in r.get("items", []):
                st = it.get("statistics", {})
                out[it["id"]] = {"title": it["snippet"]["title"],
                                 "subscribers": None if st.get("hiddenSubscriberCount") else int(st.get("subscriberCount", 0)),
                                 "videos": int(st.get("videoCount", 0)),
                                 "uploads": it["contentDetails"]["relatedPlaylists"]["uploads"]}
        return out

    def recent_uploads(self, playlist: str, n: int = 20) -> list[str]:
        r = self._get("playlistItems", part="contentDetails", playlistId=playlist, maxResults=min(50, n))
        return [it["contentDetails"]["videoId"] for it in r.get("items", [])]

    def comments(self, video_id: str, n: int = 100) -> list[str]:
        r = self._get("commentThreads", part="snippet", videoId=video_id, maxResults=min(100, n), order="relevance",
                      textFormat="plainText")
        return [it["snippet"]["topLevelComment"]["snippet"]["textOriginal"] for it in r.get("items", [])]


def iso_duration(s: str) -> int | None:
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    if not m:
        return None
    d, h, mi, se = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + se


def is_short(duration_s: int | None) -> bool | None:
    """Shorts can be up to 3 minutes; duration alone cannot prove a vertical Short."""
    if duration_s is None:
        return None
    return duration_s <= 180


def outlier_ratio(views: int | None, channel_recent_views: list[int]) -> float | None:
    """Median-baseline outlier (youtuber-skills method): views / median(channel's recent uploads)."""
    base = [v for v in channel_recent_views if v is not None]
    if views is None or len(base) < 5:
        return None
    med = statistics.median(base)
    return round(views / med, 2) if med > 0 else None


def rpm(estimated_revenue: float | None, views: int | None) -> float | None:
    if estimated_revenue is None or not views:
        return None
    return round(estimated_revenue / views * 1000, 2)


def analytics_window(days: int = 28, lag: int = 3, today: dt.date | None = None) -> tuple[str, str]:
    end = (today or dt.date.today()) - dt.timedelta(days=lag)
    start = end - dt.timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


class AnalyticsAPI:
    """Read-only owned-channel analytics. Disabled unless YT_ANALYTICS_TOKEN is provided."""

    QUERIES = {
        "overview": {"metrics": "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained",
                     "dimensions": "day"},
        "top_videos": {"metrics": "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage",
                       "dimensions": "video", "sort": "-estimatedMinutesWatched", "maxResults": 50},
        "demographics": {"metrics": "viewerPercentage", "dimensions": "ageGroup,gender"},
        "demographics_us": {"metrics": "viewerPercentage", "dimensions": "ageGroup,gender", "filters": "country==US"},
        "geography": {"metrics": "views,estimatedMinutesWatched,averageViewDuration", "dimensions": "country",
                      "sort": "-views", "maxResults": 25},
        "traffic": {"metrics": "views,estimatedMinutesWatched", "dimensions": "insightTrafficSourceType", "sort": "-views"},
        "devices": {"metrics": "views,estimatedMinutesWatched", "dimensions": "deviceType", "sort": "-views"},
        "revenue": {"metrics": "views,estimatedRevenue,estimatedAdRevenue,playbackBasedCpm", "dimensions": "day"},
    }

    def __init__(self, token: str | None = None, opener=None):
        self.token = token or os.environ.get("YT_ANALYTICS_TOKEN")
        if not self.token:
            raise RuntimeError("YT_ANALYTICS_TOKEN not set — owned-channel analytics disabled")
        self._open = opener

    def report(self, name: str, start: str, end: str, **extra) -> dict:
        q = dict(self.QUERIES[name])
        q.update(extra)
        q.update({"ids": "channel==MINE", "startDate": start, "endDate": end})
        url = ANALYTICS + "?" + urllib.parse.urlencode(q)
        if self._open:
            return json.loads(self._open(url))
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.token}"})
        try:
            return json.loads(urllib.request.urlopen(req, timeout=30).read())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"YouTube Analytics {name} HTTP {e.code}") from None

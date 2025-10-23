"""
Copyright (C) 2024-2025 Johannes Habel

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
import json
import logging
import traceback


from bs4 import BeautifulSoup
from functools import cached_property
from typing import Union, Optional, List, Dict
from base_api.modules.config import RuntimeConfig
from base_api.modules.progress_bars import Callback
from base_api.base import BaseCore, setup_logger, Helper

try:
    from modules.consts import *
    from modules.errors import *

except (ModuleNotFoundError, ImportError):
    from .modules.consts import *
    from .modules.errors import *


def _normalize_quality_value(q) -> Union[str, int]:
    if isinstance(q, int):
        return q
    s = str(q).lower().strip()
    if s in {"best", "half", "worst"}:
        return s
    m = re.search(r'(\d{3,4})', s)
    if m:
        return int(m.group(1))
    raise ValueError(f"Invalid quality: {q}")


def _choose_quality_from_list(available: List[str | int], target: Union[str, int]):
    # available like ["240", "360", "480", "720", "1080"]
    av = sorted({int(x) for x in available})
    if isinstance(target, str):
        if target == "best":
            return av[-1]
        if target == "worst":
            return av[0]
        if target == "half":
            return av[len(av) // 2]
        raise ValueError("Invalid label.")
    # numeric: highest ≤ target, else closest
    le = [h for h in av if h <= target]
    if le:
        return le[-1]
    # fallback closest (ties -> higher)
    return min(av, key=lambda h: (abs(h - target), -h))


class Video:
    def __init__(self, url, core: Optional[BaseCore] = None):
        """
        :param url: (str) The URL of the video
        """
        self.core = core
        self.url = url
        self.logger = setup_logger(name="FULLHDPORN API - [Video]", log_file=None, level=logging.ERROR)
        self.html_content = self.core.fetch(self.url)
        self.soup = BeautifulSoup(self.html_content, "lxml")

    def enable_logging(self, log_file: str = None, level = None, log_ip: str = None, log_port: int = None):
        self.logger = setup_logger(name="FULLHDPORN API - [Video]", log_file=log_file, level=level, http_ip=log_ip, http_port=log_port)

    def _meta(self, *, name: str = None, prop: str = None) -> Optional[str]:
        """Return the 'content' of a <meta ...> by name= or property=."""
        if name:
            tag = self.soup.find("meta", attrs={"name": name})
        elif prop:
            tag = self.soup.find("meta", attrs={"property": prop})
        else:
            tag = None
        return tag.get("content") if tag and tag.has_attr("content") else None

    def _meta_all(self, *, name: str = None, prop: str = None) -> List[str]:
        """Return all matching 'content' values for repeated metas."""
        if name:
            tags = self.soup.find_all("meta", attrs={"name": name})
        elif prop:
            tags = self.soup.find_all("meta", attrs={"property": prop})
        else:
            tags = []
        out = []
        for t in tags:
            if t.has_attr("content"):
                out.append(t["content"])
        return out

    @cached_property
    def title(self) -> Optional[str]:
        return self._meta(prop="og:title")

    @cached_property
    def description(self) -> Optional[str]:
        return self._meta(name="description")

    @cached_property
    def rating(self) -> List[str]:
        "This is NOT the rating of the video e.g., likes or dislikes!"
        return self._meta_all(name="rating")

    @cached_property
    def thumbnail(self) -> Optional[str]:
        return self._meta(prop="og:image")

    @cached_property
    def duration(self) -> Optional[int]:
        v = self._meta(prop="video:duration")
        try:
            return int(v) if v is not None else None
        except ValueError:
            return None

    @cached_property
    def tags(self) -> List[str]:
        # meta property="video:tag" can appear multiple times; here it's empty once
        tags = self._meta_all(prop="video:tag")
        # Normalize: split on commas if any combined values appear, strip empties
        out: List[str] = []
        for t in tags:
            if t is None:
                continue
            parts = [p.strip() for p in t.split(",")]
            out.extend([p for p in parts if p])
        return out

    @cached_property
    def video_id(self) -> Optional[str]:
        return self._meta(prop="ya:ovs:id")

    @cached_property
    def publish_date(self) -> Optional[str]:
        # ISO timestamp string
        return self._meta(prop="ya:ovs:upload_date")

    @cached_property
    def video_status(self) -> Optional[str]:
        return self._meta(prop="ya:ovs:status")

    @cached_property
    def total_views(self) -> Optional[int]:
        v = self._meta(prop="ya:ovs:views_total")
        try:
            return int(v) if v is not None else None
        except ValueError:
            return None

    @cached_property
    def embed_url(self) -> Optional[str]:
        """
        Extracts the embed URL used by getEmbed(...) (e.g., https://www.fullhdporn.sex/embed/16512).
        """
        # easiest: look for an og:video first, else parse getEmbed code
        ogv = self._meta(prop="og:video")
        if ogv:
            return ogv
        # fallback: scan inline scripts for "src='https://.../embed/ID'"
        for s in self.soup.find_all("script"):
            txt = s.string or s.get_text() or ""
            m = re.search(r"""["']https?://[^"']+/embed/\d+["']""", txt)
            if m:
                return m.group(0).strip('"\'')
        return None

    def _parse_flashvars(self) -> Dict[str, str]:
        """
        Parse the inline JS object 'flashvars' into a Python dict by:
          1) Extracting the {...} body
          2) Quoting bare keys
          3) Converting single quotes to double quotes
          4) Removing trailing commas
          5) json.loads(...)
        Returns {} if not found or parse fails.
        """
        for s in self.soup.find_all("script"):
            txt = s.string or s.get_text() or ""
            m = FLASHVARS_BLOCK.search(txt)
            if not m:
                continue

            body = m.group("body")

            # Step 1: quote bare keys (video_url: '...') -> "video_url": '...'
            body_qkeys = re.sub(
                r'(?m)(^|\s|,)([A-Za-z_$][\w$]*)\s*:',
                lambda mm: f'{mm.group(1)}"{mm.group(2)}":',
                body
            )

            # Step 2: convert single-quoted strings to double-quoted strings.
            # We only flip quotes around JS string literals, not around already-quoted keys.
            # This regex finds '...'(no embedded unescaped ') and replaces with "..."
            body_dquotes = re.sub(
                r"'([^'\\]*(?:\\.[^'\\]*)*)'",
                lambda mm: '"' + mm.group(1).replace('"', '\\"') + '"',
                body_qkeys
            )

            # Step 3: remove trailing commas before } or end (JSON doesn’t allow them)
            body_trim_trailing_commas = re.sub(
                r",\s*(\}|$)",
                r"\1",
                body_dquotes
            )

            # Step 4: build valid JSON object text
            json_text = "{" + body_trim_trailing_commas.strip() + "}"

            try:
                data = json.loads(json_text)
                # Ensure all values are strings for consistency with earlier code
                return {str(k): str(v) for k, v in data.items()}
            except Exception:
                # If anything goes wrong, fall back to a minimal regex extractor as a last resort
                pass

            # --- LAST-RESORT extractor: tolerant key/value pairs (bare or quoted keys) ---
            # Handles: key: 'value' | "value" | number
            kv_re = re.compile(
                r'(?m)^\s*(?P<key>"[^"]+"|\'[^\']+\'|[A-Za-z_$][\w$]*)\s*:\s*(?P<val>"[^"]*"|\'[^\']*\'|-?\d+(?:\.\d+)?)\s*,?\s*$'
            )
            out: Dict[str, str] = {}
            for line in body.splitlines():
                m2 = kv_re.search(line)
                if not m2:
                    continue
                k = m2.group("key").strip().strip('"\'')

                v = m2.group("val").strip()
                if v.startswith(("'", '"')) and v.endswith(("'", '"')):
                    v = v[1:-1]
                out[k] = v
            if out:
                return out

        return {}

    @cached_property
    def flashvars(self) -> Dict[str, str]:
        """Parsed `flashvars` as a flat dict of strings."""
        return self._parse_flashvars()

    @cached_property
    def categories(self) -> List[str]:
        cats = self.flashvars.get("video_categories", "") or ""
        return [c.strip() for c in cats.split(",") if c.strip()]

    @cached_property
    def preview_url(self) -> Optional[str]:
        """Poster/preview image from flashvars."""
        return self.flashvars.get("preview_url")

    @cached_property
    def mp4_variants(self) -> Dict[int, str]:
        """
        Map of {height: url} from the flashvars:
          - video_url (360p)
          - video_alt_url (480p)
          - video_alt_url2 (720p)
          - video_alt_url3 (1080p)
        Any present entries are included; heights parsed from the URL.
        """
        keys = ["video_url", "video_alt_url", "video_alt_url2", "video_alt_url3"]
        out: Dict[int, str] = {}
        for k in keys:
            u = self.flashvars.get(k)
            if not u:
                continue
            m = RES_FROM_URL.search(u)
            if not m:
                continue
            try:
                h = int(m.group(1))
            except ValueError:
                continue
            out[h] = u
        return dict(sorted(out.items(), key=lambda kv: kv[0]))

    def video_qualities(self) -> List[str]:
        """
        :return: list of available heights as strings (e.g. ["360", "480", "720", "1080"])
        """
        qualities = [str(h) for h in sorted(self.mp4_variants.keys())]
        return qualities

    def direct_download_urls(self) -> List[str]:
        """
        :return: list of direct MP4 URLs (ascending by height).
        """
        return [self.mp4_variants[h] for h in sorted(self.mp4_variants.keys())]

    def download(self, quality, path: str = "./", callback=Callback.text_progress_bar, no_title: bool = False):
        """
        Uses your existing quality helpers + legacy_download.
        Assumes:
          - _normalize_quality_value and _choose_quality_from_list are available in scope
          - self.core.legacy_download is available
        """
        cdn_urls = self.direct_download_urls()
        quals = self.video_qualities()  # e.g., ["360", "480", "720"]
        if not quals or not cdn_urls:
            raise NotAvailable(f"The chosen quality is not available")  # or return False, depending on your project

        qn = _normalize_quality_value(quality)  # from your package
        chosen_height = _choose_quality_from_list(  # from your package
            [int(q) for q in quals], qn
        )

        # Build a height->url map for easier selection
        height_map = {int(h): url for h, url in self.mp4_variants.items()}
        download_url = height_map.get(int(chosen_height))
        if not download_url:
            # fallback: closest available by absolute diff (ties -> higher)
            available = sorted(height_map.keys())
            fallback = min(available, key=lambda h: (abs(h - int(chosen_height)), -h))
            download_url = height_map[fallback]

        # build output path
        if not no_title:
            safe_title = self.title.strip()
            fname = f"{safe_title}.mp4"
            path = os.path.join(path, fname)

        try:
            self.core.legacy_download(url=download_url, path=path, callback=callback)  # your existing method
            return True

        except Exception:
            error = traceback.format_exc()
            self.logger.error(error)
            return False

class Client(Helper):
    def __init__(self, core: Optional[BaseCore] = None):
        super().__init__(core, video=Video)
        self.core = core or BaseCore(config=RuntimeConfig())
        self.core.initialize_session()
        self.logger = setup_logger(name="FULLHDPORN API - [Client]", log_file=None, level=logging.ERROR)

    def enable_logging(self, log_file: str = None, level=None, log_ip: str = None, log_port: int = None):
        self.logger = setup_logger(name="FULLHDPORN API - [Client]", log_file=log_file, level=level, http_ip=log_ip, http_port=log_port)

    def get_video(self, url: str) -> Video:
        """
        :param url: (str) The video URL
        :return: (Video) The video object
        """
        return Video(url, core=self.core)


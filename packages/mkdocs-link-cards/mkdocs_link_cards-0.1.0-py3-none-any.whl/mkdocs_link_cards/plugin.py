from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

import extruct
import requests
from bs4 import BeautifulSoup
from mkdocs.config import config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from w3lib.html import get_base_url

CARD_TOKEN = re.compile(
    r'\[\[card\s+(?P<url>\S+)(?:\s+title="(?P<title>.*?)")?\s*\]\]', re.IGNORECASE
)

# Minimal inline CSS injected once per page that uses cards.
INLINE_CSS = """
<style>
.md-typeset .linkcard-img{
  width:100%; height:160px; object-fit:cover; border-radius:8px; margin:0 0 .5rem;
}
</style>
"""

# Tiny monochrome SVG icons (data URIs) used as fallbacks for providers.
DATA_URI_ARXIV = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='320' height='180'>"
    "<rect width='100%' height='100%' fill='#1f2937'/>"
    "<text x='50%' y='55%' dominant-baseline='middle' text-anchor='middle' "
    "font-family='Arial,Helvetica,sans-serif' font-size='48' fill='#ffffff'>arXiv</text>"
    "</svg>"
)
DATA_URI_X = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='320' height='180'>"
    "<rect width='100%' height='100%' fill='#111111'/>"
    "<text x='50%' y='55%' dominant-baseline='middle' text-anchor='middle' "
    "font-family='Arial,Helvetica,sans-serif' font-size='64' fill='#ffffff'>X</text>"
    "</svg>"
)
DATA_URI_YT = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='320' height='180'>"
    "<rect width='100%' height='100%' fill='#cc0000'/>"
    "<polygon points='135,120 135,60 195,90' fill='#ffffff'/>"
    "</svg>"
)


@dataclass(frozen=True)
class CardData:
    """Resolved card information ready to render."""

    url: str
    title: str
    description: str
    image: Optional[str]
    site: str


class LinkCardsPlugin(BasePlugin):
    """
    MkDocs plugin that turns `[[card URL title="..."]]` tokens into Material-style cards.

    Configuration (mkdocs.yml):
      plugins:
        - link-cards:
            ttl: 604800
            timeout: 8
            allow_domains: []
            deny_domains: []
    """

    config_scheme = (
        ("cache_dir", config_options.Type(str, default=".cache/linkcards")),
        ("ttl", config_options.Type(int, default=7 * 24 * 3600)),
        ("timeout", config_options.Type(int, default=8)),
        (
            "allow_domains",
            config_options.ListOfItems(config_options.Type(str), default=[]),
        ),
        (
            "deny_domains",
            config_options.ListOfItems(config_options.Type(str), default=[]),
        ),
        ("inject_css", config_options.Type(bool, default=True)),
    )

    # --- MkDocs hooks -----------------------------------------------------

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
        # Compute project root for relative cache path.
        self._project_root = os.path.dirname(config.config_file_path or os.getcwd())
        self._css_injected_pages: set[str] = set()
        return config

    def on_page_markdown(
        self,
        markdown: str,
        page: Any,
        config: MkDocsConfig,
        files: Any,
    ) -> str:
        """Replace card tokens with rendered cards; inject CSS once per page."""

        saw_card = False

        def repl(m: re.Match[str]) -> str:
            nonlocal saw_card
            saw_card = True
            url = m.group("url")
            title_override = m.group("title")
            if not self._allowed(url):
                return f"[{url}]({url})"

            data = self._resolve(url)
            title = title_override or data.title or url
            desc = data.description or ""
            img = (
                f'![{_escape_md(title)}]({data.image}){{ .linkcard-img }}\n'
                if data.image
                else ""
            )
            button = (
                f'[:octicons-link-external-16: Open]({data.url}){{ .md-button }}'
            )
            md_block = (
                f'<div class="grid cards" markdown>\n'
                f'-   {img}**{_escape_md(title)}**  \n'
                f'    <small>{_escape_md(data.site)}</small>  \n'
                f'    ---\n'
                f'    {desc}\n\n'
                f'    {button}\n'
                f'</div>'
            )
            return md_block

        out = CARD_TOKEN.sub(repl, markdown)

        if saw_card and self.config.get("inject_css", True):
            # Only inject once per page.
            if getattr(page, "file", None):
                page_id = getattr(page.file, "src_uri", page.title or "page")
            else:
                page_id = page.title or "page"
            if page_id not in self._css_injected_pages:
                self._css_injected_pages.add(page_id)
                out = INLINE_CSS + "\n" + out

        return out

    # --- Helpers ----------------------------------------------------------

    def _allowed(self, url: str) -> bool:
        host = urlparse(url).netloc.lower()
        allow = self.config.get("allow_domains") or []
        deny = self.config.get("deny_domains") or []
        if allow and not any(host.endswith(x) for x in allow):
            return False
        if any(host.endswith(x) for x in deny):
            return False
        return True

    def _cache_path(self, url: str) -> str:
        base = self.config.get("cache_dir") or ".cache/linkcards"
        if not os.path.isabs(base):
            base = os.path.join(self._project_root, base)
        os.makedirs(base, exist_ok=True)
        h = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return os.path.join(base, f"{h}.json")

    def _resolve(self, url: str) -> CardData:
        """Return cached or freshly-resolved card data for a URL."""
        cpath = self._cache_path(url)
        if os.path.exists(cpath):
            age = time.time() - os.path.getmtime(cpath)
            if age < int(self.config["ttl"]):
                try:
                    with open(cpath, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    return CardData(**data)
                except Exception:
                    pass  # corrupted cache → continue

        host = urlparse(url).netloc.lower()
        try:
            if "youtube.com" in host or "youtu.be" in host:
                data = self._youtube(url)
            elif "arxiv.org" in host:
                data = self._arxiv(url)
            elif "twitter.com" in host or "x.com" in host:
                data = self._x(url)
            else:
                data = self._generic(url)
        except Exception:
            # Never break the build because of a bad URL.
            data = CardData(url=url, title=url, description="", image=None, site=host)

        with open(cpath, "w", encoding="utf-8") as f:
            json.dump(data.__dict__, f)
        return data

    # --- Provider resolvers ----------------------------------------------

    def _generic(self, url: str) -> CardData:
        """Extract OpenGraph/Twitter/JSON-LD metadata, with fallbacks."""
        resp = requests.get(url, headers=_ua(), timeout=int(self.config["timeout"]))
        html, final_url = resp.text, resp.url
        base_url = get_base_url(html, final_url)
        try:
            meta = extruct.extract(
                html,
                base_url=base_url,
                syntaxes=["opengraph", "json-ld", "microdata", "rdfa"],
            )
        except ValueError:
            meta = {}
        og_props = _first_og(meta.get("opengraph") or [])
        soup = BeautifulSoup(html, "lxml")
        title = _first(
            og_props.get("og:title"),
            _meta(soup, ["twitter:title"]),
            soup.title.string if soup.title else "",
            final_url,
            default=final_url,
        )
        desc = _first(
            og_props.get("og:description"),
            _meta(soup, ["twitter:description", "description"]),
            default="",
        )
        image = _first(
            og_props.get("og:image"),
            _meta(soup, ["twitter:image", "twitter:image:src"]),
            default=None,
        )
        site = _first(
            og_props.get("og:site_name"),
            _meta(soup, ["og:site_name", "application-name"]),
            default=urlparse(final_url).netloc,
        )
        return CardData(
            url=final_url, title=title, description=desc, image=image, site=site
        )

    def _youtube(self, url: str) -> CardData:
        """Use YouTube oEmbed for title/author, plus deterministic thumbnail."""
        u = urlparse(url)
        vid: Optional[str]
        if u.netloc.endswith("youtu.be"):
            vid = u.path.lstrip("/")
        else:
            vid = parse_qs(u.query).get("v", [None])[0]
        if not vid:
            return self._generic(url)

        try:
            oe = requests.get(
                "https://www.youtube.com/oembed",
                params={"url": f"https://www.youtube.com/watch?v={vid}", "format": "json"},
                headers=_ua(),
                timeout=int(self.config["timeout"]),
            )
            title = None
            author = None
            if oe.ok:
                data = oe.json()
                title = data.get("title")
                author = data.get("author_name")
        except Exception:
            title = None
            author = None

        thumb = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
        return CardData(
            url=f"https://www.youtube.com/watch?v={vid}",
            title=title or "YouTube Video",
            description=author or "",
            image=thumb or DATA_URI_YT,
            site="YouTube",
        )

    def _arxiv(self, url: str) -> CardData:
        """Scrape the arXiv abstract page for title and abstract."""
        u = urlparse(url)
        path = u.path
        if path.startswith("/pdf/"):
            path = "/abs/" + path.split("/pdf/")[1].replace(".pdf", "")
        abs_url = f"https://arxiv.org{path}" if "arxiv.org" not in url else url

        resp = requests.get(abs_url, headers=_ua(), timeout=int(self.config["timeout"]))
        soup = BeautifulSoup(resp.text, "lxml")
        h1 = soup.select_one("h1.title")
        title = (
            h1.get_text(" ", strip=True).replace("Title:", "").strip()
            if h1
            else "arXiv"
        )
        abstract_el = soup.select_one("blockquote.abstract")
        abstract = (
            abstract_el.get_text(" ", strip=True).replace("Abstract:", "").strip()
            if abstract_el
            else ""
        )
        if len(abstract) > 280:
            abstract = abstract[:280] + "…"

        return CardData(
            url=abs_url,
            title=title,
            description=abstract,
            image=DATA_URI_ARXIV,
            site="arXiv.org",
        )

    def _x(self, url: str) -> CardData:
        """Try Twitter oEmbed, otherwise a minimal card with icon."""
        text = ""
        author = ""
        try:
            r = requests.get(
                "https://publish.twitter.com/oembed",
                params={"url": url, "omit_script": "1", "hide_thread": "1"},
                headers=_ua(),
                timeout=int(self.config["timeout"]),
            )
            if r.ok:
                j = r.json()
                author = j.get("author_name", "") or ""
                # Extract plain text from embedded HTML if present.
                html = j.get("html", "")
                if html:
                    text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
        except Exception:
            pass

        desc = (author + " — " if author else "") + (text[:240] + "…" if len(text) > 240 else text)
        return CardData(
            url=url,
            title=author or "X (Twitter) post",
            description=desc,
            image=DATA_URI_X,
            site="X.com",
        )


# --- utilities ------------------------------------------------------------

def _first_og(items: list[dict[str, Any]]) -> dict[str, str]:
    for item in items:
        props = item.get("properties") if isinstance(item, dict) else None
        if isinstance(props, list):
            flattened = {}
            for key, value in props:
                if key not in flattened:
                    flattened[key] = value
            return flattened
    return {}


def _meta(soup: BeautifulSoup, names: list[str]) -> str:
    for attr in ("property", "name"):
        for name in names:
            tag = soup.find("meta", attrs={attr: name})
            if tag:
                content = tag.get("content")
                if content:
                    return content.strip()
    return ""


def _first(*values: Any, default: Any = "") -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
        else:
            return value
    return default


def _ua() -> Dict[str, str]:
    """Return a polite User-Agent header."""
    return {"User-Agent": "mkdocs-link-cards/0.1 (+https://github.com/markeyser/mkdocs-link-cards)"}


def _escape_md(text: str) -> str:
    """Escape characters that break Markdown emphasis/links."""
    return text.replace("*", r"\*").replace("_", r"\_").replace("|", r"\|")

import os
import re
import html
import uuid
import urllib.parse
import asyncio
import httpx
from typing import Any
from pathlib import Path
from pydantic import BaseModel, Field

from app.ai.tools.base import BaseTool, ToolPermission
from app.config import settings

# Static directory for saved Pinterest images
PINTEREST_DIR = Path("static/images/pinterest")
PINTEREST_DIR.mkdir(parents=True, exist_ok=True)


class SearchPinterestArgs(BaseModel):
    query: str = Field(
        ...,
        description="Search query for Pinterest pins (e.g., 'vijay and ajith recent', 'aesthetic dark wallpapers', 'minimalist architecture', 'celebrity outfits')."
    )
    count: int = Field(
        default=4,
        description="Number of Pinterest images to return (between 1 and 8). Defaults to 4."
    )


class SearchPinterestTool(BaseTool):
    name = "search_pinterest"
    description = (
        "Search and retrieve authentic, high-resolution pictures, pins, celebrity photos, wallpapers, and aesthetic inspirations from Pinterest. "
        "CRITICAL: Always use this tool when the user asks for Pinterest pictures, real photos of celebrities/actors, wallpapers, or asks for pictures from Pinterest! "
        "Do NOT call 'generate_image' when the user requests real pictures, photos, or Pinterest pins!"
    )
    permission = ToolPermission.READ
    args_schema = SearchPinterestArgs

    async def _download_and_cache(self, client: httpx.AsyncClient, img_url: str, filename: str) -> str | None:
        try:
            dest_path = PINTEREST_DIR / filename
            resp = await client.get(img_url, timeout=7.0)
            if resp.status_code == 200 and len(resp.content) > 1000:
                dest_path.write_bytes(resp.content)
                return f"{settings.BACKEND_URL}/static/images/pinterest/{filename}"
        except Exception:
            pass
        return None

    async def execute(self, query: str, count: int = 4, **kwargs: Any) -> dict[str, Any]:
        count = max(1, min(count, 8))
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }

        # 1. Clean query to remove noise words
        clean_q = re.sub(
            r'\b(site:pinterest\.com|pinterest|pin|pins|give|show|me|image|images|photo|photos|picture|pictures|wallpaper|wallpapers)\b',
            '',
            query,
            flags=re.IGNORECASE
        ).strip()
        clean_q = re.sub(r'\s+', ' ', clean_q).strip()
        if not clean_q:
            clean_q = query.strip()

        # Extract significant query keywords for relevance validation
        stop_words = {"the", "and", "for", "with", "from", "hd", "4k", "all", "best", "top", "new"}
        query_keywords = [
            w.lower()
            for w in re.findall(r'[a-zA-Z0-9]+', clean_q)
            if len(w) >= 3 and w.lower() not in stop_words
        ]

        search_attempts = [
            f"{clean_q} pinterest",
            f"{clean_q} wallpaper pinterest",
            f"{clean_q} aesthetic pinterest",
            f"{clean_q} hd wallpaper",
        ]

        pins: list[dict[str, str]] = []
        seen_images: set[str] = set()

        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=12.0) as client:
                for attempt in search_attempts:
                    if len(pins) >= count:
                        break
                    url = f"https://www.bing.com/images/search?q={urllib.parse.quote(attempt)}&FORM=HDRSC2"
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue

                    pattern = re.compile(r'm="(\{[^"]+\})"')
                    raw_matches = pattern.findall(resp.text)

                    for raw in raw_matches:
                        if len(pins) >= count:
                            break
                        decoded = html.unescape(raw)
                        m_img = re.search(r'"murl":"([^"]+)"', decoded)
                        m_pin = re.search(r'"purl":"([^"]+)"', decoded)
                        m_title = re.search(r'"t":"([^"]+)"', decoded)

                        if not m_img:
                            continue

                        direct_img = m_img.group(1)
                        pin_url = m_pin.group(1) if m_pin else f"https://www.pinterest.com/search/pins/?q={urllib.parse.quote(clean_q)}"
                        raw_title = m_title.group(1) if m_title else clean_q
                        clean_title = html.unescape(raw_title).replace("| Pinterest", "").strip()

                        # STRICT RELEVANCE CHECK:
                        # At least one query keyword MUST be in title, image URL, pin URL, or decoded payload
                        text_blob = f"{clean_title} {direct_img} {pin_url} {decoded}".lower()
                        if query_keywords:
                            is_relevant = any(kw in text_blob for kw in query_keywords)
                            if not is_relevant:
                                continue

                        # Check if Pinterest source
                        is_pinterest = (
                            "pinimg.com" in direct_img
                            or "pinterest.com" in pin_url.lower()
                            or "pinterest" in decoded.lower()
                        )
                        if not is_pinterest and pins:
                            # Prefer purely Pinterest results if already collected
                            continue

                        # Upgrade small preview images (236x/474x/564x) to 736x HD
                        high_res_img = re.sub(r'/(236x|474x|564x)/', '/736x/', direct_img)
                        if high_res_img in seen_images:
                            continue
                        seen_images.add(high_res_img)

                        # Cache image locally for instant display
                        file_ext = "jpg"
                        if ".png" in high_res_img.lower():
                            file_ext = "png"
                        filename = f"{uuid.uuid4().hex[:12]}.{file_ext}"
                        local_url = await self._download_and_cache(client, high_res_img, filename)
                        final_img_url = local_url if local_url else high_res_img

                        pins.append({
                            "title": clean_title,
                            "image_url": final_img_url,
                            "pin_url": pin_url,
                            "source": "Pinterest" if is_pinterest else "Web HD",
                        })
        except Exception as e:
            if not pins:
                return {
                    "status": "error",
                    "message": f"Failed to search Pinterest: {str(e)}",
                    "pins": [],
                }

        if not pins:
            return {
                "status": "not_found",
                "message": f"No relevant Pinterest pins found for '{clean_q}'.",
                "pins": [],
            }

        md_lines = []
        for p in pins:
            pin_link = p.get("pin_url", "")
            md_lines.append(f"![{p['title']}|pin={pin_link}]({p['image_url']})")

        markdown_output = "\n\n".join(md_lines)

        return {
            "status": "success",
            "query": clean_q,
            "count": len(pins),
            "pins": pins,
            "markdown": markdown_output,
            "message": f"Found {len(pins)} authentic Pinterest pins for '{clean_q}'.",
        }

import os
import time
import uuid
import urllib.parse
import asyncio
import httpx
from typing import Any
from pathlib import Path
from pydantic import BaseModel, Field

from app.ai.tools.base import BaseTool, ToolPermission
from app.config import settings

# Static directory for saved images
STATIC_IMAGES_DIR = Path("static/images")
STATIC_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


class GenerateImageArgs(BaseModel):
    prompt: str = Field(
        ...,
        description="Detailed visual prompt describing the subject, lighting, composition, colors, and atmosphere of the desired image."
    )
    style: str = Field(
        default="photorealistic",
        description="Artistic style: 'photorealistic', 'cinematic', 'anime', 'cyberpunk', 'digital art', 'fantasy', 'minimalist', 'logo'"
    )
    aspect_ratio: str = Field(
        default="1:1",
        description="Aspect ratio: '1:1' (square), '16:9' (landscape / wallpaper), '9:16' (portrait / mobile), '4:3' (standard)"
    )


class GenerateImageTool(BaseTool):
    name = "generate_image"
    description = (
        "Generate stunning, high-resolution visual artwork, photos, illustrations, logos, or wallpapers from a descriptive prompt. "
        "Returns the image URL and Markdown embed code."
    )
    permission = ToolPermission.READ
    args_schema = GenerateImageArgs

    _style_modifiers = {
        "photorealistic": "highly detailed, 8k resolution, cinematic lighting, photorealistic, professional photography, octane render",
        "cinematic": "cinematic still, 35mm lens, dramatic lighting, depth of field, anamorphic, color graded, blockbuster film aesthetic",
        "anime": "vibrant anime style, detailed studio ghibli and makoto shinkai aesthetic, vivid colors, clean linework",
        "cyberpunk": "cyberpunk aesthetic, neon glow, holographic reflections, futuristic city, rainy reflections, high tech",
        "digital art": "digital concept art, trending on ArtStation, vivid colors, intricate details, masterwork illustration",
        "fantasy": "epic fantasy style, ethereal glowing lighting, mythical atmosphere, highly detailed oil painting effect",
        "minimalist": "minimalist aesthetic, clean lines, elegant composition, modern aesthetic, high aesthetic quality",
        "logo": "clean vector logo design, iconic symbol, minimalist branding, flat color, professional emblem, white background",
    }

    _dimension_map = {
        "1:1": (1024, 1024),
        "16:9": (1280, 720),
        "9:16": (720, 1280),
        "4:3": (1024, 768),
        "3:4": (768, 1024),
    }

    async def _download_and_cache(self, url: str, filename: str) -> str | None:
        """Download image in the background and save to backend static directory."""
        try:
            dest_path = STATIC_IMAGES_DIR / filename
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200 and len(resp.content) > 1000:
                    dest_path.write_bytes(resp.content)
                    return f"{settings.BACKEND_URL}/static/images/{filename}"
        except Exception:
            pass
        return None

    async def execute(
        self,
        prompt: str,
        style: str = "photorealistic",
        aspect_ratio: str = "1:1",
        **kwargs: Any
    ) -> dict[str, Any]:
        style_key = style.lower().strip()
        modifier = self._style_modifiers.get(style_key, self._style_modifiers["photorealistic"])
        enhanced_prompt = f"{prompt.strip()}, {modifier}"

        w, h = self._dimension_map.get(aspect_ratio, (1024, 1024))
        seed = int(time.time())
        encoded_prompt = urllib.parse.quote(enhanced_prompt)

        # Primary CDN URL via Pollinations engine
        cdn_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={w}&height={h}&nologo=true&enhance=true&seed={seed}"

        # Attempt quick local caching
        img_id = uuid.uuid4().hex[:12]
        filename = f"{img_id}.jpg"
        local_url = await self._download_and_cache(cdn_url, filename)

        chosen_url = local_url if local_url else cdn_url

        return {
            "status": "success",
            "prompt": prompt,
            "style": style,
            "aspect_ratio": aspect_ratio,
            "image_url": chosen_url,
            "cdn_url": cdn_url,
            "local_url": local_url,
            "markdown": f"![{prompt}]({chosen_url})",
            "message": f"Successfully generated visual for '{prompt}'.",
        }

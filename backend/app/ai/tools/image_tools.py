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
        "Generate synthetic AI artwork, logos, or digital illustrations from text prompts. "
        "CRITICAL: ONLY invoke this tool when the user EXPLICITLY asks to 'generate an AI image', 'draw', 'paint', or 'create AI art'. "
        "NEVER call this tool for photos, pictures, characters, anime, celebrities, or wallpapers — for all picture requests, invoke 'search_pinterest'!"
    )
    permission = ToolPermission.READ
    args_schema = GenerateImageArgs

    _style_modifiers = {
        "photorealistic": "highly detailed, 8k resolution, cinematic lighting, photorealistic, professional photography, octane render",
        "cinematic": "cinematic still, 35mm lens, dramatic lighting, depth of field, anamorphic, color graded, blockbuster film aesthetic",
        "anime": "masterpiece anime artwork, vibrant colors, official key visual, crisp linework, highly detailed, studio ufotable and mappa quality",
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

        # Auto-detect anime or animated prompts so we never apply uncanny photorealism
        prompt_lower = prompt.lower()
        anime_keywords = [
            "anime", "manga", "naruto", "sasuke", "goku", "luffy", "jujutsu",
            "sukuna", "gojo", "itachi", "waifu", "shonen", "otaku", "chibi",
            "cartoon", "comic", "demon slayer", "tanjiro", "zoro", "kakashi"
        ]
        if any(kw in prompt_lower for kw in anime_keywords) and style_key in ["photorealistic", "default"]:
            style_key = "anime"

        modifier = self._style_modifiers.get(style_key, self._style_modifiers["photorealistic"])
        enhanced_prompt = f"{prompt.strip()}, {modifier}"

        w, h = self._dimension_map.get(aspect_ratio, (1024, 1024))
        seed = int(time.time())
        encoded_prompt = urllib.parse.quote(enhanced_prompt)

        # Primary CDN URL via Pollinations with state-of-the-art Flux engine
        cdn_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={w}&height={h}&nologo=true&enhance=true&model=flux&seed={seed}"

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


class EnhanceImageArgs(BaseModel):
    image_url_or_path: str = Field(
        default="",
        description="The URL, file path, attachment reference, or empty string to enhance the user's uploaded or referenced image."
    )
    mode: str = Field(
        default="hd_clarity",
        description="Enhancement preset: 'hd_clarity' (sharpness & crisp details), 'super_resolution' (2x upscale + detail boost), 'vibrant' (rich color & dynamic contrast), 'cinematic' (moody film tone & contrast), 'denoise_smooth' (clean noise & smooth artifacts)"
    )
    upscale_factor: float = Field(
        default=2.0,
        description="Upscale factor: 1.0 (keep original dimensions), 1.5, or 2.0 (2x HD upscale)"
    )


class EnhanceImageTool(BaseTool):
    name = "enhance_image"
    description = (
        "Enhance, upscale, clarify, retouch, and improve the quality of an existing image. "
        "Use this tool whenever the user uploads or provides an image (or image URL) and asks to 'enhance it', "
        "'upscale', 'increase quality', 'make it HD', 'sharpen', 'improve clarity', or 'retouch'."
    )
    permission = ToolPermission.READ
    args_schema = EnhanceImageArgs

    async def execute(
        self,
        image_url_or_path: str = "",
        mode: str = "hd_clarity",
        upscale_factor: float = 2.0,
        **kwargs: Any
    ) -> dict[str, Any]:
        from io import BytesIO
        import base64
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps

        raw_bytes = None
        target = (image_url_or_path or "").strip().strip("'\"")

        # 1. Check if target is a base64 data URI
        if target.startswith("data:"):
            try:
                comma_idx = target.find(",")
                if comma_idx != -1:
                    raw_bytes = base64.b64decode(target[comma_idx + 1:])
            except Exception:
                pass

        # 2. Fetch image from URL
        if not raw_bytes and (target.startswith("http://") or target.startswith("https://")):
            try:
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    resp = await client.get(target, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200:
                        raw_bytes = resp.content
            except Exception as e:
                return {"status": "error", "message": f"Failed to download image from URL: {e}"}

        # 3. Check local candidate paths if target was provided
        if not raw_bytes and target and not target.lower().startswith("attachment"):
            local_candidates = [
                Path(target),
                Path(target.lstrip("/")),
                Path("static/images") / Path(target).name,
                Path("static") / Path(target).name,
            ]
            for candidate in local_candidates:
                if candidate.exists() and candidate.is_file():
                    raw_bytes = candidate.read_bytes()
                    break

        # 4. Fallback to attachments from context
        if not raw_bytes:
            attachments = kwargs.get("attachments") or []
            for att in attachments:
                data_str = att.get("data") or ""
                url_str = att.get("url") or ""
                if data_str.startswith("data:"):
                    try:
                        comma_idx = data_str.find(",")
                        if comma_idx != -1:
                            raw_bytes = base64.b64decode(data_str[comma_idx + 1:])
                            break
                    except Exception:
                        pass
                elif len(data_str) > 100 and not data_str.startswith("http"):
                    try:
                        raw_bytes = base64.b64decode(data_str)
                        break
                    except Exception:
                        pass
                elif url_str.startswith("http://") or url_str.startswith("https://"):
                    try:
                        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                            resp = await client.get(url_str, headers={"User-Agent": "Mozilla/5.0"})
                            if resp.status_code == 200:
                                raw_bytes = resp.content
                                break
                    except Exception:
                        pass

        if not raw_bytes:
            return {"status": "error", "message": f"Could not access image. Please provide a valid image URL or attach an image."}

        try:
            img = Image.open(BytesIO(raw_bytes))
            img = img.convert("RGB")
            orig_w, orig_h = img.size

            # 2. Upscale if requested
            factor = max(1.0, min(float(upscale_factor), 3.0))
            if factor > 1.0:
                new_w = int(orig_w * factor)
                new_h = int(orig_h * factor)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            else:
                new_w, new_h = orig_w, orig_h

            # 3. Apply enhancement filters based on mode
            mode_key = mode.lower().strip()

            if mode_key in ["hd_clarity", "super_resolution"]:
                # High-fidelity detail sharpening & contrast
                img = ImageOps.autocontrast(img, cutoff=0.5)
                img = ImageEnhance.Sharpness(img).enhance(1.45)
                img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
                img = ImageEnhance.Contrast(img).enhance(1.12)
                img = ImageEnhance.Color(img).enhance(1.08)
            elif mode_key == "vibrant":
                # Rich color vibrancy & dynamic pop
                img = ImageOps.autocontrast(img, cutoff=1.0)
                img = ImageEnhance.Color(img).enhance(1.30)
                img = ImageEnhance.Contrast(img).enhance(1.18)
                img = ImageEnhance.Sharpness(img).enhance(1.25)
            elif mode_key == "cinematic":
                # Film grading with rich shadows and sharpness
                img = ImageEnhance.Contrast(img).enhance(1.22)
                img = ImageEnhance.Color(img).enhance(1.10)
                img = img.filter(ImageFilter.UnsharpMask(radius=2.5, percent=130, threshold=2))
                img = ImageEnhance.Brightness(img).enhance(1.03)
            elif mode_key == "denoise_smooth":
                # Denoising followed by edge reconstruction
                img = img.filter(ImageFilter.SMOOTH_MORE)
                img = img.filter(ImageFilter.EDGE_ENHANCE)
                img = ImageEnhance.Contrast(img).enhance(1.05)
            else:
                # Default auto-enhance
                img = ImageOps.autocontrast(img, cutoff=0.5)
                img = ImageEnhance.Sharpness(img).enhance(1.35)
                img = ImageEnhance.Contrast(img).enhance(1.10)

            # 4. Save enhanced result to static directory
            img_id = uuid.uuid4().hex[:12]
            filename = f"enhanced_{img_id}.jpg"
            dest_path = STATIC_IMAGES_DIR / filename
            img.save(dest_path, "JPEG", quality=95, optimize=True)

            enhanced_url = f"{settings.BACKEND_URL}/static/images/{filename}"

            return {
                "status": "success",
                "original_resolution": f"{orig_w}x{orig_h}",
                "enhanced_resolution": f"{new_w}x{new_h}",
                "mode": mode,
                "image_url": enhanced_url,
                "markdown": f"![Enhanced Image ({new_w}x{new_h})|pin=none]({enhanced_url})",
                "message": f"Successfully enhanced image from {orig_w}x{orig_h} to {new_w}x{new_h} HD using '{mode}' mode.",
            }
        except Exception as e:
            return {"status": "error", "message": f"Image enhancement failed: {e}"}


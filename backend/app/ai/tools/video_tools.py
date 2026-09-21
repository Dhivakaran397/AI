import os
import io
import math
import struct
import wave
import uuid
import asyncio
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any
import httpx
from PIL import Image, ImageDraw, ImageFont

import imageio_ffmpeg
from app.ai.tools.base import BaseTool
from app.config import settings


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Return a high-quality Windows TrueType font, falling back gracefully."""
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


async def _fetch_ai_image(prompt: str, width: int, height: int, seed: int) -> Image.Image | None:
    """Fetch a photorealistic / cinematic AI scene visual via Pollinations engine."""
    clean_p = prompt.strip()
    enhanced = f"{clean_p}, cinematic movie still, 8k resolution, dramatic lighting, highly detailed, photorealistic"
    encoded = urllib.parse.quote(enhanced)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&enhance=true&seed={seed}"
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200 and len(resp.content) > 3000:
                img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                return img
    except Exception:
        pass
    return None


def _generate_procedural_audio(wav_path: str, duration_sec: float, mood: str = "energetic"):
    """
    Synthesizes a pleasant ambient lo-fi / cinematic background rhythm in standard PCM WAV format.
    No external sound files required.
    """
    sample_rate = 44100
    n_samples = int(sample_rate * duration_sec)
    
    chords = [
        [261.63, 329.63, 392.00],  # C major
        [220.00, 261.63, 329.63],  # A minor
        [174.61, 220.00, 261.63],  # F major
        [196.00, 246.94, 293.66],  # G major
    ]
    
    samples = []
    chord_len = max(1.5, duration_sec / max(1, len(chords)))
    
    for i in range(n_samples):
        t = i / sample_rate
        chord_idx = int(t / chord_len) % len(chords)
        chord = chords[chord_idx]
        
        val = 0.0
        for freq in chord:
            val += 0.25 * math.sin(2 * math.pi * freq * t)
            val += 0.08 * math.sin(2 * math.pi * (freq * 2) * t)
            
        beat_freq = 2.0 if mood == "energetic" else 1.0
        beat_env = (1.0 + 0.4 * math.sin(2 * math.pi * beat_freq * t))
        
        fade_in = min(1.0, t / 0.5)
        fade_out = min(1.0, (duration_sec - t) / 0.8)
        
        sample_val = val * beat_env * fade_in * fade_out * 0.3
        sample_val = max(-1.0, min(1.0, sample_val))
        int_sample = int(sample_val * 32767)
        samples.append(int_sample)
        
    with wave.open(wav_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        data = struct.pack(f'<{len(samples)}h', *samples)
        wav_file.writeframes(data)


class GenerateVideoTool(BaseTool):
    name = "generate_video"
    description = (
        "Generate a complete high-definition animated MP4 video with authentic AI-generated visual scenes, "
        "Ken Burns cinematic camera motion, large subtitles, and synchronized soundtrack. "
        "Perfect for Instagram Reels, YouTube Shorts, TikTok (9:16 vertical), or widescreen presentations (16:9)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The title or subject of the video (e.g. 'Avengers Civil War Airport Battle', '5 AI Trends 2026')"
            },
            "format": {
                "type": "string",
                "enum": ["reels_vertical", "landscape_16_9"],
                "description": "Video aspect ratio: 'reels_vertical' (9:16 vertical reels) or 'landscape_16_9' (16:9 widescreen)",
                "default": "reels_vertical"
            },
            "music_mood": {
                "type": "string",
                "enum": ["energetic", "calm", "cinematic"],
                "description": "Ambient background rhythm / mood for the soundtrack",
                "default": "cinematic"
            },
            "scenes": {
                "type": "array",
                "description": "Sequence of 3 to 5 animated scenes with headlines, subtitles, and visual prompts",
                "items": {
                    "type": "object",
                    "properties": {
                        "headline": {"type": "string", "description": "Punchy scene headline or big takeaway"},
                        "subtitle": {"type": "string", "description": "Supporting context or subtitle text"},
                        "visual_prompt": {
                            "type": "string",
                            "description": "Detailed image generation prompt for this scene (e.g. 'Iron Man and Captain America faceoff, airport battle, cinematic film still, 8k')"
                        },
                        "points": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "1-2 key bullet points"
                        },
                        "accent_color": {
                            "type": "string",
                            "description": "Hex color e.g. '#6366f1', '#ec4899', '#10b981', '#f59e0b'"
                        },
                        "duration_sec": {
                            "type": "number",
                            "description": "Duration of this scene in seconds (typically 3.0 to 4.5 seconds)",
                            "default": 3.5
                        }
                    },
                    "required": ["headline"]
                }
            }
        },
        "required": ["topic", "scenes"]
    }

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        topic = kwargs.get("topic") or kwargs.get("title") or "AI Video Presentation"
        raw_format = kwargs.get("format") or kwargs.get("aspect_ratio") or "reels_vertical"
        if "16:9" in str(raw_format).lower() or "landscape" in str(raw_format).lower():
            video_format = "landscape_16_9"
        else:
            video_format = "reels_vertical"

        music_mood = kwargs.get("music_mood") or kwargs.get("theme") or "cinematic"
        raw_scenes = kwargs.get("scenes", [])
        
        if not raw_scenes:
            raw_scenes = [
                {"headline": topic, "subtitle": "Created by DAI Autonomous Engine", "duration_sec": 3.5}
            ]

        if video_format == "landscape_16_9":
            width, height = 1280, 720
        else:
            width, height = 720, 1280  # 9:16 vertical reel

        video_id = uuid.uuid4().hex[:12]
        output_dir = Path("static/videos")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        mp4_filename = f"{video_id}.mp4"
        final_mp4_path = output_dir / mp4_filename
        temp_wav_path = output_dir / f"temp_{video_id}.wav"
        temp_raw_video = output_dir / f"temp_raw_{video_id}.mp4"
        
        fps = 24
        total_duration = sum(float(s.get("duration_sec") or s.get("duration") or 3.5) for s in raw_scenes)
        total_duration = max(3.0, min(total_duration, 45.0))

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

        # Fetch real AI visual imagery for all scenes concurrently
        image_tasks = []
        for idx, s in enumerate(raw_scenes):
            v_prompt = s.get("visual_prompt") or s.get("prompt")
            if not v_prompt:
                h = s.get("headline") or s.get("title") or topic
                sub = s.get("subtitle") or s.get("caption") or ""
                v_prompt = f"{h}, {sub}, {topic}, cinematic movie still, blockbuster scene, 8k resolution, dramatic lighting, highly detailed"
            seed = 1000 + idx * 77
            image_tasks.append(_fetch_ai_image(v_prompt, width, height, seed))

        fetched_images = await asyncio.gather(*image_tasks, return_exceptions=True)

        # Fallback theme colors
        color_palettes = [
            ("#0f172a", "#1e1b4b", "#6366f1"),
            ("#09090b", "#1c1917", "#ec4899"),
            ("#022c22", "#064e3b", "#10b981"),
            ("#172554", "#1e3a8a", "#0ea5e9"),
            ("#2e1065", "#3b0764", "#8b5cf6"),
        ]

        # Start FFmpeg raw video pipe
        ffmpeg_cmd = [
            ffmpeg_exe,
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{width}x{height}",
            "-pix_fmt", "rgb24",
            "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "veryfast",
            "-crf", "22",
            str(temp_raw_video)
        ]

        pipe = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        font_brand = _get_font(18, bold=True)
        font_pill = _get_font(16, bold=True)
        font_title = _get_font(34 if video_format == "reels_vertical" else 36, bold=True)
        font_sub = _get_font(21, bold=False)
        font_pt = _get_font(18, bold=False)

        global_frame_idx = 0
        total_frames = int(total_duration * fps)

        for scene_idx, scene in enumerate(raw_scenes):
            scene_duration = float(scene.get("duration_sec") or scene.get("duration") or 3.5)
            scene_frames = int(scene_duration * fps)
            palette = color_palettes[scene_idx % len(color_palettes)]
            accent_hex = scene.get("accent_color", palette[2])
            
            headline = scene.get("headline") or scene.get("title") or topic
            subtitle = scene.get("subtitle") or scene.get("caption") or scene.get("description") or ""
            points = scene.get("points") or []

            # Get scene image or create procedural fallback
            scene_img = fetched_images[scene_idx] if scene_idx < len(fetched_images) else None
            if not isinstance(scene_img, Image.Image):
                scene_img = Image.new("RGB", (width, height), color=palette[0])
                f_draw = ImageDraw.Draw(scene_img)
                f_draw.ellipse([width//2 - 350, height//2 - 350, width//2 + 350, height//2 + 350], fill=palette[1])

            # Pre-resize base image to 1.15x for smooth Ken Burns pan & zoom
            scale_margin = 1.15
            target_w = int(width * scale_margin)
            target_h = int(height * scale_margin)
            base_img = scene_img.resize((target_w, target_h), Image.Resampling.BILINEAR)

            # Alternate motion styles per scene (Zoom In, Pan Across, Zoom Out)
            motion_style = scene_idx % 3

            for f in range(scene_frames):
                prog = f / max(1, scene_frames)
                overall_prog = global_frame_idx / max(1, total_frames)

                if motion_style == 0:
                    # Zoom In
                    curr_scale = scale_margin - 0.12 * prog
                    cw = int(width * curr_scale)
                    ch = int(height * curr_scale)
                    cx = int((base_img.width - cw) / 2)
                    cy = int((base_img.height - ch) / 2)
                elif motion_style == 1:
                    # Pan Left to Right with slight zoom
                    curr_scale = 1.06
                    cw = int(width * curr_scale)
                    ch = int(height * curr_scale)
                    cx = int((base_img.width - cw) * prog)
                    cy = int((base_img.height - ch) / 2)
                else:
                    # Zoom Out
                    curr_scale = 1.02 + 0.11 * prog
                    cw = int(width * curr_scale)
                    ch = int(height * curr_scale)
                    cx = int((base_img.width - cw) / 2)
                    cy = int((base_img.height - ch) / 2)

                cx = max(0, min(cx, base_img.width - cw))
                cy = max(0, min(cy, base_img.height - ch))
                frame = base_img.crop((cx, cy, cx + cw, cy + ch)).resize((width, height), Image.Resampling.BILINEAR)
                draw = ImageDraw.Draw(frame)

                # Top Progress Bar (animated neon line across top edge)
                draw.rectangle([0, 0, width, 5], fill=(20, 20, 25))
                draw.rectangle([0, 0, int(width * overall_prog), 5], fill=accent_hex)

                # Brand Pill (top left)
                draw.rounded_rectangle([35, 35, 175, 75], radius=14, fill=(0, 0, 0, 180), outline=(255, 255, 255))
                draw.text((50, 44), "DAI CINEMA", font=font_brand, fill=(255, 255, 255))

                # Scene Counter Pill (top right)
                counter_str = f"SCENE {scene_idx + 1:02d} / {len(raw_scenes):02d}"
                draw.rounded_rectangle([width - 185, 35, width - 35, 75], radius=14, fill=(0, 0, 0, 180), outline=accent_hex)
                draw.text((width - 170, 46), counter_str, font=font_pill, fill=(255, 255, 255))

                # Bottom Frosted Glass Caption Card
                if video_format == "reels_vertical":
                    card_h = 280 if points else 210
                    card_top = height - card_h - 40
                    card_box = [30, card_top, width - 30, height - 40]
                else:
                    card_h = 190
                    card_top = height - card_h - 25
                    card_box = [45, card_top, width - 45, height - 25]

                # Draw dark frosted container with stylish rounded border
                draw.rounded_rectangle(card_box, radius=20, fill=(0, 0, 0, 210), outline=accent_hex, width=2)

                # Headline
                text_x = card_box[0] + 25
                text_y = card_top + 20
                draw.text((text_x, text_y), headline[:48], font=font_title, fill=(255, 255, 255))

                # Subtitle
                if subtitle:
                    sub_y = text_y + 44
                    draw.text((text_x, sub_y), subtitle[:75], font=font_sub, fill=(225, 225, 235))

                # Bullet points
                if points:
                    pt_y = text_y + (86 if subtitle else 50)
                    for pt in points[:2]:
                        draw.text((text_x, pt_y), f"•  {str(pt)[:55]}", font=font_pt, fill=(200, 205, 215))
                        pt_y += 30

                # Pipe RGB frame to FFmpeg
                raw_bytes = frame.tobytes()
                pipe.stdin.write(raw_bytes)
                global_frame_idx += 1

        pipe.stdin.close()
        pipe.wait()

        # Step 2: Generate procedural audio
        _generate_procedural_audio(str(temp_wav_path), total_duration, mood=music_mood)

        # Step 3: Mux audio + video with FFmpeg
        mux_cmd = [
            ffmpeg_exe,
            "-y",
            "-i", str(temp_raw_video),
            "-i", str(temp_wav_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            str(final_mp4_path)
        ]
        subprocess.run(mux_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        try:
            if temp_raw_video.exists():
                temp_raw_video.unlink()
            if temp_wav_path.exists():
                temp_wav_path.unlink()
        except Exception:
            pass

        video_url = f"{settings.BACKEND_URL}/static/videos/{mp4_filename}"

        return {
            "status": "success",
            "video_id": video_id,
            "title": topic,
            "format": video_format,
            "duration": round(total_duration, 1),
            "scenes_count": len(raw_scenes),
            "video_url": video_url,
            "download_url": video_url,
            "scenes": [
                {
                    "headline": s.get("headline"),
                    "subtitle": s.get("subtitle", ""),
                    "duration": s.get("duration_sec", 3.5)
                }
                for s in raw_scenes
            ]
        }


class GenerateCarouselTool(BaseTool):
    name = "generate_social_carousel"
    description = (
        "Generate a high-impact multi-slide Social Media Carousel (Instagram, LinkedIn) "
        "with authentic AI artwork, modern typography, category badges, and swipeable takeaways."
    )
    parameters = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Topic or title of the carousel (e.g. '5 Rules of Clean Architecture', 'Avengers Battle Breakdown')"
            },
            "platform": {
                "type": "string",
                "enum": ["instagram", "linkedin"],
                "description": "Target platform layout: 'instagram' or 'linkedin'",
                "default": "instagram"
            },
            "slides": {
                "type": "array",
                "description": "3 to 6 slides forming a cohesive narrative",
                "items": {
                    "type": "object",
                    "properties": {
                        "slide_number": {"type": "integer"},
                        "title": {"type": "string", "description": "Slide header or takeaway"},
                        "description": {"type": "string", "description": "Core explanation or takeaway"},
                        "visual_prompt": {"type": "string", "description": "Descriptive AI prompt for slide visual"},
                        "bullet_points": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "1 to 3 bullet points"
                        },
                        "tag": {"type": "string", "description": "Category badge e.g. 'PART 1', 'RULE #1', 'TAKEAWAY'"}
                    },
                    "required": ["title", "description"]
                }
            }
        },
        "required": ["topic", "slides"]
    }

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        topic = kwargs.get("topic", "Social Media Carousel")
        platform = kwargs.get("platform", "instagram")
        slides = kwargs.get("slides", [])

        carousel_id = uuid.uuid4().hex[:12]
        carousel_dir = Path("static/carousels") / carousel_id
        carousel_dir.mkdir(parents=True, exist_ok=True)

        width, height = 1080, 1080

        # Fetch AI illustrations for slides concurrently
        img_tasks = []
        for idx, slide in enumerate(slides):
            v_p = slide.get("visual_prompt")
            if not v_p:
                v_p = f"{slide.get('title')}, {topic}, modern digital artwork, cinematic lighting, 8k, graphic design aesthetic"
            seed = 5000 + idx * 43
            img_tasks.append(_fetch_ai_image(v_p, width, height, seed))

        fetched_slides_img = await asyncio.gather(*img_tasks, return_exceptions=True)

        font_badge = _get_font(26, bold=True)
        font_title = _get_font(52, bold=True)
        font_desc = _get_font(30, bold=False)
        font_bullet = _get_font(26, bold=False)
        font_footer = _get_font(24, bold=True)

        theme_accents = ["#6366f1", "#ec4899", "#10b981", "#0ea5e9", "#8b5cf6", "#f59e0b"]
        rendered_slides = []

        for idx, slide in enumerate(slides):
            accent = theme_accents[idx % len(theme_accents)]
            slide_ai_img = fetched_slides_img[idx] if idx < len(fetched_slides_img) else None

            if isinstance(slide_ai_img, Image.Image):
                # Use real AI image as atmospheric background
                img = slide_ai_img.resize((width, height), Image.Resampling.BILINEAR)
                # Darken overlay for text readability
                overlay = Image.new("RGBA", (width, height), (0, 0, 0, 150))
                img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            else:
                img = Image.new("RGB", (width, height), color=(15, 23, 42))

            draw = ImageDraw.Draw(img)

            # Top Header Badges
            counter_text = f"SLIDE {idx + 1:02d} / {len(slides):02d}"
            draw.rounded_rectangle([60, 60, 260, 120], radius=16, fill=(0, 0, 0, 190), outline=accent, width=2)
            draw.text((80, 75), counter_text, font=font_badge, fill=(255, 255, 255))

            tag_text = slide.get("tag", f"PART {idx + 1}").upper()
            draw.rounded_rectangle([width - 280, 60, width - 60, 120], radius=16, fill=(0, 0, 0, 190), outline=(255, 255, 255), width=2)
            draw.text((width - 255, 75), tag_text[:12], font=font_badge, fill=accent)

            # Card Box in Center-Bottom
            card_top = 480
            draw.rounded_rectangle([60, card_top, width - 60, height - 120], radius=24, fill=(0, 0, 0, 220), outline=accent, width=2)

            # Main Slide Title
            title_text = slide.get("title", "")
            draw.text((100, card_top + 45), title_text[:50], font=font_title, fill=(255, 255, 255))

            # Description
            desc_text = slide.get("description", "")
            draw.text((100, card_top + 130), desc_text[:140], font=font_desc, fill=(220, 225, 235))

            # Bullet points
            bullets = slide.get("bullet_points", [])
            b_y = card_top + 215
            for b in bullets[:3]:
                draw.text((100, b_y), f"✔   {str(b)[:55]}", font=font_bullet, fill=(240, 240, 250))
                b_y += 55

            # Bottom Swipe Indicator
            draw.text((width // 2 - 90, height - 70), "Swipe Left →", font=font_footer, fill=(200, 200, 210))

            img_filename = f"slide_{idx + 1}.jpg"
            img_path = carousel_dir / img_filename
            img.save(str(img_path), quality=92)

            slide_url = f"{settings.BACKEND_URL}/static/carousels/{carousel_id}/{img_filename}"
            rendered_slides.append({
                "slide_number": idx + 1,
                "title": title_text,
                "description": desc_text,
                "bullet_points": bullets,
                "image_url": slide_url
            })

        return {
            "status": "success",
            "carousel_id": carousel_id,
            "title": topic,
            "platform": platform,
            "total_slides": len(rendered_slides),
            "slides": rendered_slides,
            "preview_image_url": rendered_slides[0]["image_url"] if rendered_slides else None
        }

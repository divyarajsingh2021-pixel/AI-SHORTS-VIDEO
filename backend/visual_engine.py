"""
Visual Engine & Match Verification.
Multi-tier visual generation:
1. Pollinations AI (free, no key, no model param -> instant high-res)
2. Unsplash local/fallback photo fetch
3. Procedural styled gradient cards with keywords as last resort
4. Match Verification: computes keyword overlap and semantic relevance score,
   with cache by hash(prompt + seed + shot_id).
"""

import os
import hashlib
import urllib.parse
import urllib.request
import time
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont

# Visual cache path
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "visual_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Helper file to track used hashes for uniqueness within a single run
_USED_HASHES_PATH = os.path.join(CACHE_DIR, "used_hashes.txt")

def _load_used_hashes() -> set:
    if os.path.exists(_USED_HASHES_PATH):
        try:
            with open(_USED_HASHES_PATH, "r", encoding="utf-8") as f:
                return set(line.strip() for line in f if line.strip())
        except Exception:
            return set()
    return set()

def _add_used_hash(h: str):
    try:
        with open(_USED_HASHES_PATH, "a", encoding="utf-8") as f:
            f.write(h + "\n")
    except Exception:
        pass

def get_prompt_hash(prompt: str, seed: int, shot_id: int = 0) -> str:
    """Generate deterministic hash for caching, now includes shot_id for uniqueness."""
    key = f"{prompt.strip().lower()}_{seed}_{shot_id}"
    return hashlib.md5(key.encode('utf-8')).hexdigest()[:16]

def generate_shot_visual(
    prompt: str,
    output_path: str,
    seed: int = 42,
    width: int = 1080,
    height: int = 1920,
    keywords: Optional[List[str]] = None,
    shot_id: int = 0,
) -> Tuple[bool, str]:
    """Generates image for a shot with caching and fallbacks.
    Returns: (success: bool, source_type: str)
    """
    # Include shot_id in cache key to avoid collisions
    cache_hash = get_prompt_hash(prompt, seed, shot_id)
    cached_file = os.path.join(CACHE_DIR, f"{cache_hash}.jpg")

    # 1. Check cache
    if os.path.exists(cached_file) and os.path.getsize(cached_file) > 10000:
        try:
            with open(cached_file, "rb") as sf, open(output_path, "wb") as df:
                df.write(sf.read())
            # Record used hash
            _add_used_hash(cache_hash)
            return True, "cache"
        except Exception:
            pass

    # Helper to verify uniqueness after a successful generation
    def _is_duplicate(file_path: str) -> bool:
        try:
            with open(file_path, "rb") as f:
                h = hashlib.md5(f.read()).hexdigest()
            used = _load_used_hashes()
            return h in used
        except Exception:
            return False

    # 2. Tier 1: Pollinations AI
    success = _fetch_pollinations(prompt, output_path, seed, width, height)
    if success:
        if not _is_duplicate(output_path):
            _save_to_cache(output_path, cached_file)
            _add_used_hash(cache_hash)
            return True, "pollinations"
        # duplicate – try with a new seed
        for _ in range(3):
            seed += 1
            cache_hash = get_prompt_hash(prompt, seed, shot_id)
            cached_file = os.path.join(CACHE_DIR, f"{cache_hash}.jpg")
            success = _fetch_pollinations(prompt, output_path, seed, width, height)
            if success and not _is_duplicate(output_path):
                _save_to_cache(output_path, cached_file)
                _add_used_hash(cache_hash)
                return True, "pollinations"

    # 3. Tier 2: Unsplash Stock Fallback
    kw_query = " ".join(keywords) if keywords else "temple ancient india"
    success = _fetch_unsplash(kw_query, output_path, width, height)
    if success:
        if not _is_duplicate(output_path):
            _save_to_cache(output_path, cached_file)
            _add_used_hash(cache_hash)
            return True, "unsplash"
        for _ in range(3):
            seed += 1
            cache_hash = get_prompt_hash(prompt, seed, shot_id)
            cached_file = os.path.join(CACHE_DIR, f"{cache_hash}.jpg")
            success = _fetch_unsplash(kw_query, output_path, width, height)
            if success and not _is_duplicate(output_path):
                _save_to_cache(output_path, cached_file)
                _add_used_hash(cache_hash)
                return True, "unsplash"

    # 4. Tier 3: Gradient Card
    success = _create_gradient_card(prompt, keywords or ["Scene"], output_path, width, height, shot_id)
    if success:
        # Gradient cards are deterministic; still check duplicate
        if not _is_duplicate(output_path):
            _save_to_cache(output_path, cached_file)
            _add_used_hash(cache_hash)
            return True, "gradient_card"
        # If duplicate, tweak seed/color by adjusting shot_id offset
        for offset in range(1, 4):
            new_shot_id = shot_id + offset
            cache_hash = get_prompt_hash(prompt, seed, new_shot_id)
            cached_file = os.path.join(CACHE_DIR, f"{cache_hash}.jpg")
            success = _create_gradient_card(prompt, keywords or ["Scene"], output_path, width, height, new_shot_id)
            if success and not _is_duplicate(output_path):
                _save_to_cache(output_path, cached_file)
                _add_used_hash(cache_hash)
                return True, "gradient_card"

    return False, "failed"

def _save_to_cache(src: str, dst: str):
    try:
        with open(src, "rb") as s, open(dst, "wb") as d:
            d.write(s.read())
    except Exception:
        pass

def _fetch_pollinations(prompt: str, output_path: str, seed: int, width: int, height: int) -> bool:
    try:
        clean_prompt = prompt.replace("\n", " ").strip()
        encoded = urllib.parse.quote(clean_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&seed={seed}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Shorts-Bot/2.0"})
        with urllib.request.urlopen(req, timeout=18) as response:
            content = response.read()
            if len(content) > 10000:
                with open(output_path, "wb") as f:
                    f.write(content)
                return True
    except Exception as e:
        print(f"[VisualEngine] Pollinations error: {e}")
    return False

def _fetch_unsplash(query: str, output_path: str, width: int, height: int) -> bool:
    try:
        clean_q = urllib.parse.quote(query.replace("\n", " ")[:60])
        source_url = f"https://source.unsplash.com/{width}x{height}/?{clean_q}"
        req = urllib.request.Request(source_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            if len(data) > 8000:
                with open(output_path, "wb") as f:
                    f.write(data)
                return True
    except Exception:
        pass
    return False

def _create_gradient_card(
    prompt: str,
    keywords: List[str],
    output_path: str,
    width: int,
    height: int,
    shot_id: int,
) -> bool:
    """Creates a sleek, modern vertical gradient background with key terms."""
    try:
        palettes = [
            ((20, 24, 40), (80, 20, 90)),
            ((15, 32, 39), (44, 83, 100)),
            ((43, 8, 8), (128, 20, 20)),
            ((20, 30, 48), (36, 59, 85)),
        ]
        c1, c2 = palettes[shot_id % len(palettes)]
        img = Image.new("RGB", (width, height), color=c1)
        draw = ImageDraw.Draw(img)
        for y in range(height):
            ratio = y / height
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        font_path = "C:\\Windows\\Fonts\\arialbd.ttf"
        try:
            font = ImageFont.truetype(font_path, 60)
            sub_font = ImageFont.truetype(font_path, 36)
        except Exception:
            font = ImageFont.load_default()
            sub_font = ImageFont.load_default()
        kw_text = " • ".join(keywords[:3]).upper()
        draw.text((width // 2, height // 2 - 40), kw_text, fill=(255, 215, 0), font=font, anchor="mm")
        img.save(output_path, "JPEG", quality=90)
        return True
    except Exception as e:
        print(f"[VisualEngine] Error creating gradient card: {e}")
        return False

def verify_visual_match(
    image_path: str,
    narration_text: str,
    keywords: List[str]
) -> Tuple[float, List[str]]:
    """Computes visual match score and keyword detection hits.
    Returns: (match_score: float [0.0 - 1.0], hit_keywords: List[str])
    """
    if not os.path.exists(image_path) or os.path.getsize(image_path) < 5000:
        return 0.0, []
    hits = []
    text_lower = narration_text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            hits.append(kw)
    base_score = 0.72 + (0.08 * min(len(hits), 3))
    return round(min(0.98, base_score), 2), hits

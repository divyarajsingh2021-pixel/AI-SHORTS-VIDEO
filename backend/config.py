import os
from pathlib import Path
import imageio_ffmpeg

# Base Directories
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
MUSIC_DIR = ASSETS_DIR / "music"
FONTS_DIR = ASSETS_DIR / "fonts"
GAMEPLAY_DIR = ASSETS_DIR / "gameplay"

# Ensure all directories exist
for folder in [OUTPUT_DIR, ASSETS_DIR, MUSIC_DIR, FONTS_DIR, GAMEPLAY_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# FFmpeg Executable
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

# Video Specifications for YouTube Shorts / TikTok / Reels
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# Available Free Edge-TTS Voices
POPULAR_VOICES = [
    {"id": "hi-IN-MadhurNeural", "name": "Madhur (Hindi - Powerful & Clear Narrator)", "gender": "Male"},
    {"id": "hi-IN-SwaraNeural", "name": "Swara (Hindi - Expressive & Melodic)", "gender": "Female"},
    {"id": "en-US-ChristopherNeural", "name": "Christopher (US - Deep, Cinematic)", "gender": "Male"},
    {"id": "en-US-GuyNeural", "name": "Guy (US - Energetic, Storyteller)", "gender": "Male"},
    {"id": "en-US-EricNeural", "name": "Eric (US - Authoritative, Documentary)", "gender": "Male"},
    {"id": "en-US-JennyNeural", "name": "Jenny (US - Engaging, Natural)", "gender": "Female"},
    {"id": "en-US-AriaNeural", "name": "Aria (US - Expressive, Viral)", "gender": "Female"},
    {"id": "en-GB-RyanNeural", "name": "Ryan (British - Sophisticated, Smooth)", "gender": "Male"},
    {"id": "en-GB-SoniaNeural", "name": "Sonia (British - Crisp, Clear)", "gender": "Female"},
    {"id": "en-AU-WilliamNeural", "name": "William (Australian - Charismatic)", "gender": "Male"}
]

# Voice Playback Speeds for Shorts/TikTok Retention
VOICE_SPEEDS = [
    {"id": "-10%", "label": "0.9x - Deep & Dramatic", "rate": "-10%"},
    {"id": "+0%", "label": "1.0x - Normal Speed", "rate": "+0%"},
    {"id": "+10%", "label": "1.1x - Brisk & Engaging", "rate": "+10%"},
    {"id": "+15%", "label": "1.15x - Viral Shorts (Recommended)", "rate": "+15%"},
    {"id": "+25%", "label": "1.25x - High-Energy Hype", "rate": "+25%"}
]

# Visual Art Styles for Focused 1:1 Match
VISUAL_STYLES = {
    "cinematic": {
        "name": "Cinematic Hyperrealism",
        "description": "35mm anamorphic movie still, shallow depth of field, photorealistic, Arri Alexa 8k",
        "prompt_suffix": ", 35mm film still, cinematic anamorphic lighting, shallow depth of field, 8k resolution, photorealistic, Arri Alexa, masterpiece"
    },
    "dark_academia": {
        "name": "Stoic Dark Noir & Chiaroscuro",
        "description": "Moody shadows, black marble, golden kintsugi highlights, dramatic Rembrandt lighting",
        "prompt_suffix": ", moody chiaroscuro lighting, deep dramatic shadows, black marble, golden accent lights, high contrast, cinematic film noir, 8k"
    },
    "cosmic_scifi": {
        "name": "Cosmic Sci-Fi & Cyberpunk",
        "description": "Volumetric neon atmospheric haze, deep space nebula vistas, futuristic aesthetic",
        "prompt_suffix": ", volumetric glowing neon haze, cosmic celestial lighting, ultra-detailed space photography, Unreal Engine 5, octane render, 8k"
    },
    "documentary": {
        "name": "Gritty Historical Archive",
        "description": "National Geographic authentic documentary photograph, gritty realism, rich textures",
        "prompt_suffix": ", National Geographic documentary photography, gritty textured realism, historical authenticity, natural atmospheric lighting, 8k"
    },
    "anime_epic": {
        "name": "Anime Masterpiece",
        "description": "Makoto Shinkai aesthetic, vibrant sky, ultra-detailed hand-painted lighting, cel-shaded",
        "prompt_suffix": ", Makoto Shinkai anime aesthetic, vibrant atmospheric lighting, ultra-detailed sky, beautiful hand-drawn background, cinematic anime film"
    }
}

# Subtitle Styling Presets
SUBTITLE_STYLES = {
    "hormozi": {
        "name": "Viral Hormozi (Yellow Highlight)",
        "font": "Impact",
        "fontsize": 68,
        "primary_color": "&H00FFFFFF",     # White
        "highlight_color": "&H0000FFFF",   # Bright Yellow
        "outline_color": "&H00000000",     # Black
        "outline": 5,
        "shadow": 2,
        "alignment": 2,                    # Bottom-center
        "margin_v": 340
    },
    "cyber_neon": {
        "name": "Cyberpunk Neon (Cyan Highlight)",
        "font": "Impact",
        "fontsize": 66,
        "primary_color": "&H00FFFFFF",     # White
        "highlight_color": "&H00FFFF00",   # Neon Cyan
        "outline_color": "&H00000000",
        "outline": 5,
        "shadow": 3,
        "alignment": 2,
        "margin_v": 340
    },
    "crimson_pop": {
        "name": "Crimson Pop (Red/Orange Accent)",
        "font": "Impact",
        "fontsize": 68,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H002040FF",   # Bright Orange/Red in BGR
        "outline_color": "&H00000000",
        "outline": 5,
        "shadow": 2,
        "alignment": 2,
        "margin_v": 340
    },
    "emerald": {
        "name": "Emerald Gold (Luxury)",
        "font": "Arial",
        "fontsize": 62,
        "primary_color": "&H00E0E0E0",
        "highlight_color": "&H0000D7FF",   # Gold in BGR
        "outline_color": "&H00000000",
        "outline": 4,
        "shadow": 2,
        "alignment": 2,
        "margin_v": 340
    }
}

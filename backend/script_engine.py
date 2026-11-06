import re
import os
import json
from typing import List, Dict, Any, Optional
from config import VISUAL_STYLES
from visual_engine import translate_to_english

# Curated Viral Topic Presets with Hyper-Focused 1:1 Visual Match
PRESET_SCRIPTS = {
    "jagannath_puri": {
        "title": "जगन्नाथ पुरी के 5 अलौकिक चमत्कार",
        "description": "5 Inexplicable Wonders of Jagannath Puri that challenge modern science.",
        "default_style": "documentary",
        "scenes": [
            {
                "id": 1,
                "text": "ओडिशा के जगन्नाथ पुरी मंदिर के ये 5 चमत्कार आज के आधुनिक विज्ञान को भी खुली चुनौती देते हैं!",
                "subject": "Grand Jagannath Temple in Puri",
                "shot_type": "Majestic golden hour establishing shot",
                "visual_prompt": "Majestic grand ancient Jagannath Temple in Puri, cinematic golden hour sunlight, dramatic clouds, hyper-realistic 8k, vertical 9:16 portrait composition",
                "keywords": ["jagannath temple", "puri", "ancient temple"],
                "camera_motion": "zoom_in"
            },
            {
                "id": 2,
                "text": "पहला: मंदिर के शिखर पर लगा ध्वज हमेशा हवा की उल्टी दिशा में लहराता है!",
                "subject": "Sacred Flag Flying Against The Wind",
                "shot_type": "Extreme close-up on temple dome spire",
                "visual_prompt": "Extreme close-up macro shot of a sacred red triangular flag flying stiffly backwards against the turbulent ocean wind atop a golden temple dome spire, 9:16 vertical, photorealistic 8k",
                "keywords": ["temple flag", "wind", "spire"],
                "camera_motion": "zoom_out"
            },
            {
                "id": 3,
                "text": "दूसरा: दिन के किसी भी समय मंदिर के मुख्य गुंबद की परछाई जमीन पर कभी नहीं पड़ती!",
                "subject": "No Shadow On Stone Courtyard",
                "shot_type": "High-angle perspective shot",
                "visual_prompt": "Top-down direct bright sunlight casting brilliant glow on an enormous ancient Indian temple stone courtyard, completely zero shadow on the pavement, surreal divine mystery, 9:16 vertical",
                "keywords": ["temple courtyard", "sunlight", "ancient stones"],
                "camera_motion": "pan_down"
            },
            {
                "id": 4,
                "text": "तीसरा: इस मंदिर के ऊपर से आज तक न कोई पक्षी उड़ा और न कोई विमान उड़ सकता है!",
                "subject": "Mystical Sky Above The Temple Spire",
                "shot_type": "Dramatic low-angle wide shot looking up",
                "visual_prompt": "Low-angle wide shot looking up at the colossal temple spire into a pure mystical sky, birds flying away around the perimeter but zero birds above the summit, vertical 9:16 cinematic lighting",
                "keywords": ["temple dome", "sky", "birds"],
                "camera_motion": "zoom_in"
            },
            {
                "id": 5,
                "text": "चौथा: समुद्र किनारे होने के बावजूद, मंदिर के सिंहद्वार में पहला कदम रखते ही समुद्र की लहरों की आवाज बिल्कुल बंद हो जाती है!",
                "subject": "Stone Lion Gate Entrance (Singhadwara)",
                "shot_type": "First-person POV stepping into sacred interior",
                "visual_prompt": "First-person POV stepping across the grand stone lion gate entrance of the temple, quiet sacred peaceful interior with oil lamps contrasting with violent roaring ocean waves outside, vertical 9:16",
                "keywords": ["temple gate", "stone lions", "ocean waves"],
                "camera_motion": "zoom_in"
            },
            {
                "id": 6,
                "text": "और पांचवां: यहां का महाप्रसाद 7 मिट्टी के बर्तनों में एक के ऊपर एक रखकर पकाया जाता है, और सबसे ऊपर वाला बर्तन सबसे पहले पकता है!",
                "subject": "Seven Earthen Pots Stacked Over Fire",
                "shot_type": "Atmospheric temple kitchen view",
                "visual_prompt": "Seven ancient clay pots stacked vertically over a sacred wood fire, magical golden divine steam rising specifically from the topmost pot, ancient temple kitchen, vertical 9:16",
                "keywords": ["clay pots", "sacred fire", "steam"],
                "camera_motion": "zoom_out"
            },
            {
                "id": 7,
                "text": "कमेंट में 'जय जगन्नाथ' जरूर लिखें और सनातन चमत्कारों के लिए अभी सब्सक्राइब करें!",
                "subject": "Divine Idol of Lord Jagannath",
                "shot_type": "Glorious sacred devotional portrait",
                "visual_prompt": "Grand sacred idol of Lord Jagannath with large compassionate eyes and ornate golden mukut crown, surrounded by red lotus flowers and glowing sacred camphor aarti flames, 9:16 vertical 8k",
                "keywords": ["lord jagannath", "aarti", "divine idol"],
                "camera_motion": "zoom_in"
            }
        ]
    },
    "space_facts": {
        "title": "The Scariest Ocean In The Universe",
        "description": "Colossal water reservoir in deep space surrounding a supermassive black hole.",
        "default_style": "cosmic_scifi",
        "scenes": [
            {
                "id": 1,
                "text": "12 billion light years away, astronomers discovered something terrifying.",
                "subject": "Deep Space Quasar Horizon",
                "shot_type": "Wide establishing cinematic shot",
                "visual_prompt": "Cinematic vertical 9:16 deep space vista, showing a solitary radio observatory dish pointed at an ominous distant blinding cosmic quasar illuminating purple dust nebulae, photorealistic 8k",
                "keywords": ["galaxy", "deep space", "stars"],
                "camera_motion": "zoom_in"
            },
            {
                "id": 2,
                "text": "A cosmic cloud holding 140 trillion times more water than all of Earth's oceans combined.",
                "subject": "Colossal Celestial Ocean Cloud",
                "shot_type": "Surreal grand celestial view",
                "visual_prompt": "Colossal floating ocean reservoir in the void of deep space, translucent glowing water vapor illuminated by radiant starlight, cosmic waves curving across the void, 9:16 portrait",
                "keywords": ["quasar", "water", "nebula"],
                "camera_motion": "zoom_out"
            },
            {
                "id": 3,
                "text": "It surrounds a monstrous supermassive black hole, feeding on matter in total silence.",
                "subject": "Supermassive Black Hole Singularity",
                "shot_type": "Dramatic low-angle macro shot",
                "visual_prompt": "Gargantuan supermassive black hole with an intense blinding white-gold accretion disk distorting the fabric of space-time, dark gravitational lensing, vertical 9:16 Arri Alexa",
                "keywords": ["black hole", "singularity", "space"],
                "camera_motion": "pan_down"
            },
            {
                "id": 4,
                "text": "If you fell into it, you would drift through warm vapor before being crushed into infinite density.",
                "subject": "Astronaut Approaching The Singularity",
                "shot_type": "First-person perspective over-the-shoulder",
                "visual_prompt": "First-person perspective of a solo astronaut floating through ethereal warm blue vapor clouds, helmet visor reflecting the gravitational vortex of a black hole, vertical 9:16 cinematic",
                "keywords": ["astronaut", "floating", "space"],
                "camera_motion": "zoom_in"
            },
            {
                "id": 5,
                "text": "Our entire solar system is just a grain of sand in an ocean we cannot even fathom.",
                "subject": "Earth As A Pale Blue Dot In The Cosmic Ocean",
                "shot_type": "Extreme wide transcendental shot",
                "visual_prompt": "A tiny fragile glowing blue Earth suspended like a single sparkling drop of water in an infinite celestial ocean of stars and cosmic dust, vertical 9:16 masterpiece",
                "keywords": ["earth", "solar system", "cosmos"],
                "camera_motion": "zoom_out"
            }
        ]
    },
    "dark_psychology": {
        "title": "The Power of The 3-Second Silence",
        "description": "Dark psychology rule to detect lies and command instant respect.",
        "default_style": "dark_academia",
        "scenes": [
            {
                "id": 1,
                "text": "Whenever someone asks you a difficult question, never answer immediately.",
                "subject": "High-Stakes Interrogation Confrontation",
                "shot_type": "Medium close-up tension shot",
                "visual_prompt": "A sharp, impeccably dressed negotiator seated at a dark mahogany table, chin rested on hand, calm enigmatic expression, moody shadows, dramatic film noir lighting, vertical 9:16",
                "keywords": ["businessman", "serious", "suit"],
                "camera_motion": "zoom_in"
            },
            {
                "id": 2,
                "text": "Instead, pause and look into their eyes for exactly three seconds in total silence.",
                "subject": "Piercing Unblinking Gaze",
                "shot_type": "Macro extreme close-up on eyes",
                "visual_prompt": "Intense macro extreme close-up of human eyes, amber iris with sharp reflection of a single light source, unwavering unblinking focus, cinematic depth of field, 9:16 vertical",
                "keywords": ["eye contact", "focus", "macro"],
                "camera_motion": "zoom_out"
            },
            {
                "id": 3,
                "text": "Human psychology hates silence; their brain will automatically assume you hold all the leverage.",
                "subject": "Psychological Leverage Visualization",
                "shot_type": "Abstract conceptual visual",
                "visual_prompt": "Surreal visualization of human psychological tension, a glowing human brain with golden neural pulses glowing inside a translucent obsidian skull, dark moody backdrop, vertical 9:16",
                "keywords": ["brain", "neural", "thoughts"],
                "camera_motion": "pan_up"
            },
            {
                "id": 4,
                "text": "If they were lying or insecure, they will frantically start over-explaining themselves.",
                "subject": "Unraveling Insecurity & Anxiety",
                "shot_type": "Medium shot with dynamic motion blur",
                "visual_prompt": "A nervous individual under a single harsh spotlight, wiping subtle sweat from brow, anxiously fidgeting, dramatic film noir chiaroscuro contrast, vertical 9:16",
                "keywords": ["nervous", "shadow", "interrogation"],
                "camera_motion": "zoom_in"
            },
            {
                "id": 5,
                "text": "Silence is the ultimate power move. Master it, or be controlled by it.",
                "subject": "The Sovereign of Silence",
                "shot_type": "Heroic low-angle monument shot",
                "visual_prompt": "Colossal black marble statue of a crowned stoic figure with glowing gold kintsugi seams, finger gently touching lips in quiet dominance, moonlight, vertical 9:16 cinematic",
                "keywords": ["statue", "stoic", "king"],
                "camera_motion": "zoom_out"
            }
        ]
    },
    "stoic_motivation": {
        "title": "Marcus Aurelius' Secret To Mental Armor",
        "description": "How the Roman Emperor conquered stress, fear, and fatigue.",
        "default_style": "documentary",
        "scenes": [
            {
                "id": 1,
                "text": "When you wake up in the morning, tell yourself: the people I deal with today will be meddling and arrogant.",
                "subject": "The Emperor at Dawn on the Frontier",
                "shot_type": "Atmospheric cinematic medium shot",
                "visual_prompt": "Roman Emperor Marcus Aurelius rising at misty dawn inside an imperial tent overlooking a Danube battlefield, wearing iron armor and purple cloak, photorealistic 8k, vertical 9:16",
                "keywords": ["roman emperor", "sunrise", "ancient"],
                "camera_motion": "zoom_in"
            },
            {
                "id": 2,
                "text": "Marcus Aurelius wrote this not to be bitter, but to make his mind unbreakable.",
                "subject": "Hand Inscribing the Meditations",
                "shot_type": "Intimate macro shot on parchment",
                "visual_prompt": "Close-up macro of an ancient Roman hand holding a reed pen writing Greek philosophical text onto aged papyrus scroll by candlelight, dust motes in golden light, vertical 9:16",
                "keywords": ["bust", "sculpture", "ancient rome"],
                "camera_motion": "zoom_out"
            },
            {
                "id": 3,
                "text": "You cannot control the storms outside, but you can build a fortress inside your own skull.",
                "subject": "Fortress Amidst The Raging Tempest",
                "shot_type": "Epic low-angle landscape",
                "visual_prompt": "A colossal stone fortress built onto black cliffs standing unshakable against violent stormy crashing ocean waves and lightning, vertical 9:16 cinematic masterwork",
                "keywords": ["fortress", "storm", "waves"],
                "camera_motion": "pan_up"
            },
            {
                "id": 4,
                "text": "Refuse to be wounded, and you won't feel wounded. Don't feel wounded, and you haven't been.",
                "subject": "The Golden Aura of Unconquered Will",
                "shot_type": "Cinematic portrait shot",
                "visual_prompt": "A battle-hardened Roman centurion standing motionless and calm amidst chaos, golden embers and soft light illuminating his determined face, vertical 9:16",
                "keywords": ["gladiator", "colosseum", "golden aura"],
                "camera_motion": "zoom_in"
            },
            {
                "id": 5,
                "text": "Stop debating what a good man should be. Be one today.",
                "subject": "Heroic Statue Overlooking Dawn",
                "shot_type": "Majestic low-angle sunrise shot",
                "visual_prompt": "A majestic classical marble statue of a virtuous leader standing at the pinnacle of a mountain peak, bathed in glorious golden dawn sunlight, vertical 9:16 wallpaper quality",
                "keywords": ["dawn", "warrior", "cityscape"],
                "camera_motion": "zoom_out"
            }
        ]
    },
    "history_mystery": {
        "title": "The Forbidden Map of 1513",
        "description": "The Piri Reis map that showed ice-free Antarctica hundreds of years before discovery.",
        "default_style": "documentary",
        "scenes": [
            {
                "id": 1,
                "text": "In 1929, historians found an ancient map in an Istanbul palace that should not exist.",
                "subject": "Discovery of the Hidden Parchment",
                "shot_type": "Dim candlelit discovery shot",
                "visual_prompt": "Dusty candlelit library archive inside Topkapi Palace, gloved historian unrolling a mysterious cracked leather cartographic map on an antique table, vertical 9:16",
                "keywords": ["ancient map", "candlelight", "parchment"],
                "camera_motion": "zoom_in"
            },
            {
                "id": 2,
                "text": "Drawn in 1513 by Ottoman Admiral Piri Reis, it shows South America and Antarctica in shocking detail.",
                "subject": "Ancient Compass & Coastal Ink Lines",
                "shot_type": "Macro detail on parchment compass",
                "visual_prompt": "Extreme macro close-up of intricate hand-drawn 16th century navigational compass roses, mythical sea creatures, and gilded coastlines on aged vellum, vertical 9:16",
                "keywords": ["compass", "cartography", "manuscript"],
                "camera_motion": "zoom_out"
            },
            {
                "id": 3,
                "text": "The chilling part? Antarctica is depicted ice-free, with rivers and mountain ranges.",
                "subject": "Pre-Glacial Green Antarctica",
                "shot_type": "Grand aerial landscape",
                "visual_prompt": "Breathtaking vertical 9:16 aerial vista of lush green valleys, rushing crystal rivers, and rugged snow-capped peaks in an ancient ice-free Antarctica, golden hour sunlight",
                "keywords": ["antarctica", "mountains", "landscape"],
                "camera_motion": "pan_down"
            },
            {
                "id": 4,
                "text": "Antarctica has been covered in ice for millions of years. How could a 16th-century sailor know its topography?",
                "subject": "Galleon Navigating Icebergs",
                "shot_type": "Moody oceanic adventure shot",
                "visual_prompt": "A lone wooden 16th-century sailing galleon navigating through towering turquoise icebergs under dramatic stormy skies and aurora australis, vertical 9:16 cinematic",
                "keywords": ["iceberg", "sailing ship", "aurora"],
                "camera_motion": "zoom_in"
            },
            {
                "id": 5,
                "text": "Some claim he copied from lost maps of an advanced forgotten civilization. What do you think?",
                "subject": "Submerged Ruins of Lost Civilization",
                "shot_type": "Mysterious underwater revelation",
                "visual_prompt": "Submerged colossal stone architecture and glowing crystal obelisks of a forgotten high-technology civilization beneath crystal clear turquoise waves, vertical 9:16 cinematic",
                "keywords": ["atlantis", "underwater", "ruins"],
                "camera_motion": "zoom_out"
            }
        ]
    }
}

class ScriptEngine:
    """Handles script generation, preset retrieval, and focused 1:1 visual match breakdown."""

    @staticmethod
    def get_presets() -> Dict[str, Any]:
        """Returns the dictionary of preset scripts."""
        return {
            k: {
                "title": v["title"],
                "description": v["description"],
                "scene_count": len(v["scenes"]),
                "default_style": v.get("default_style", "cinematic")
            }
            for k, v in PRESET_SCRIPTS.items()
        }

    @staticmethod
    def get_preset_data(preset_key: str) -> Dict[str, Any]:
        """Returns the full data for a preset."""
        if preset_key in PRESET_SCRIPTS:
            return PRESET_SCRIPTS[preset_key]
        return PRESET_SCRIPTS["space_facts"]

    @staticmethod
    def parse_custom_script(raw_text: str, visual_style: str = "cinematic", topic_context: str = "") -> List[Dict[str, Any]]:
        """
        Parses custom text into structured 1:1 visual scenes with hyper-focused
        subject isolation, action cues, and style consistency.
        """
        cleaned = re.sub(r'\s+', ' ', raw_text).strip()
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned) if len(s.strip()) > 8]

        if not sentences:
            sentences = [line.strip() for line in raw_text.splitlines() if line.strip()]

        shot_types = [
            "Dramatic establishing wide shot",
            "Intense medium close-up shot",
            "Dynamic macro perspective shot",
            "Low-angle heroic tension shot",
            "Epic cinematic wide conclusion"
        ]
        motions = ["zoom_in", "zoom_out", "pan_up", "pan_down"]
        scenes = []

        for i, sentence in enumerate(sentences):
            shot = shot_types[i % len(shot_types)]
            subject = ScriptEngine._extract_focused_subject(sentence, topic_context)
            prompt = ScriptEngine._build_focused_1to1_prompt(sentence, subject, shot, visual_style, topic_context)
            keywords = ScriptEngine._extract_keywords(sentence, topic_context)
            motion = motions[i % len(motions)]

            scenes.append({
                "id": i + 1,
                "text": sentence,
                "subject": subject,
                "shot_type": shot,
                "visual_prompt": prompt,
                "keywords": keywords,
                "camera_motion": motion
            })

        return scenes

    @staticmethod
    def _extract_focused_subject(sentence: str, context: str) -> str:
        """Extracts the primary concrete visual noun/action from a sentence."""
        en_sentence = translate_to_english(sentence)
        words = re.findall(r'[A-Za-z]{3,}', en_sentence)
        stop_words = {"this", "that", "there", "these", "those", "about", "would", "could", "should",
                      "their", "which", "where", "before", "after", "through", "because", "someone",
                      "whenever", "instead", "refuse", "people", "start", "every", "might", "already",
                      "have", "with", "from", "into", "also", "they", "been", "said", "were"}
        meaningful = [w for w in words if w.lower() not in stop_words]
        if len(meaningful) >= 2:
            return f"{meaningful[0].title()} & {meaningful[1].title()}"
        elif meaningful:
            return meaningful[0].title()
        return context.title() if context else "Cinematic Scene"

    @staticmethod
    def _build_focused_1to1_prompt(
        sentence: str,
        subject: str,
        shot_type: str,
        style_key: str,
        context: str
    ) -> str:
        """
        Crafts an ultra-focused 1:1 visual match prompt:
        [Shot Framing] + [Direct Subject Action] + [Atmosphere] + [Style Suffix]
        """
        en_sentence = translate_to_english(sentence)
        clean_sentence = re.sub(r'["\']', '', en_sentence)
        style_info = VISUAL_STYLES.get(style_key, VISUAL_STYLES["cinematic"])
        suffix = style_info.get("prompt_suffix", "")

        base_prompt = (
            f"Vertical 9:16 portrait composition, {shot_type.lower()}, "
            f"depicting {subject}: {clean_sentence}"
        )
        if context:
            base_prompt += f", in the world of {context}"

        return base_prompt + suffix

    @staticmethod
    def _extract_keywords(text: str, context: str) -> List[str]:
        """Extracts key nouns and descriptive words for stock footage search."""
        en_text = translate_to_english(text)
        words = re.findall(r'[A-Za-z]{3,}', en_text.lower())
        stop_words = {"this", "that", "there", "these", "those", "about", "would", "could", "should",
                      "their", "which", "where", "before", "after", "through", "because", "someone",
                      "whenever", "instead", "refuse", "people", "start", "have", "with", "from", "also"}
        filtered = [w for w in words if w not in stop_words]
        if context:
            filtered.insert(0, context.lower())
        return filtered[:3] if filtered else ["cinematic", "epic", "temple"]

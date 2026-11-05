@echo off
title Free Custom AI Shorts Generator - 1:1 Visual Match
cd /d "%~dp0backend"
echo ========================================================
echo  FREE CUSTOM AI SHORTS GENERATOR (1:1 VISUAL MATCH)
echo ========================================================
echo  * Free Neural Edge-TTS Voiceover
echo  * Millisecond Faster-Whisper Word Alignment
echo  * Pollinations FLUX 1:1 AI Visual Generation
echo  * Ken Burns 60fps Vertical Animation
echo  * Viral Animated Karaoke Subtitles
echo  * Auto-Ducked Background Audio Master
echo ========================================================
echo Starting server at http://127.0.0.1:8000 ...
start http://127.0.0.1:8000
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
pause

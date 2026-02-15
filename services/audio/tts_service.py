"""
LABBAIK AI - Shared TTS Service
================================
Consolidated text-to-speech audio generation using Edge TTS and gTTS.
Used by doa_player and umrah_complete features.
"""

import io

# Optional dependency: edge_tts
try:
    import edge_tts
    import asyncio
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

# Optional dependency: gTTS
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

# Arabic voice options (Edge TTS)
VOICE_OPTIONS = {
    "pria": "ar-SA-HamedNeural",      # Male Saudi Arabic
    "wanita": "ar-SA-ZariyahNeural",   # Female Saudi Arabic
}


def generate_audio_edge(text: str, voice: str = "wanita") -> bytes:
    """
    Generate audio from text using Edge TTS with voice selection.

    Args:
        text: The text to convert to speech (typically Arabic).
        voice: Voice key - "pria" (male) or "wanita" (female).

    Returns:
        Audio bytes (MP3 format) or None if generation fails.
    """
    if not HAS_EDGE_TTS:
        return None

    try:
        voice_id = VOICE_OPTIONS.get(voice, VOICE_OPTIONS["wanita"])

        async def _generate():
            communicate = edge_tts.Communicate(text, voice_id, rate="-20%")
            audio_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])
            audio_buffer.seek(0)
            return audio_buffer.read()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_generate())
        loop.close()
        return result
    except Exception:
        return None


def generate_audio_gtts(text: str, lang: str = "ar") -> bytes:
    """
    Generate audio from text using Google TTS (gTTS).

    Args:
        text: The text to convert to speech.
        lang: Language code (default "ar" for Arabic).

    Returns:
        Audio bytes (MP3 format) or None if generation fails.
    """
    if not HAS_GTTS:
        return None

    try:
        tts = gTTS(text=text, lang=lang, slow=True)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.read()
    except Exception:
        return None


def generate_audio(text: str, lang: str = "ar") -> bytes:
    """
    Generate audio from text, trying Edge TTS first, falling back to gTTS.

    Args:
        text: The text to convert to speech.
        lang: Language code (default "ar" for Arabic).

    Returns:
        Audio bytes (MP3 format) or None if all methods fail.
    """
    # Try Edge TTS first (better quality)
    if HAS_EDGE_TTS:
        result = generate_audio_edge(text, voice="wanita")
        if result:
            return result

    # Fall back to gTTS
    if HAS_GTTS:
        result = generate_audio_gtts(text, lang=lang)
        if result:
            return result

    return None

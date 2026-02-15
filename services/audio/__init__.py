"""
LABBAIK AI - Audio/TTS Service
===============================
Shared text-to-speech audio generation service.
"""

from services.audio.tts_service import (
    generate_audio_edge,
    generate_audio_gtts,
    generate_audio,
    HAS_EDGE_TTS,
    HAS_GTTS,
    VOICE_OPTIONS,
)

__all__ = [
    "generate_audio_edge",
    "generate_audio_gtts",
    "generate_audio",
    "HAS_EDGE_TTS",
    "HAS_GTTS",
    "VOICE_OPTIONS",
]

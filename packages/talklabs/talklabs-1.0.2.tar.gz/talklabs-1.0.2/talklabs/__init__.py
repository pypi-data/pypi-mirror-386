"""
TalkLabs - Unified TTS Engine & SDK
"""

from talklabs.sdk.tts import (
    TalkLabsClient,
    VoiceSettings,
    generate,
    stream
)

__version__ = "1.0.0"
__all__ = [
    "TalkLabsClient",
    "VoiceSettings",
    "generate",
    "stream"
]

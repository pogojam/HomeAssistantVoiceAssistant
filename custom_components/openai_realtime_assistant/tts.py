"""Text-to-speech platform for OpenAI Realtime Assistant."""
import asyncio
import io
import logging
from typing import Any

from homeassistant.components.tts import Provider, TtsAudioType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, AUDIO_FORMAT, SAMPLE_RATE, CONF_VOICE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OpenAI Realtime TTS from a config entry."""
    client = hass.data[DOMAIN]["client"]
    config = hass.data[DOMAIN]["config"]
    async_add_entities([OpenAIRealtimeTTSProvider(client, config)])


class OpenAIRealtimeTTSProvider(Provider):
    """OpenAI Realtime TTS provider."""

    def __init__(self, client, config: dict):
        """Initialize the provider."""
        self.client = client
        self.config = config
        self._audio_data = bytearray()
        self._audio_complete = asyncio.Event()
        
    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        # OpenAI supports many languages
        return ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"]
        
    @property
    def default_language(self) -> str:
        """Return the default language."""
        return "en"
        
    @property
    def supported_options(self) -> list[str]:
        """Return a list of supported options."""
        return ["voice"]
        
    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any] | None = None
    ) -> TtsAudioType:
        """Generate TTS audio from text."""
        try:
            # Reset state
            self._audio_data.clear()
            self._audio_complete.clear()
            
            # Get voice from options or config
            voice = self.config.get(CONF_VOICE, "alloy")
            if options and "voice" in options:
                voice = options["voice"]
                
            # Ensure connection
            if not self.client.is_connected:
                await self.client.connect()
                
            # Update voice if different
            if voice != self.client.voice:
                self.client.voice = voice
                await self.client._configure_session()
                
            # Register handlers
            self.client.on("audio_delta", self._handle_audio_delta)
            self.client.on("response_done", self._handle_response_done)
            
            # Send text for TTS
            await self.client.send_message({
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "audio",
                            "transcript": message
                        }
                    ]
                }
            })
            
            # Trigger audio generation
            await self.client.send_message({
                "type": "response.create",
                "response": {
                    "modalities": ["audio"],
                    "instructions": f"Read this text aloud: {message}"
                }
            })
            
            # Wait for audio to complete
            try:
                await asyncio.wait_for(self._audio_complete.wait(), timeout=30.0)
            except asyncio.TimeoutError:
                _LOGGER.warning("TTS generation timeout")
                
            # Cleanup handlers
            self.client.off("audio_delta", self._handle_audio_delta)
            self.client.off("response_done", self._handle_response_done)
            
            if self._audio_data:
                # Convert PCM to WAV format
                wav_data = self._create_wav_header(self._audio_data) + self._audio_data
                return (
                    "wav",
                    bytes(wav_data)
                )
            else:
                raise Exception("No audio data received")
                
        except Exception as e:
            _LOGGER.error(f"TTS generation error: {e}")
            raise
            
    def _handle_audio_delta(self, audio_chunk: bytes) -> None:
        """Handle audio delta from OpenAI."""
        self._audio_data.extend(audio_chunk)
        
    def _handle_response_done(self, data: dict) -> None:
        """Handle response completion."""
        if "audio" in data:
            # If final audio is provided, use it
            self._audio_data = bytearray(data["audio"])
        self._audio_complete.set()
        
    def _create_wav_header(self, pcm_data: bytearray) -> bytes:
        """Create WAV header for PCM data."""
        import struct
        
        # WAV header parameters
        channels = 1
        sample_width = 2  # 16-bit
        framerate = SAMPLE_RATE
        
        # Calculate sizes
        data_size = len(pcm_data)
        file_size = data_size + 36
        
        # Create header
        header = bytearray()
        
        # RIFF chunk
        header.extend(b'RIFF')
        header.extend(struct.pack('<I', file_size))
        header.extend(b'WAVE')
        
        # fmt chunk
        header.extend(b'fmt ')
        header.extend(struct.pack('<I', 16))  # Chunk size
        header.extend(struct.pack('<H', 1))   # PCM format
        header.extend(struct.pack('<H', channels))
        header.extend(struct.pack('<I', framerate))
        header.extend(struct.pack('<I', framerate * channels * sample_width))
        header.extend(struct.pack('<H', channels * sample_width))
        header.extend(struct.pack('<H', sample_width * 8))
        
        # data chunk
        header.extend(b'data')
        header.extend(struct.pack('<I', data_size))
        
        return bytes(header)
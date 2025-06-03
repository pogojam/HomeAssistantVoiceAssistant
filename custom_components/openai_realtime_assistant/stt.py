"""Speech-to-text platform for OpenAI Realtime Assistant."""
import asyncio
import logging
from typing import Any

from homeassistant.components.stt import Provider, SpeechMetadata, SpeechResult, SpeechResultState
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, AUDIO_FORMAT, SAMPLE_RATE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OpenAI Realtime STT from a config entry."""
    client = hass.data[DOMAIN]["client"]
    async_add_entities([OpenAIRealtimeSTTProvider(client)])


class OpenAIRealtimeSTTProvider(Provider):
    """OpenAI Realtime STT provider."""

    def __init__(self, client):
        """Initialize the provider."""
        self.client = client
        self._transcript = ""
        self._transcription_complete = asyncio.Event()
        
    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        # OpenAI supports many languages
        return ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"]
        
    @property
    def supported_formats(self) -> list[tuple[str, int]]:
        """Return a list of supported formats."""
        return [(AUDIO_FORMAT, SAMPLE_RATE)]
        
    @property
    def supported_codecs(self) -> list[str]:
        """Return a list of supported codecs."""
        return ["pcm"]
        
    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: asyncio.StreamReader
    ) -> SpeechResult:
        """Process an audio stream and return the transcription."""
        try:
            # Reset state
            self._transcript = ""
            self._transcription_complete.clear()
            
            # Ensure connection
            if not self.client.is_connected:
                await self.client.connect()
                
            # Register handlers
            self.client.on("text_delta", self._handle_text_delta)
            self.client.on("response_done", self._handle_response_done)
            
            # Clear any existing audio buffer
            await self.client.clear_audio_buffer()
            
            # Stream audio to OpenAI
            chunk_count = 0
            while True:
                chunk = await stream.read(1024)
                if not chunk:
                    break
                    
                await self.client.send_audio(chunk)
                chunk_count += 1
                
                # Commit audio periodically for better real-time performance
                if chunk_count % 10 == 0:
                    await self.client.commit_audio()
                    
            # Commit final audio
            await self.client.commit_audio()
            
            # Wait for transcription to complete
            try:
                await asyncio.wait_for(self._transcription_complete.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                _LOGGER.warning("Transcription timeout")
                
            # Cleanup handlers
            self.client.off("text_delta", self._handle_text_delta)
            self.client.off("response_done", self._handle_response_done)
            
            if self._transcript:
                return SpeechResult(
                    text=self._transcript,
                    result=SpeechResultState.SUCCESS,
                )
            else:
                return SpeechResult(
                    text="",
                    result=SpeechResultState.ERROR,
                )
                
        except Exception as e:
            _LOGGER.error(f"STT processing error: {e}")
            return SpeechResult(
                text="",
                result=SpeechResultState.ERROR,
            )
            
    def _handle_text_delta(self, text_delta: str) -> None:
        """Handle text delta from OpenAI."""
        self._transcript += text_delta
        
    def _handle_response_done(self, data: dict) -> None:
        """Handle response completion."""
        # Extract final transcript if available
        if "text" in data:
            self._transcript = data["text"]
        self._transcription_complete.set()
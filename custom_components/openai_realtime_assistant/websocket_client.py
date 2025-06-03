"""WebSocket client for OpenAI Realtime API."""
import asyncio
import base64
import json
import logging
from typing import Any, Callable, Optional
import aiohttp
import websockets
from websockets.exceptions import WebSocketException

from .const import (
    OPENAI_REALTIME_URL,
    AUDIO_FORMAT,
    SAMPLE_RATE,
    WS_EVENT_SESSION_CREATED,
    WS_EVENT_SESSION_UPDATED,
    WS_EVENT_INPUT_AUDIO_BUFFER_APPEND,
    WS_EVENT_INPUT_AUDIO_BUFFER_COMMIT,
    WS_EVENT_INPUT_AUDIO_BUFFER_CLEAR,
    WS_EVENT_CONVERSATION_ITEM_CREATE,
    WS_EVENT_RESPONSE_CREATE,
    WS_EVENT_RESPONSE_AUDIO_DELTA,
    WS_EVENT_RESPONSE_TEXT_DELTA,
    WS_EVENT_RESPONSE_FUNCTION_CALL,
    WS_EVENT_ERROR,
)

_LOGGER = logging.getLogger(__name__)


class OpenAIRealtimeClient:
    """WebSocket client for OpenAI Realtime API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-realtime-preview",
        voice: str = "alloy",
        temperature: float = 0.7,
        system_prompt: str = "",
    ):
        """Initialize the client."""
        self.api_key = api_key
        self.model = model
        self.voice = voice
        self.temperature = temperature
        self.system_prompt = system_prompt
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.session_id: Optional[str] = None
        self.is_connected = False
        self._audio_buffer = bytearray()
        self._text_buffer = ""
        self._reconnect_task: Optional[asyncio.Task] = None
        self._message_handlers: dict[str, list[Callable]] = {}
        self._conversation_context = []
        
    def on(self, event_type: str, handler: Callable) -> None:
        """Register an event handler."""
        if event_type not in self._message_handlers:
            self._message_handlers[event_type] = []
        self._message_handlers[event_type].append(handler)
        
    def off(self, event_type: str, handler: Callable) -> None:
        """Unregister an event handler."""
        if event_type in self._message_handlers:
            self._message_handlers[event_type].remove(handler)
            
    async def _emit(self, event_type: str, data: Any) -> None:
        """Emit an event to all registered handlers."""
        if event_type in self._message_handlers:
            for handler in self._message_handlers[event_type]:
                try:
                    await handler(data) if asyncio.iscoroutinefunction(handler) else handler(data)
                except Exception as e:
                    _LOGGER.error(f"Error in event handler for {event_type}: {e}")

    async def connect(self) -> None:
        """Connect to OpenAI Realtime API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1",
            }
            
            self.websocket = await websockets.connect(
                OPENAI_REALTIME_URL,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10,
            )
            
            self.is_connected = True
            _LOGGER.info("Connected to OpenAI Realtime API")
            
            # Start message handler
            asyncio.create_task(self._handle_messages())
            
            # Configure session
            await self._configure_session()
            
        except Exception as e:
            _LOGGER.error(f"Failed to connect: {e}")
            self.is_connected = False
            await self._schedule_reconnect()
            
    async def disconnect(self) -> None:
        """Disconnect from OpenAI Realtime API."""
        self.is_connected = False
        
        if self._reconnect_task:
            self._reconnect_task.cancel()
            
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            
        _LOGGER.info("Disconnected from OpenAI Realtime API")
        
    async def _configure_session(self) -> None:
        """Configure the session with model parameters."""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": self.system_prompt,
                "voice": self.voice,
                "input_audio_format": AUDIO_FORMAT,
                "output_audio_format": AUDIO_FORMAT,
                "input_audio_transcription": {
                    "enabled": True,
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "tools": [],
                "tool_choice": "auto",
                "temperature": self.temperature,
            }
        }
        
        await self.send_message(config)
        
    async def _handle_messages(self) -> None:
        """Handle incoming WebSocket messages."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                event_type = data.get("type")
                
                _LOGGER.debug(f"Received event: {event_type}")
                
                if event_type == WS_EVENT_SESSION_CREATED:
                    self.session_id = data.get("session", {}).get("id")
                    await self._emit("session_created", data)
                    
                elif event_type == WS_EVENT_SESSION_UPDATED:
                    await self._emit("session_updated", data)
                    
                elif event_type == WS_EVENT_RESPONSE_AUDIO_DELTA:
                    audio_data = base64.b64decode(data.get("delta", ""))
                    await self._emit("audio_delta", audio_data)
                    
                elif event_type == WS_EVENT_RESPONSE_TEXT_DELTA:
                    text_delta = data.get("delta", "")
                    self._text_buffer += text_delta
                    await self._emit("text_delta", text_delta)
                    
                elif event_type == WS_EVENT_RESPONSE_FUNCTION_CALL:
                    await self._emit("function_call", data)
                    
                elif event_type == WS_EVENT_ERROR:
                    _LOGGER.error(f"API Error: {data}")
                    await self._emit("error", data)
                    
                elif event_type == "response.done":
                    await self._emit("response_done", {
                        "text": self._text_buffer,
                        "audio": bytes(self._audio_buffer)
                    })
                    self._text_buffer = ""
                    self._audio_buffer.clear()
                    
        except WebSocketException as e:
            _LOGGER.error(f"WebSocket error: {e}")
            await self._schedule_reconnect()
        except Exception as e:
            _LOGGER.error(f"Message handler error: {e}")
            
    async def send_message(self, message: dict) -> None:
        """Send a message to the API."""
        if not self.is_connected or not self.websocket:
            _LOGGER.warning("Not connected to API")
            return
            
        try:
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            _LOGGER.error(f"Failed to send message: {e}")
            await self._schedule_reconnect()
            
    async def send_audio(self, audio_data: bytes) -> None:
        """Send audio data to the API."""
        # Convert audio to base64
        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        
        message = {
            "type": WS_EVENT_INPUT_AUDIO_BUFFER_APPEND,
            "audio": audio_base64
        }
        
        await self.send_message(message)
        
    async def commit_audio(self) -> None:
        """Commit the audio buffer."""
        message = {"type": WS_EVENT_INPUT_AUDIO_BUFFER_COMMIT}
        await self.send_message(message)
        
    async def clear_audio_buffer(self) -> None:
        """Clear the audio buffer."""
        message = {"type": WS_EVENT_INPUT_AUDIO_BUFFER_CLEAR}
        await self.send_message(message)
        
    async def send_text(self, text: str) -> None:
        """Send text input to the API."""
        message = {
            "type": WS_EVENT_CONVERSATION_ITEM_CREATE,
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": text
                    }
                ]
            }
        }
        
        await self.send_message(message)
        
        # Trigger response
        await self.send_message({"type": WS_EVENT_RESPONSE_CREATE})
        
    async def add_context(self, role: str, content: str) -> None:
        """Add context to the conversation."""
        self._conversation_context.append({
            "type": "message",
            "role": role,
            "content": [
                {
                    "type": "text",
                    "text": content
                }
            ]
        })
        
        message = {
            "type": WS_EVENT_CONVERSATION_ITEM_CREATE,
            "item": self._conversation_context[-1]
        }
        
        await self.send_message(message)
        
    async def clear_context(self) -> None:
        """Clear conversation context."""
        self._conversation_context.clear()
        
    async def update_system_prompt(self, prompt: str) -> None:
        """Update the system prompt."""
        self.system_prompt = prompt
        if self.is_connected:
            await self._configure_session()
            
    async def start_session(self) -> None:
        """Start a new session."""
        if not self.is_connected:
            await self.connect()
            
    async def close_session(self) -> None:
        """Close the current session."""
        await self.disconnect()
        
    async def _schedule_reconnect(self) -> None:
        """Schedule a reconnection attempt."""
        if self._reconnect_task and not self._reconnect_task.done():
            return
            
        self._reconnect_task = asyncio.create_task(self._reconnect())
        
    async def _reconnect(self) -> None:
        """Attempt to reconnect with exponential backoff."""
        retry_count = 0
        max_retries = 5
        base_delay = 1
        
        while retry_count < max_retries and not self.is_connected:
            delay = base_delay * (2 ** retry_count)
            _LOGGER.info(f"Reconnecting in {delay} seconds...")
            await asyncio.sleep(delay)
            
            try:
                await self.connect()
                if self.is_connected:
                    _LOGGER.info("Reconnected successfully")
                    break
            except Exception as e:
                _LOGGER.error(f"Reconnection failed: {e}")
                
            retry_count += 1
            
        if not self.is_connected:
            _LOGGER.error("Max reconnection attempts reached")
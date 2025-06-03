"""Conversation platform for OpenAI Realtime Assistant."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Literal

from homeassistant.components import conversation
from homeassistant.components.conversation import ConversationEntity, ConversationInput, ConversationResult
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import ulid

from .const import DOMAIN, CONF_ENABLE_HOME_CONTROL, CONF_MODEL, CONF_VOICE, CONF_TEMPERATURE, CONF_SYSTEM_PROMPT
from .const import DEFAULT_MODEL, DEFAULT_VOICE, DEFAULT_TEMPERATURE, DEFAULT_SYSTEM_PROMPT
from .home_assistant_tools import HomeAssistantTools
from .websocket_client import OpenAIRealtimeClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OpenAI Realtime conversation from a config entry."""
    api_key = config_entry.data[CONF_API_KEY]
    
    # Create the websocket client
    client = OpenAIRealtimeClient(
        api_key=api_key,
        model=config_entry.data.get(CONF_MODEL, DEFAULT_MODEL),
        voice=config_entry.data.get(CONF_VOICE, DEFAULT_VOICE),
        temperature=config_entry.data.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
        system_prompt=config_entry.data.get(CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT),
    )
    
    # Create and add the conversation entity
    async_add_entities([OpenAIConversationEntity(config_entry, client)])


class OpenAIConversationEntity(ConversationEntity):
    """OpenAI conversation entity."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, entry: ConfigEntry, client: OpenAIRealtimeClient) -> None:
        """Initialize the entity."""
        self.client = client
        self.entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "OpenAI",
            "model": "GPT-4o Realtime",
            "entry_type": "service",
        }
        
        # Response tracking
        self._response_text = ""
        self._response_complete = asyncio.Event()
        
        # Initialize Home Assistant tools if enabled
        self.ha_tools = None
            
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Initialize Home Assistant tools if enabled
        if self.entry.data.get(CONF_ENABLE_HOME_CONTROL, True):
            self.ha_tools = HomeAssistantTools(self.hass)
            await self._setup_function_calling()
        
        # Register this entity as a conversation agent
        conversation.async_set_agent(self.hass, self.entry, self)
            
    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        # Disconnect the client
        if self.client.is_connected:
            await self.client.disconnect()
            
        conversation.async_unset_agent(self.hass, self.entry)
        await super().async_will_remove_from_hass()

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL
        
    async def async_process(
        self, user_input: ConversationInput
    ) -> ConversationResult:
        """Process a conversation input."""
        try:
            # Reset state
            self._response_text = ""
            self._response_complete.clear()
            
            # Ensure connection
            if not self.client.is_connected:
                await self.client.connect()
                
            # Register handlers
            self.client.on("text_delta", self._handle_text_delta)
            self.client.on("response_done", self._handle_response_done)
            self.client.on("function_call", self._handle_function_call)
            
            # Send the user input
            await self.client.send_text(user_input.text)
            
            # Wait for response
            try:
                await asyncio.wait_for(self._response_complete.wait(), timeout=30.0)
            except asyncio.TimeoutError:
                _LOGGER.warning("Response timeout")
                self._response_text = "I'm sorry, I didn't get a response in time. Please try again."
                
            # Cleanup handlers
            self.client.off("text_delta", self._handle_text_delta)
            self.client.off("response_done", self._handle_response_done)
            self.client.off("function_call", self._handle_function_call)
            
            response = intent.IntentResponse(language=user_input.language)
            response.async_set_speech(self._response_text)
            
            return ConversationResult(
                response=response,
                conversation_id=user_input.conversation_id or ulid.ulid(),
            )
            
        except Exception as e:
            _LOGGER.error(f"Conversation processing error: {e}")
            response = intent.IntentResponse(language=user_input.language)
            response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"An error occurred: {str(e)}"
            )
            return ConversationResult(response=response)
            
    async def _setup_function_calling(self) -> None:
        """Set up function calling for Home Assistant control."""
        # Update the client session with available tools
        tools = self.ha_tools.get_available_tools()
        
        if not self.client.is_connected:
            await self.client.connect()
            
        await self.client.send_message({
            "type": "session.update",
            "session": {
                "tools": tools,
                "tool_choice": "auto"
            }
        })
            
    def _handle_text_delta(self, text_delta: str) -> None:
        """Handle text delta from OpenAI."""
        self._response_text += text_delta
        
    def _handle_response_done(self, data: dict) -> None:
        """Handle response completion."""
        if "text" in data:
            self._response_text = data["text"]
        self._response_complete.set()
        
    async def _handle_function_call(self, data: dict) -> None:
        """Handle function calls for Home Assistant control."""
        if not self.ha_tools:
            return
            
        try:
            function_name = data.get("name")
            function_args = json.loads(data.get("arguments", "{}"))
            
            _LOGGER.debug(f"Function call: {function_name} with args: {function_args}")
            
            # Execute the function
            result = await self.ha_tools.execute_function(function_name, function_args)
            
            # Send the result back to OpenAI
            await self.client.send_message({
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": data.get("call_id"),
                    "output": json.dumps(result)
                }
            })
            
        except Exception as e:
            _LOGGER.error(f"Function call error: {e}")
            
            # Send error back to OpenAI
            await self.client.send_message({
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": data.get("call_id"),
                    "output": json.dumps({"error": str(e)})
                }
            })
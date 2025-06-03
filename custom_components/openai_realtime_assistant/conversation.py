"""Conversation platform for OpenAI Realtime Assistant."""
import asyncio
import json
import logging
from typing import Any, Literal

from homeassistant.components import conversation
from homeassistant.components.conversation import ConversationInput, ConversationResult
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import ulid

from .const import DOMAIN, CONF_ENABLE_HOME_CONTROL
from .home_assistant_tools import HomeAssistantTools

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up OpenAI Realtime conversation from YAML."""
    _LOGGER.debug("Setting up OpenAI Realtime conversation from YAML")
    
    # Get the client and config from hass.data
    if DOMAIN not in hass.data:
        _LOGGER.error("OpenAI Realtime Assistant not properly initialized")
        return False
        
    client = hass.data[DOMAIN]["client"]
    agent = OpenAIRealtimeAgent(hass, client, hass.data[DOMAIN]["config"])
    
    # Register the agent for YAML config
    # Create a fake config entry for YAML-based setup
    from homeassistant.helpers import entity_registry
    er = entity_registry.async_get(hass)
    
    # Store the agent in hass.data for access
    hass.data[DOMAIN]["agent"] = agent
    
    # Register as the default conversation agent
    conversation.async_set_agent(hass, None, agent)
    
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OpenAI Realtime conversation from a config entry."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    client = entry_data["client"]
    config = entry_data["config"]
    agent = OpenAIRealtimeAgent(hass, client, config)
    conversation.async_set_agent(hass, config_entry, agent)


class OpenAIRealtimeAgent(conversation.AbstractConversationAgent):
    """OpenAI Realtime conversation agent."""

    def __init__(self, hass: HomeAssistant, client, config: dict):
        """Initialize the agent."""
        self.hass = hass
        self.client = client
        self.config = config
        self._response_complete = asyncio.Event()
        self._response_text = ""
        self._conversation_id = None
        
        # Initialize Home Assistant tools if enabled
        if config.get(CONF_ENABLE_HOME_CONTROL, True):
            self.ha_tools = HomeAssistantTools(hass)
            self._setup_function_calling()
        else:
            self.ha_tools = None
            
    def _setup_function_calling(self):
        """Set up function calling for Home Assistant control."""
        # Update the client session with available tools
        tools = self.ha_tools.get_available_tools()
        asyncio.create_task(self._update_tools(tools))
        
    async def _update_tools(self, tools: list[dict]):
        """Update the session with available tools."""
        if not self.client.is_connected:
            await self.client.connect()
            
        await self.client.send_message({
            "type": "session.update",
            "session": {
                "tools": tools,
                "tool_choice": "auto"
            }
        })
        
    @property
    def attribution(self) -> dict[str, Any]:
        """Return the attribution for the agent."""
        return {
            "name": "OpenAI Realtime Assistant",
            "url": "https://openai.com",
        }
        
    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return "*"
        
    async def async_process(
        self, user_input: ConversationInput
    ) -> ConversationResult:
        """Process a conversation input."""
        try:
            # Reset state
            self._response_text = ""
            self._response_complete.clear()
            
            # Generate conversation ID if needed
            if user_input.conversation_id is None:
                self._conversation_id = ulid.ulid()
            else:
                self._conversation_id = user_input.conversation_id
                
            # Ensure connection
            if not self.client.is_connected:
                await self.client.connect()
                
            # Register handlers
            self.client.on("text_delta", self._handle_text_delta)
            self.client.on("response_done", self._handle_response_done)
            self.client.on("function_call", self._handle_function_call)
            
            # Add any context if this is a continued conversation
            if user_input.conversation_id and hasattr(self, "_conversation_history"):
                for msg in self._conversation_history.get(user_input.conversation_id, []):
                    await self.client.add_context(msg["role"], msg["content"])
                    
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
            
            # Store in conversation history
            if not hasattr(self, "_conversation_history"):
                self._conversation_history = {}
            if self._conversation_id not in self._conversation_history:
                self._conversation_history[self._conversation_id] = []
                
            self._conversation_history[self._conversation_id].extend([
                {"role": "user", "content": user_input.text},
                {"role": "assistant", "content": self._response_text}
            ])
            
            # Limit conversation history
            if len(self._conversation_history[self._conversation_id]) > 20:
                self._conversation_history[self._conversation_id] = (
                    self._conversation_history[self._conversation_id][-20:]
                )
                
            response = intent.IntentResponse(language=user_input.language)
            response.async_set_speech(self._response_text)
            
            return ConversationResult(
                response=response,
                conversation_id=self._conversation_id,
            )
            
        except Exception as e:
            _LOGGER.error(f"Conversation processing error: {e}")
            response = intent.IntentResponse(language=user_input.language)
            response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"An error occurred: {str(e)}"
            )
            return ConversationResult(response=response)
            
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
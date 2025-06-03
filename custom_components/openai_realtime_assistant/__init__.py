"""OpenAI Realtime Assistant Integration for Home Assistant."""
import logging
from typing import Any

# Set up logger at module level to debug loading
_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("OpenAI Realtime Assistant module is being imported")

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_MODEL,
    CONF_VOICE,
    CONF_TEMPERATURE,
    CONF_SYSTEM_PROMPT,
    CONF_ENABLE_HOME_CONTROL,
    CONF_CONVERSATION_TIMEOUT,
    DEFAULT_MODEL,
    DEFAULT_VOICE,
    DEFAULT_TEMPERATURE,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_CONVERSATION_TIMEOUT,
)
from .websocket_client import OpenAIRealtimeClient

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_API_KEY): cv.string,
                vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string,
                vol.Optional(CONF_VOICE, default=DEFAULT_VOICE): cv.string,
                vol.Optional(CONF_TEMPERATURE, default=DEFAULT_TEMPERATURE): vol.Coerce(float),
                vol.Optional(CONF_SYSTEM_PROMPT, default=DEFAULT_SYSTEM_PROMPT): cv.string,
                vol.Optional(CONF_ENABLE_HOME_CONTROL, default=True): cv.boolean,
                vol.Optional(CONF_CONVERSATION_TIMEOUT, default=DEFAULT_CONVERSATION_TIMEOUT): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["stt", "tts", "conversation"]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the OpenAI Realtime Assistant component."""
    _LOGGER.debug("async_setup called for OpenAI Realtime Assistant")
    _LOGGER.debug(f"Config keys: {list(config.keys())}")
    
    if DOMAIN not in config:
        _LOGGER.debug(f"Domain '{DOMAIN}' not found in config, returning True")
        return True

    _LOGGER.debug(f"Setting up OpenAI Realtime Assistant with domain '{DOMAIN}'")
    conf = config[DOMAIN]
    hass.data[DOMAIN] = {
        "config": conf,
        "client": OpenAIRealtimeClient(
            api_key=conf[CONF_API_KEY],
            model=conf[CONF_MODEL],
            voice=conf[CONF_VOICE],
            temperature=conf[CONF_TEMPERATURE],
            system_prompt=conf[CONF_SYSTEM_PROMPT],
        ),
    }

    # Register services
    async def handle_start_conversation(call):
        """Handle start conversation service."""
        _LOGGER.debug(f"Start conversation service called")
        client = hass.data[DOMAIN]["client"]
        await client.start_session()

    async def handle_stop_conversation(call):
        """Handle stop conversation service."""
        _LOGGER.debug(f"Stop conversation service called")
        client = hass.data[DOMAIN]["client"]
        await client.close_session()

    async def handle_clear_context(call):
        """Handle clear context service."""
        _LOGGER.debug(f"Clear context service called")
        client = hass.data[DOMAIN]["client"]
        await client.clear_context()

    async def handle_set_system_prompt(call):
        """Handle set system prompt service."""
        _LOGGER.debug(f"Set system prompt service called with: {call.data}")
        client = hass.data[DOMAIN]["client"]
        prompt = call.data.get("prompt")
        await client.update_system_prompt(prompt)

    hass.services.async_register(DOMAIN, "start_conversation", handle_start_conversation)
    hass.services.async_register(DOMAIN, "stop_conversation", handle_stop_conversation)
    hass.services.async_register(DOMAIN, "clear_context", handle_clear_context)
    hass.services.async_register(DOMAIN, "set_system_prompt", handle_set_system_prompt)

    _LOGGER.debug("OpenAI Realtime Assistant services registered successfully")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenAI Realtime Assistant from a config entry."""
    _LOGGER.debug(f"async_setup_entry called for entry_id: {entry.entry_id}")
    _LOGGER.debug(f"Entry data keys: {list(entry.data.keys())}")
    
    # Store config entry data
    hass.data.setdefault(DOMAIN, {})
    
    # Create client from config entry
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "client": OpenAIRealtimeClient(
            api_key=entry.data[CONF_API_KEY],
            model=entry.data.get(CONF_MODEL, DEFAULT_MODEL),
            voice=entry.data.get(CONF_VOICE, DEFAULT_VOICE),
            temperature=entry.data.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
            system_prompt=entry.data.get(CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT),
        ),
    }
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug(f"Successfully set up entry {entry.entry_id}, platforms forwarded: {PLATFORMS}")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f"async_unload_entry called for entry_id: {entry.entry_id}")
    result = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    _LOGGER.debug(f"Unload result for entry {entry.entry_id}: {result}")
    return result
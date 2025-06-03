"""OpenAI Realtime Assistant Integration for Home Assistant."""
import logging
from typing import Any

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

_LOGGER = logging.getLogger(__name__)

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
    if DOMAIN not in config:
        return True

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
        client = hass.data[DOMAIN]["client"]
        await client.start_session()

    async def handle_stop_conversation(call):
        """Handle stop conversation service."""
        client = hass.data[DOMAIN]["client"]
        await client.close_session()

    async def handle_clear_context(call):
        """Handle clear context service."""
        client = hass.data[DOMAIN]["client"]
        await client.clear_context()

    async def handle_set_system_prompt(call):
        """Handle set system prompt service."""
        client = hass.data[DOMAIN]["client"]
        prompt = call.data.get("prompt")
        await client.update_system_prompt(prompt)

    hass.services.async_register(DOMAIN, "start_conversation", handle_start_conversation)
    hass.services.async_register(DOMAIN, "stop_conversation", handle_stop_conversation)
    hass.services.async_register(DOMAIN, "clear_context", handle_clear_context)
    hass.services.async_register(DOMAIN, "set_system_prompt", handle_set_system_prompt)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenAI Realtime Assistant from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
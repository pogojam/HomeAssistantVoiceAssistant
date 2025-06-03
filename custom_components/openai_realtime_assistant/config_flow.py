"""Config flow for OpenAI Realtime Assistant."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY

from .const import DOMAIN, CONF_MODEL, CONF_VOICE, CONF_ENABLE_HOME_CONTROL, DEFAULT_MODEL, DEFAULT_VOICE


class OpenAIRealtimeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OpenAI Realtime Assistant."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Here you would validate the API key
            # For now, we'll just accept it
            return self.async_create_entry(
                title="OpenAI Realtime Assistant",
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): str,
                vol.Optional(CONF_VOICE, default=DEFAULT_VOICE): str,
                vol.Optional(CONF_ENABLE_HOME_CONTROL, default=True): bool,
            }),
            errors=errors,
        )
"""Home Assistant tools for function calling."""
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import area_registry as ar

_LOGGER = logging.getLogger(__name__)


class HomeAssistantTools:
    """Tools for controlling Home Assistant via function calls."""
    
    def __init__(self, hass: HomeAssistant):
        """Initialize the tools."""
        self.hass = hass
        self.entity_registry = er.async_get(hass)
        self.device_registry = dr.async_get(hass)
        self.area_registry = ar.async_get(hass)
        
    def get_available_tools(self) -> list[dict]:
        """Get the list of available tools for OpenAI."""
        return [
            {
                "type": "function",
                "name": "turn_on",
                "description": "Turn on a device or entity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "The entity ID to turn on (e.g., light.living_room)"
                        }
                    },
                    "required": ["entity_id"]
                }
            },
            {
                "type": "function",
                "name": "turn_off",
                "description": "Turn off a device or entity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "The entity ID to turn off"
                        }
                    },
                    "required": ["entity_id"]
                }
            },
            {
                "type": "function",
                "name": "toggle",
                "description": "Toggle a device or entity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "The entity ID to toggle"
                        }
                    },
                    "required": ["entity_id"]
                }
            },
            {
                "type": "function",
                "name": "set_light_brightness",
                "description": "Set the brightness of a light",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "The light entity ID"
                        },
                        "brightness": {
                            "type": "integer",
                            "description": "Brightness level (0-255)",
                            "minimum": 0,
                            "maximum": 255
                        }
                    },
                    "required": ["entity_id", "brightness"]
                }
            },
            {
                "type": "function",
                "name": "set_light_color",
                "description": "Set the color of a light",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "The light entity ID"
                        },
                        "rgb_color": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "RGB color values [red, green, blue]"
                        }
                    },
                    "required": ["entity_id", "rgb_color"]
                }
            },
            {
                "type": "function",
                "name": "activate_scene",
                "description": "Activate a scene",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "The scene entity ID (e.g., scene.movie_time)"
                        }
                    },
                    "required": ["entity_id"]
                }
            },
            {
                "type": "function",
                "name": "set_climate_temperature",
                "description": "Set the temperature for a climate device",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "The climate entity ID"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Target temperature"
                        }
                    },
                    "required": ["entity_id", "temperature"]
                }
            },
            {
                "type": "function",
                "name": "get_entity_state",
                "description": "Get the current state of an entity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "The entity ID to query"
                        }
                    },
                    "required": ["entity_id"]
                }
            },
            {
                "type": "function",
                "name": "list_entities",
                "description": "List entities by domain or area",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "description": "Entity domain (e.g., light, switch, climate)"
                        },
                        "area": {
                            "type": "string",
                            "description": "Area name"
                        }
                    }
                }
            }
        ]
        
    async def execute_function(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a function with the given arguments."""
        try:
            if function_name == "turn_on":
                return await self._turn_on(args["entity_id"])
            elif function_name == "turn_off":
                return await self._turn_off(args["entity_id"])
            elif function_name == "toggle":
                return await self._toggle(args["entity_id"])
            elif function_name == "set_light_brightness":
                return await self._set_light_brightness(args["entity_id"], args["brightness"])
            elif function_name == "set_light_color":
                return await self._set_light_color(args["entity_id"], args["rgb_color"])
            elif function_name == "activate_scene":
                return await self._activate_scene(args["entity_id"])
            elif function_name == "set_climate_temperature":
                return await self._set_climate_temperature(args["entity_id"], args["temperature"])
            elif function_name == "get_entity_state":
                return await self._get_entity_state(args["entity_id"])
            elif function_name == "list_entities":
                return await self._list_entities(args.get("domain"), args.get("area"))
            else:
                return {"error": f"Unknown function: {function_name}"}
        except Exception as e:
            _LOGGER.error(f"Error executing function {function_name}: {e}")
            return {"error": str(e)}
            
    async def _turn_on(self, entity_id: str) -> Dict[str, Any]:
        """Turn on an entity."""
        await self.hass.services.async_call(
            "homeassistant", "turn_on", {"entity_id": entity_id}
        )
        return {"success": True, "entity_id": entity_id, "action": "turned on"}
        
    async def _turn_off(self, entity_id: str) -> Dict[str, Any]:
        """Turn off an entity."""
        await self.hass.services.async_call(
            "homeassistant", "turn_off", {"entity_id": entity_id}
        )
        return {"success": True, "entity_id": entity_id, "action": "turned off"}
        
    async def _toggle(self, entity_id: str) -> Dict[str, Any]:
        """Toggle an entity."""
        await self.hass.services.async_call(
            "homeassistant", "toggle", {"entity_id": entity_id}
        )
        return {"success": True, "entity_id": entity_id, "action": "toggled"}
        
    async def _set_light_brightness(self, entity_id: str, brightness: int) -> Dict[str, Any]:
        """Set light brightness."""
        await self.hass.services.async_call(
            "light", "turn_on", {"entity_id": entity_id, "brightness": brightness}
        )
        return {"success": True, "entity_id": entity_id, "brightness": brightness}
        
    async def _set_light_color(self, entity_id: str, rgb_color: list) -> Dict[str, Any]:
        """Set light color."""
        await self.hass.services.async_call(
            "light", "turn_on", {"entity_id": entity_id, "rgb_color": rgb_color}
        )
        return {"success": True, "entity_id": entity_id, "rgb_color": rgb_color}
        
    async def _activate_scene(self, entity_id: str) -> Dict[str, Any]:
        """Activate a scene."""
        await self.hass.services.async_call(
            "scene", "turn_on", {"entity_id": entity_id}
        )
        return {"success": True, "entity_id": entity_id, "action": "activated"}
        
    async def _set_climate_temperature(self, entity_id: str, temperature: float) -> Dict[str, Any]:
        """Set climate temperature."""
        await self.hass.services.async_call(
            "climate", "set_temperature", {"entity_id": entity_id, "temperature": temperature}
        )
        return {"success": True, "entity_id": entity_id, "temperature": temperature}
        
    async def _get_entity_state(self, entity_id: str) -> Dict[str, Any]:
        """Get entity state."""
        state = self.hass.states.get(entity_id)
        if state:
            return {
                "entity_id": entity_id,
                "state": state.state,
                "attributes": dict(state.attributes),
                "last_changed": state.last_changed.isoformat(),
                "last_updated": state.last_updated.isoformat()
            }
        else:
            return {"error": f"Entity {entity_id} not found"}
            
    async def _list_entities(self, domain: str = None, area: str = None) -> Dict[str, Any]:
        """List entities by domain or area."""
        entities = []
        
        for state in self.hass.states.async_all():
            if domain and not state.entity_id.startswith(f"{domain}."):
                continue
                
            entity_entry = self.entity_registry.async_get(state.entity_id)
            if area and entity_entry:
                if entity_entry.area_id:
                    area_entry = self.area_registry.async_get_area(entity_entry.area_id)
                    if area_entry and area_entry.name.lower() != area.lower():
                        continue
                else:
                    continue
                    
            entities.append({
                "entity_id": state.entity_id,
                "state": state.state,
                "name": state.attributes.get("friendly_name", state.entity_id)
            })
            
        return {"entities": entities}
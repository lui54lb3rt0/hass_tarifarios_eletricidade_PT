"""Tarifários Eletricidade PT Home Assistant Integration."""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tarifários Eletricidade PT from a config entry."""
    await hass.async_forward_entry_setup(entry, "sensor")
    return True

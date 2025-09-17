"""Tarifários Eletricidade PT Home Assistant Integration."""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tarifários Eletricidade PT from a config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True

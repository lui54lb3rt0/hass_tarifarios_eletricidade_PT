"""Tarifários Eletricidade PT Home Assistant Integration."""

from homeassistant.core import HomeAssistant

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration (empty, config flow only)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up a config entry for the integration."""
    # Store config entry data for access by platforms
    hass.data.setdefault("hass_tarifarios_eletricidade_pt", {})
    hass.data["hass_tarifarios_eletricidade_pt"][entry.entry_id] = entry.data

    # Forward the setup to the sensor platform
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True

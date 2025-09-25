"""Tarifários Eletricidade PT Home Assistant Integration."""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from .const import DOMAIN  # ensure DOMAIN = "hass_tarifarios_eletricidade_pt"
from .data_loader import TarifariosDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration (YAML not used)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Extract configuration from config entry
    comercializador = entry.data.get("comercializador")
    sel_codes = entry.data.get("codigos_oferta")
    if isinstance(sel_codes, str):
        sel_codes = [c.strip() for c in sel_codes.split(",") if c.strip()]
    
    # Create the data update coordinator
    coordinator = TarifariosDataUpdateCoordinator(
        hass, 
        comercializador=comercializador,
        codigos_oferta=sel_codes
    )
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "config": entry.data,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

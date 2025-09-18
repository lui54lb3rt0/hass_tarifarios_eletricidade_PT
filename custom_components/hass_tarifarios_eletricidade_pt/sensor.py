"""Sensor platform for Tarifários Eletricidade PT."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity

from .const import DOMAIN
from .data_loader import process_csv   # get_filtered_dataframe removed


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up sensors for a config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]

    # Base summary sensor (shows what user configured)
    async_add_entities([ResumoTarifariosSensor(entry.entry_id, entry_data)], True)

    # Get user selections
    selected_codigos = entry.data.get("codigos_oferta")
    if isinstance(selected_codigos, str):
        selected_codigos = [c.strip() for c in selected_codigos.split(",") if c.strip()]
    pot_cont = entry.data.get("pot_cont")

    # Load dataframe (already handles filtering by selected codes if passed)
    df = process_csv(codigos_oferta=selected_codigos)

    # Column names after renaming: uses 'Potência contratada' and 'Código da oferta comercial'
    if pot_cont:
        if "Potência contratada" in df.columns:
            df = df[df["Potência contratada"] == pot_cont]
        elif "Pot_Cont" in df.columns:
            df = df[df["Pot_Cont"] == pot_cont]

    entities = []
    if not df.empty and "Código da oferta comercial" in df.columns:
        for _, row in df.iterrows():
            codigo = row["Código da oferta comercial"]
            attrs = row.drop("Código da oferta comercial").to_dict()
            entities.append(TarifaOfertaSensor(entry.entry_id, codigo, attrs))

    async_add_entities(entities, True)


class TarifaOfertaSensor(SensorEntity):
    """Sensor for a single tariff offer."""

    def __init__(self, entry_id: str, codigo: str, attrs: dict):
        self._attr_name = f"Tarifa {codigo}"
        self._attr_unique_id = f"{entry_id}_{codigo}"
        self._state = "available"
        self._attrs = attrs

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attrs


class ResumoTarifariosSensor(SensorEntity):
    """Summary sensor with config entry data."""

    _attr_icon = "mdi:flash"

    def __init__(self, entry_id: str, data: dict):
        self._attr_name = "Tarifários Eletricidade PT"
        self._attr_unique_id = f"{entry_id}_resumo"
        self._data = data
        self._state = "ok"

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._data

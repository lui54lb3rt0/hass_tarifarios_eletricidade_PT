"""Sensor platform for Tarifários Eletricidade PT."""
from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass

from .const import DOMAIN
from .data_loader import process_csv


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up sensors for a config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]

    # ISO8601 UTC timestamp used as "latest update" state
    update_time = datetime.now(timezone.utc).isoformat()

    # Summary sensor (state = last update)
    async_add_entities(
        [ResumoTarifariosSensor(entry.entry_id, entry_data, update_time)],
        True
    )

    selected_codigos = entry.data.get("codigos_oferta")
    if isinstance(selected_codigos, str):
        selected_codigos = [c.strip() for c in selected_codigos.split(",") if c.strip()]
    pot_cont = entry.data.get("pot_cont")

    df = process_csv(codigos_oferta=selected_codigos)
    if df is None or df.empty:
        return

    code_col_candidates = ["Código da oferta comercial", "COD_Proposta", "CODProposta"]
    code_col = next((c for c in code_col_candidates if c in df.columns), None)
    pot_col_candidates = ["Potência contratada", "Pot_Cont"]
    pot_col = next((c for c in pot_col_candidates if c in df.columns), None)

    if pot_cont and pot_col:
        df = df[df[pot_col] == pot_cont]

    if df.empty or not code_col:
        return

    entities = []
    for _, row in df.iterrows():
        codigo = str(row[code_col])
        attrs = row.drop(code_col).to_dict()
        attrs["last_refresh"] = update_time
        entities.append(TarifaOfertaSensor(entry.entry_id, codigo, attrs, update_time))

    async_add_entities(entities, True)


class TarifaOfertaSensor(SensorEntity):
    """Sensor for a single tariff offer (state = last update timestamp)."""

    _attr_icon = "mdi:flash"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, entry_id: str, codigo: str, attrs: dict, update_time: str):
        self._attr_name = f"Tarifa {codigo}"
        self._attr_unique_id = f"{entry_id}_{codigo}"
        self._update_time = update_time
        self._attrs = attrs

    @property
    def state(self):
        return self._update_time  # Latest update timestamp

    @property
    def extra_state_attributes(self):
        return self._attrs


class ResumoTarifariosSensor(SensorEntity):
    """Summary sensor (state = last update timestamp)."""

    _attr_icon = "mdi:flash"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, entry_id: str, data: dict, update_time: str):
        self._attr_name = "Tarifários Eletricidade PT"
        self._attr_unique_id = f"{entry_id}_resumo"
        self._data = dict(data)
        self._update_time = update_time

    @property
    def state(self):
        return self._update_time

    @property
    def extra_state_attributes(self):
        # Add last_refresh too for consistency
        out = dict(self._data)
        out["last_refresh"] = self._update_time
        return out

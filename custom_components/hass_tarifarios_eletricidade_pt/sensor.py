"""Sensor platform for Tarifários Eletricidade PT (only offer sensors)."""
from __future__ import annotations

from datetime import datetime, timezone
import math
import unicodedata
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass

from .const import DOMAIN
from .data_loader import async_process_csv

_LOGGER = logging.getLogger(__name__)

CODE_COL_CANDIDATES = ["Código da oferta comercial", "COD_Proposta", "CODProposta"]
POT_COL_CANDIDATES = ["Potência contratada", "Pot_Cont"]


def _normalize(k: str) -> str:
    k2 = unicodedata.normalize("NFKD", k).encode("ascii", "ignore").decode()
    k2 = k2.lower()
    for old, new in (("€", "eur"), ("%", "pct"), ("/", "_"), ("-", "_")):
        k2 = k2.replace(old, new)
    for ch in "()[]":
        k2 = k2.replace(ch, "")
    while "  " in k2:
        k2 = k2.replace("  ", " ")
    k2 = k2.strip().replace(" ", "_")
    while "__" in k2:
        k2 = k2.replace("__", "_")
    return k2


def _clean(v):
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    timestamp = datetime.now(timezone.utc)  # datetime object (for timestamp device_class)

    selected_codigos = entry.data.get("codigos_oferta")
    if isinstance(selected_codigos, str):
        selected_codigos = [c.strip() for c in selected_codigos.split(",") if c.strip()]
    pot_cont = entry.data.get("pot_cont")

    df = await async_process_csv(hass, codigos_oferta=selected_codigos)
    if df is None or df.empty:
        _LOGGER.warning("async_process_csv returned empty.")
        return

    code_col = next((c for c in CODE_COL_CANDIDATES if c in df.columns), None)
    pot_col = next((c for c in POT_COL_CANDIDATES if c in df.columns), None)

    if pot_cont and pot_col:
        before = len(df)
        df_filtered = df[df[pot_col] == pot_cont]
        if df_filtered.empty:
            _LOGGER.warning("Pot filter removed all rows; keeping unfiltered.")
        else:
            _LOGGER.debug("Pot filter %s: %d -> %d rows", pot_cont, before, len(df_filtered))
            df = df_filtered

    if df.empty:
        _LOGGER.warning("No rows after filtering.")
        return

    if not code_col:
        _LOGGER.error("Code column not found. Available: %s", list(df.columns))
        return

    entities = []
    for _, row in df.iterrows():
        codigo = str(row[code_col])
        raw = row.to_dict()
        attrs = {}
        for k, v in raw.items():
            attrs[_normalize(k)] = _clean(v)
        attrs["codigo_original"] = codigo
        attrs["last_refresh_iso"] = timestamp.isoformat()
        if pot_col:
            attrs["pot_cont_raw"] = row.get(pot_col)
        entities.append(OfferSensor(entry.entry_id, codigo, attrs, timestamp))

    async_add_entities(entities, True)


class OfferSensor(SensorEntity):
    _attr_icon = "mdi:flash"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, entry_id: str, codigo: str, attrs: dict, ts: datetime):
        self._attr_name = f"Tarifa {codigo}"
        self._attr_unique_id = f"{entry_id}_{codigo}"
        self._attrs = attrs
        self._ts = ts

    @property
    def native_value(self):
        return self._ts

    @property
    def extra_state_attributes(self):
        return self._attrs

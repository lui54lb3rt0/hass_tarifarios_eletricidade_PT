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
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CODE_COL_CANDIDATES = ["Código da oferta comercial", "COD_Proposta", "CODProposta"]
NAME_COL_CANDIDATES = ["NomeProposta", "Nome Proposta", "Nome"]
POT_COL_CANDIDATES  = ["Potência contratada__norm", "Pot_Cont__norm", "Potência contratada", "Pot_Cont"]


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


def _norm_pot(val):
    if not val:
        return None
    return str(val).replace(",", ".").strip()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    config = hass.data[DOMAIN][entry.entry_id]["config"]
    
    # Get data from coordinator
    df = coordinator.data
    if df is None or df.empty:
        _LOGGER.warning("No data available from coordinator.")
        return

    ts = datetime.now(timezone.utc)
    pot_cont_cfg = _norm_pot(config.get("pot_cont"))

    code_col = next((c for c in CODE_COL_CANDIDATES if c in df.columns), None)
    name_col = next((c for c in NAME_COL_CANDIDATES if c in df.columns), None)
    pot_norm_col = next((c for c in POT_COL_CANDIDATES if c in df.columns), None)

    if pot_cont_cfg and pot_norm_col:
        before = len(df)
        df_filtered = df[df[pot_norm_col].astype(str) == pot_cont_cfg]
        if not df_filtered.empty:
            _LOGGER.debug("Pot filter %s: %d -> %d", pot_cont_cfg, before, len(df_filtered))
            df = df_filtered
        else:
            _LOGGER.warning("Pot filter removed all rows; keeping unfiltered.")

    if not code_col:
        _LOGGER.error("Code column not found. Columns=%s", list(df.columns))
        return

    entities = []
    for _, row in df.iterrows():
        codigo = str(row[code_col])
        display_name = (str(row[name_col]).strip() if name_col and row.get(name_col) else f"Tarifa {codigo}")

        raw = row.to_dict()
        attrs = {}
        for k, v in raw.items():
            attrs[_normalize(k)] = _clean(v)
        attrs["codigo_original"] = codigo
        attrs["last_refresh_iso"] = ts.isoformat()
        if pot_norm_col and pot_norm_col in row:
            attrs["potencia_norm"] = row[pot_norm_col]

        entities.append(OfferSensor(coordinator, entry.entry_id, codigo, display_name, attrs, ts))

    async_add_entities(entities, True)


class OfferSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Tarifarios offer sensor."""
    _attr_icon = "mdi:flash"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, entry_id: str, codigo: str, name: str, attrs: dict, ts: datetime):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{codigo}"
        self._codigo = codigo
        self._attrs = attrs
        self._ts = ts

    @property
    def native_value(self):
        """Return the timestamp of the last update."""
        if self.coordinator.last_update_success:
            return datetime.now(timezone.utc)
        return self._ts

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        # Update attributes with fresh data from coordinator if available
        if self.coordinator.data is not None and not self.coordinator.data.empty:
            try:
                # Find the row for this codigo in the fresh data
                code_col = next((c for c in CODE_COL_CANDIDATES if c in self.coordinator.data.columns), None)
                if code_col:
                    matching_rows = self.coordinator.data[self.coordinator.data[code_col].astype(str) == self._codigo]
                    if not matching_rows.empty:
                        # Update attributes with fresh data
                        row = matching_rows.iloc[0]
                        fresh_attrs = {}
                        for k, v in row.to_dict().items():
                            fresh_attrs[_normalize(k)] = _clean(v)
                        fresh_attrs["codigo_original"] = self._codigo
                        fresh_attrs["last_refresh_iso"] = datetime.now(timezone.utc).isoformat()
                        return fresh_attrs
            except Exception as e:
                _LOGGER.debug("Error updating attributes for %s: %s", self._codigo, e)
        
        # Fallback to stored attributes
        return self._attrs

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

from .const import DOMAIN, VERSION

_LOGGER = logging.getLogger(__name__)

CODE_COL_CANDIDATES = ["Código da oferta comercial", "COD_Proposta", "CODProposta"]
NAME_COL_CANDIDATES = ["Nome da oferta comercial", "NomeProposta", "Nome Proposta", "Nome"]
POT_COL_CANDIDATES  = ["Potência contratada__norm", "Pot_Cont__norm", "Potência contratada", "Pot_Cont"]
TERMO_FIXO_CANDIDATES = ["Termo fixo (€/dia)", "TF"]


def _normalize(k: str) -> str:
    k2 = unicodedata.normalize("NFKD", k).encode("ascii", "ignore").decode()
    k2 = k2.lower()
    for old, new in (("€", "eur"), ("%", "pct"), ("/", "_"), ("-", "_"), ("|", "_"), (":", "_")):
        k2 = k2.replace(old, new)
    for ch in "()[]{}":
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
    # Normalize to dot format for consistent comparison
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

    code_col = next((c for c in CODE_COL_CANDIDATES if c in df.columns), None)
    name_col = next((c for c in NAME_COL_CANDIDATES if c in df.columns), None)
    pot_norm_col = next((c for c in POT_COL_CANDIDATES if c in df.columns), None)
    termo_fixo_col = next((c for c in TERMO_FIXO_CANDIDATES if c in df.columns), None)

    if not code_col:
        _LOGGER.error("Code column not found. Columns=%s", list(df.columns))
        return

    entities = []
    comercializador = config.get("comercializador", "unknown")
    
    for _, row in df.iterrows():
        codigo = str(row[code_col])
        
        # Get the commercial offer name (Nome da oferta comercial)
        offer_name = None
        if name_col and row.get(name_col):
            offer_name = str(row[name_col]).strip()
        
        # Create display name: Provider - Commercial Offer Name
        if offer_name:
            full_display_name = f"{comercializador} - {offer_name}"
        else:
            # Fallback if no offer name available
            full_display_name = f"{comercializador} - Tarifa {codigo}"

        # Get the termo fixo value for this row
        termo_fixo_value = None
        if termo_fixo_col and row.get(termo_fixo_col):
            try:
                termo_fixo_value = float(str(row[termo_fixo_col]).replace(",", "."))
            except (ValueError, TypeError):
                termo_fixo_value = None

        raw = row.to_dict()
        attrs = {}
        for k, v in raw.items():
            normalized_key = _normalize(k)
            cleaned_value = _clean(v)
            attrs[normalized_key] = cleaned_value
            # Debug specific columns
            if "vazio" in normalized_key.lower() and ("cheias" in normalized_key.lower() or normalized_key.lower().endswith("vazio")):
                _LOGGER.debug("Attribute mapping: '%s' -> '%s' = %s", k, normalized_key, cleaned_value)
        
        attrs["codigo_original"] = codigo
        attrs["comercializador"] = comercializador
        attrs["nome_oferta_comercial"] = offer_name or f"Tarifa {codigo}"
        attrs["termo_fixo_eur_dia"] = termo_fixo_value
        attrs["integration_version"] = VERSION
        attrs["last_refresh_iso"] = ts.isoformat()
        if pot_norm_col and pot_norm_col in row:
            attrs["potencia_norm"] = row[pot_norm_col]

        entities.append(OfferSensor(coordinator, entry.entry_id, codigo, full_display_name, attrs, ts, termo_fixo_value))

    async_add_entities(entities, True)


class OfferSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Tarifarios offer sensor."""
    _attr_icon = "mdi:currency-eur"
    _attr_device_class = None  # No device class for price values
    _attr_unit_of_measurement = "€/day"

    def __init__(self, coordinator, entry_id: str, codigo: str, name: str, attrs: dict, ts: datetime, termo_fixo_value: float = None):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{codigo}"
        self._codigo = codigo
        self._attrs = attrs
        self._ts = ts
        self._termo_fixo_value = termo_fixo_value

    @property
    def native_value(self):
        """Return the daily fixed term value in euros."""
        if self.coordinator.last_update_success and self.coordinator.data is not None and not self.coordinator.data.empty:
            # Try to get fresh termo fixo value from coordinator data
            try:
                code_col = next((c for c in CODE_COL_CANDIDATES if c in self.coordinator.data.columns), None)
                termo_fixo_col = next((c for c in TERMO_FIXO_CANDIDATES if c in self.coordinator.data.columns), None)
                
                if code_col and termo_fixo_col:
                    matching_rows = self.coordinator.data[self.coordinator.data[code_col].astype(str) == self._codigo]
                    if not matching_rows.empty:
                        row = matching_rows.iloc[0]
                        if row.get(termo_fixo_col):
                            try:
                                return float(str(row[termo_fixo_col]).replace(",", "."))
                            except (ValueError, TypeError):
                                pass
            except Exception as e:
                _LOGGER.debug("Error getting fresh termo fixo for %s: %s", self._codigo, e)
        
        # Fallback to stored value
        return self._termo_fixo_value

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
                        fresh_attrs["integration_version"] = VERSION
                        fresh_attrs["last_refresh_iso"] = datetime.now(timezone.utc).isoformat()
                        return fresh_attrs
            except Exception as e:
                _LOGGER.debug("Error updating attributes for %s: %s", self._codigo, e)
        
        # Fallback to stored attributes
        return self._attrs

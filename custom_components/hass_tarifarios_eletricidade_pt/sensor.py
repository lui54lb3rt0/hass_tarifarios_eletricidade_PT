"""Sensor platform for Tarifários Eletricidade PT."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from custom_components.hass_tarifarios_eletricidade_pt.data_loader import get_filtered_dataframe, process_csv
from homeassistant.components.sensor import SensorEntity


def create_entities_from_dataframe(df, user_selected_pot_cont, selected_codigos):
    filtered_df = df[df['Pot_Cont'] == user_selected_pot_cont]
    if selected_codigos:
        filtered_df = filtered_df[filtered_df["Código da oferta comercial"].isin(selected_codigos)]
    entities = []
    for _, row in filtered_df.iterrows():
        cod_proposta = row["Código da oferta comercial"]  # or the column name after renaming
        attributes = row.drop("Código da oferta comercial").to_dict()
        entity = OfertaSensor(cod_proposta, attributes)
        entities.append(entity)
    return entities


class OfertaSensor(SensorEntity):
    def __init__(self, cod_proposta, attributes):
        self._attr_name = f"Tarifa {cod_proposta}"
        self._attr_unique_id = cod_proposta
        self._attr_state = "available"
        self._attr_extra_state_attributes = attributes

    @property
    def name(self):
        return self._attr_name

    @property
    def state(self):
        return self._attr_state

    @property
    def extra_state_attributes(self):
        return self._attr_extra_state_attributes


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up sensors for a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    # Placeholder single sensor
    async_add_entities([TarifarioResumoSensor(entry.entry_id, data)], True)

    user_selected_pot_cont = entry.options.get("pot_cont") or entry.data.get("pot_cont")
    df = get_filtered_dataframe(user_selected_pot_cont)
    
    selected_codigos = entry.data.get("codigos_oferta", [])
    if isinstance(selected_codigos, str):
        selected_codigos = [c.strip() for c in selected_codigos.split(",")]
    
    entities = create_entities_from_dataframe(df, user_selected_pot_cont, selected_codigos)
    async_add_entities(entities)

    # New code using process_csv
    # Get selected codes from config entry if available, else None for all
    selected_codigos = entry.data.get("codigos_oferta", None)
    selected_pot_cont = entry.data.get("pot_cont", None)
    df = process_csv(codigos_oferta=selected_codigos)
    if selected_pot_cont is not None:
        df = df[df['Potência contratada'] == selected_pot_cont]
    entities = []
    for _, row in df.iterrows():
        cod_proposta = row["Código da oferta comercial"]
        attributes = row.drop("Código da oferta comercial").to_dict()
        entities.append(TarifarioSensor(cod_proposta, attributes))
    async_add_entities(entities)

class TarifarioSensor(SensorEntity):
    def __init__(self, cod_proposta, attributes):
        self._attr_name = f"Tarifa {cod_proposta}"
        self._attr_unique_id = cod_proposta
        self._attr_state = "available"
        self._attr_extra_state_attributes = attributes

class TarifarioResumoSensor(Entity):
    _attr_name = "Tarifários Eletricidade PT"
    _attr_icon = "mdi:flash"

    def __init__(self, entry_id: str, data: dict):
        self._entry_id = entry_id
        self._data = data
        self._attr_unique_id = f"{entry_id}_resumo"
        self._state = "ok"

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._data

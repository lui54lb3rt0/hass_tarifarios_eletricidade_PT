"""Sensor platform for Tarifários Eletricidade PT."""
from homeassistant.helpers.entity import Entity, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import pandas as pd
import os

from .const import DOMAIN
from custom_components.hass_tarifarios_eletricidade_pt.data_loader import get_filtered_dataframe


def create_entities_from_dataframe(df, user_selected_pot_cont):
    filtered_df = df[df['Pot_Cont'] == user_selected_pot_cont]
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
    user_selected_pot_cont = entry.options.get("pot_cont") or entry.data.get("pot_cont")
    df = get_filtered_dataframe(user_selected_pot_cont)
    entities = create_entities_from_dataframe(df, user_selected_pot_cont)
    async_add_entities(entities)

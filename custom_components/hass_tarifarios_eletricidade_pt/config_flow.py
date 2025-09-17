import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN
from .data_loader import get_codigos_oferta

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tarifários Eletricidade PT."""

    async def async_step_user(self, user_input=None):
        codigo_oferta_list = get_codigos_oferta()
        schema = vol.Schema({
            vol.Required("codigos_oferta", default=[]): vol.All(
                vol.In(codigo_oferta_list)
            )
        })
        if user_input is not None:
            return self.async_create_entry(
                title="Tarifários Eletricidade PT",
                data=user_input,
            )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )
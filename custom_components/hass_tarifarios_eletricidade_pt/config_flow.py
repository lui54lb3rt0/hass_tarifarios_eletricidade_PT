import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

pot_cont_values = ["3.45", "4.6", "5.75", "6.9", "10.35"]  # Replace with actual values

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tarifários Eletricidade PT."""

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            # Create the config entry and finish setup
            return self.async_create_entry(
                title=f"Tarifários Eletricidade PT ({user_input['pot_cont']})",
                data=user_input,
            )
        # Show the form if no input yet
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("pot_cont", default=pot_cont_values[0]): vol.In(pot_cont_values)
            }),
        )
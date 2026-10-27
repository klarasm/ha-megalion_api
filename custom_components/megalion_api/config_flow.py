"""Config flow for the Megalion API integration."""

import logging
from typing import Any

from megalion_http import Auth, AuthError, MegalionHubAPI
import probatio

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_HOST): str,
        probatio.Required(CONF_USERNAME): str,
        probatio.Required(CONF_PASSWORD): str,
    }
)


class MegalionConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Megalion API."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                auth = Auth(
                    async_get_clientsession(self.hass), user_input[CONF_HOST], ""
                )
                await auth.update_token(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )

                hub = MegalionHubAPI(auth)
                user = await hub.async_get_user()
            except AuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(str(user.userId))
                self._abort_if_unique_id_configured(updates={CONF_HOST:
                                                             user_input[CONF_HOST],
                                                             CONF_USERNAME:
                                                             user_input[CONF_USERNAME],
                                                             CONF_PASSWORD:
                                                             user_input[CONF_PASSWORD],
                                                             })
                return self.async_create_entry(
                    title=f"Megalion API (userId {user.userId})", data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the parameters of an existing entry."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            try:
                auth = Auth(
                    async_get_clientsession(self.hass), user_input[CONF_HOST], ""
                )
                await auth.update_token(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )

                hub = MegalionHubAPI(auth)
                user = await hub.async_get_user()
            except AuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(str(user.userId))
                self._abort_if_unique_id_configured(updates={CONF_HOST:
                                                             user_input[CONF_HOST],
                                                             CONF_USERNAME:
                                                             user_input[CONF_USERNAME],
                                                             CONF_PASSWORD:
                                                             user_input[CONF_PASSWORD],
                                                             })
                return self.async_create_entry(
                    title=f"Megalion API (userId {user.userId})", data=user_input
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(STEP_USER_DATA_SCHEMA,
                                                            entry.data),
            errors=errors
        )

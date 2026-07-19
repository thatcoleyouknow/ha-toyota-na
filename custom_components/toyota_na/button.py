import asyncio
from typing import Any, cast

from toyota_na.vehicle.base_vehicle import RemoteRequestCommand, ToyotaVehicle

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .base_entity import ToyotaNABaseEntity
from .const import COMMAND_BUTTONS, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_devices: AddEntitiesCallback,
):
    """Set up the button platform."""
    buttons = []

    coordinator: DataUpdateCoordinator[list[ToyotaVehicle]] = hass.data[DOMAIN][
        config_entry.entry_id
    ]["coordinator"]

    for vehicle in coordinator.data:
        if vehicle.subscribed is False:
            continue

        for button_config in COMMAND_BUTTONS:
            command = cast(RemoteRequestCommand, button_config["command"])
            if not vehicle.supports_command(command):
                continue
            buttons.append(
                ToyotaCommandButton(
                    command,
                    cast(str, button_config["icon"]),
                    coordinator,
                    button_config["name"],
                    vehicle.vin,
                )
            )

        buttons.append(
            ToyotaRefreshButton(
                coordinator,
                "Refresh",
                vehicle.vin,
            )
        )

    async_add_devices(buttons, True)


class ToyotaCommandButton(ToyotaNABaseEntity, ButtonEntity):
    _icon: str
    _command: RemoteRequestCommand

    def __init__(
        self,
        command: RemoteRequestCommand,
        icon: str,
        *args: Any,
    ):
        super().__init__(*args)
        self._command = command
        self._icon = icon

    @property
    def icon(self):
        return self._icon

    @property
    def available(self):
        return self.vehicle is not None

    async def async_press(self) -> None:
        """Send the remote command, then refresh the coordinator once the vehicle updates."""
        if self.vehicle is None:
            return
        await self.vehicle.send_command(self._command)
        self.hass.async_create_task(self._background_refresh())

    async def _background_refresh(self):
        """Poll for updated vehicle state after a command, then refresh the coordinator."""
        try:
            await self.vehicle.poll_vehicle_refresh()
            await asyncio.sleep(10)
            await self.coordinator.async_request_refresh()
        except Exception:
            pass


class ToyotaRefreshButton(ToyotaNABaseEntity, ButtonEntity):
    @property
    def icon(self):
        return "mdi:refresh"

    @property
    def available(self):
        return self.vehicle is not None

    async def async_press(self) -> None:
        """Force Toyota to push a fresh status, then refresh the coordinator."""
        if self.vehicle is None:
            return
        await self.vehicle.poll_vehicle_refresh()
        self.coordinator.async_set_updated_data(self.coordinator.data)
        await asyncio.sleep(10)
        await self.coordinator.async_request_refresh()

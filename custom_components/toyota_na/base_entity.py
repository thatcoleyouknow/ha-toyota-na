from typing import Union

from toyota_na.vehicle.base_vehicle import ToyotaVehicle, VehicleFeatures

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN


class ToyotaNABaseEntity(CoordinatorEntity[list[ToyotaVehicle]]):
    def __init__(
        self,
        coordinator: DataUpdateCoordinator[list[ToyotaVehicle]],
        sensor_name: str,
        vin: str,
    ) -> None:
        super().__init__(coordinator)
        self.sensor_name = sensor_name
        self.vin = vin

    def feature(self, feature: VehicleFeatures):
        """Return the feature dict."""
        if self.vehicle is None:
            return
        return self.vehicle.features.get(feature)

    @property
    def name(self):
        # Deliberately just the sensor name, not "{sensor_name} {vehicle model}" -- Home
        # Assistant already prefixes an entity's friendly name with its device's name in the UI.
        # Building that prefix manually here produced reversed/doubled names (e.g. "2023
        # Highlander Front Driver Door 2023 Highlander"). Don't reintroduce it.
        if self.vehicle is not None:
            return self.sensor_name

    @property
    def unique_id(self):
        # Plain vin+sensor_name, no config-entry namespacing. A vehicle visible to two Toyota
        # accounts (Toyota "family sharing") could in principle collide here if both accounts'
        # entries tried to create entities for the same VIN -- entry_id namespacing was tried
        # for this (see git history) and reverted in favor of a different fix: only one config
        # entry is ever allowed to create entities for a given VIN in the first place (the VIN
        # claim guard in __init__.py, see async_claim_vehicles()). That external invariant is
        # what keeps this safe; it isn't enforced by anything in this file.
        return f"{self.vin}.{self.sensor_name}"

    @property
    def device_info(self) -> DeviceInfo:
        model = None

        if self.vehicle is not None:
            model = f"{self.vehicle.model_year} {self.vehicle.model_name}"

        return {
            "identifiers": {(DOMAIN, self.vin)},
            "name": model,
            "model": model,
            "manufacturer": "Toyota Motor North America",
        }

    @property
    def vehicle(self) -> Union[ToyotaVehicle, None]:
        """Return the vehicle."""
        return next((v for v in self.coordinator.data if v.vin == self.vin), None)

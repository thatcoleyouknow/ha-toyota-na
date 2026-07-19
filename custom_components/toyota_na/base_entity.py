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
        if self.vehicle is not None:
            return self.sensor_name

    @property
    def unique_id(self):
        # Namespaced by config entry so the same VIN visible to two different Toyota accounts
        # (e.g. a family-shared vehicle) never collides -- see the comment where entry_id is
        # set on the coordinator in __init__.py for why this matters.
        return f"{self.coordinator.entry_id}.{self.vin}.{self.sensor_name}"

    @property
    def device_info(self) -> DeviceInfo:
        model = None

        if self.vehicle is not None:
            model = f"{self.vehicle.model_year} {self.vehicle.model_name}"

        return {
            "identifiers": {(DOMAIN, f"{self.coordinator.entry_id}.{self.vin}")},
            "name": model,
            "model": model,
            "manufacturer": "Toyota Motor North America",
        }

    @property
    def vehicle(self) -> Union[ToyotaVehicle, None]:
        """Return the vehicle."""
        return next((v for v in self.coordinator.data if v.vin == self.vin), None)

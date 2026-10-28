"""Sensor platform for the Megalion API integration."""

import logging

from collections.abc import Callable
from dataclasses import dataclass
from typing import override, Any
import datetime as dt

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfDensity,
    UnitOfElectricPotential,
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfRatio,
    UnitOfTemperature,
)
from homeassistant.const import UnitOfRatio
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import MegalionConfigEntry, MegalionCoordinator
from .entity import MegalionEntity

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class MegalionSensorEntityDescription(SensorEntityDescription):
    """Describe a Megalion sensor."""

    value_fn: Callable[[str, MegalionStatus], str | float | int]

def fromutcisoformat(iso: str) -> dt.datetime:
    return dt.datetime.replace(dt.datetime.fromisoformat(iso), tzinfo=dt.UTC)

BATTERY_SENSORS: tuple[MegalionSensorEntityDescription, ...] = (
    MegalionSensorEntityDescription(
        key="dayCharge",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda sn, status: status.batteries[sn].dayCharge,
        name="Energy Charged Today",
    ),
    MegalionSensorEntityDescription(
        key="dayDisharge",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda sn, status: status.batteries[sn].dayDischarge,
        name="Energy Discharged Today",
    ),
    MegalionSensorEntityDescription(
        key="deviceId",
        value_fn=lambda sn, status: status.batteries[sn].deviceId,
        entity_category = EntityCategory.DIAGNOSTIC,
        name="Device ID",
    ),
    MegalionSensorEntityDescription(
        key="sn",
        value_fn=lambda sn, status: status.batteries[sn].sn,
        entity_category = EntityCategory.DIAGNOSTIC,
        name="Serial Number",
    ),
    MegalionSensorEntityDescription(
        key="lastOfflineTimeUtc",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda sn, status: fromutcisoformat(status.batteries[sn].lastOfflineTimeUtc),
        entity_category = EntityCategory.DIAGNOSTIC,
        name="Offline Since",
    ),
    MegalionSensorEntityDescription(
        key="lastOnlineTimeUtc",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda sn, status: fromutcisoformat(status.batteries[sn].lastOnlineTimeUtc),
        entity_category = EntityCategory.DIAGNOSTIC,
        name="Online Since",
    ),
)

def get_property(battery: Battery, property: str) -> dict[str, Any]:
        return next(e for e in battery.raw_detail
                    if e['propertyName'] == property)

def get_value_or_note(entry: dict[str, Any]) -> str:
    match entry['propertyName']:
        case "reportTime":
            return entry['value']
        case _:
            if entry['note'] == "" or entry['unit'] != "":
                return entry['value']
            else:
                return entry['note']

def gen_detail_desc(entry: dict[str, Any]) -> MegalionSensorEntityDescription:

    unit = entry['unit']

    device_class=None
    native_unit_of_measurement=None
    state_class=None
    suggested_display_precision=None
    entity_category=None
    value_fn=lambda sn, status: get_value_or_note(get_property(status.batteries[sn], entry['propertyName']))

    match unit:
        case "A":
            device_class=SensorDeviceClass.CURRENT
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE
            state_class=SensorStateClass.MEASUREMENT
        case "Ah":
            native_unit_of_measurement=unit
            state_class=SensorStateClass.MEASUREMENT
        case "kW":
            device_class=SensorDeviceClass.POWER
            native_unit_of_measurement=UnitOfPower.KILO_WATT
            state_class=SensorStateClass.MEASUREMENT
        case "kWh":
            device_class=SensorDeviceClass.ENERGY
            native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR
            state_class=SensorStateClass.TOTAL
        case "mV":
            device_class=SensorDeviceClass.VOLTAGE
            native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT
            state_class=SensorStateClass.MEASUREMENT
        case "V":
            device_class=SensorDeviceClass.VOLTAGE
            native_unit_of_measurement=UnitOfElectricPotential.VOLT
            state_class=SensorStateClass.MEASUREMENT
            suggested_display_precision=1
        case "%":
            device_class=SensorDeviceClass.BATTERY
            native_unit_of_measurement=UnitOfRatio.PERCENTAGE
            state_class=SensorStateClass.MEASUREMENT
        case "℃":
            device_class=SensorDeviceClass.TEMPERATURE
            native_unit_of_measurement=UnitOfTemperature.CELSIUS
            state_class=SensorStateClass.MEASUREMENT

    if entry['propertyName'] in [ "bmsVersion", "reportTime",
                                 "relayControlStatus", "min_voltage_location",
                                 "max_voltage_location",
                                 "min_temperature_location",
                                 "max_temperature_location", "pcsProtocolType",
                                 "online_voltage_count",
                                 "online_temperature_count", "rackStatus",
                                 "systemWorkMode", "systemOperationStatus",
                                 "online_cluster_count", "online_module_count"
                                 ]:
        entity_category = EntityCategory.DIAGNOSTIC
    if entry['propertyName'] == "reportTime":
        device_class=SensorDeviceClass.TIMESTAMP
        value_fn=lambda sn, status: fromutcisoformat(get_value_or_note(get_property(status.batteries[sn], entry['propertyName'])))

    return MegalionSensorEntityDescription(
        key=entry['propertyName'],
        device_class=device_class,
        native_unit_of_measurement=native_unit_of_measurement,
        state_class=state_class,
        suggested_display_precision=suggested_display_precision,
        name=entry['propertyNameEn'],
        entity_category=entity_category,
        value_fn=value_fn
    )

def batt_fw(batt: dict[str, Any]) -> str:
    return next(fw['value'] for fw in batt.raw_detail if fw['propertyName'] == "bmsVersion")

async def async_setup_entry(
    hass: HomeAssistant,
    entry: MegalionConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Megalion API sensors."""
    coordinator = entry.runtime_data

    user = coordinator.data.user
    batteries = coordinator.data.batteries
    battery_entities = [
        MegalionBatterySensor(coordinator, desc, sn, batt_fw(batt))
        for sn, batt in batteries.items()
        for desc in BATTERY_SENSORS
    ]
    battery_detail = [
            MegalionBatterySensor(coordinator, gen_detail_desc(detail), sn, batt_fw(batt))
            for sn, batt in batteries.items()
            for detail in batt.raw_detail
            ]
    battery_cell_voltages = [
            MegalionBatterySensor(coordinator, MegalionSensorEntityDescription(
                    key=f"cell_{i+1}_voltage",
                    device_class=SensorDeviceClass.VOLTAGE,
                    native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
                    state_class=SensorStateClass.MEASUREMENT,
                    name=f"Cell {i+1} Voltage",
                    value_fn=lambda sn, status, i=i: status.batteries[sn].cellVoltages[i],
                    entity_category = EntityCategory.DIAGNOSTIC,
                ), sn, batt_fw(batt))
            for sn, batt in batteries.items()
            for i in range(0, len(batt.cellVoltages))
            ]
    battery_cell_temperatures = [
            MegalionBatterySensor(coordinator, MegalionSensorEntityDescription(
                    key=f"cell_group_{i+1}_temperature",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                    state_class=SensorStateClass.MEASUREMENT,
                    name=f"Cell Group {i+1} Temperature",
                    value_fn=lambda sn, status, i=i: status.batteries[sn].cellTemperatures[i],
                    entity_category = EntityCategory.DIAGNOSTIC,
                ), sn, batt_fw(batt))
            for sn, batt in batteries.items()
            for i in range(0, len(batt.cellTemperatures))
            ]
    async_add_entities(battery_entities + battery_detail +
                       battery_cell_voltages + battery_cell_temperatures)

class MegalionBatterySensor(MegalionEntity, SensorEntity):
    """A sensor of a Megalion Battery device."""

    entity_description: MegalionSensorEntityDescription

    def __init__(
        self,
        coordinator: MegalionCoordinator,
        description: MegalionSensorEntityDescription,
        sn: str,
        fw: str,
    ) -> None:
        battery = coordinator.data.batteries[sn]
        device_info = DeviceInfo(
            identifiers={(DOMAIN, sn)},
            manufacturer="Megalion",
            model=battery.deviceModel,
            name=battery.deviceName,
            serial_number=battery.sn,
            sw_version=fw,
        )
        super().__init__(coordinator, device_info)
        self.entity_description = description
        self._attr_unique_id = f"{sn}_{description.key}"
        if hasattr(description, "name"):
            self._attr_name = description.name
        self.sn = sn

    @property
    @override
    def native_value(self) -> datetime | str | float | int:
        """Return the value of the sensor."""
        return self.entity_description.value_fn(self.sn, self.coordinator.data)

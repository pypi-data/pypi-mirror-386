from typing import ClassVar

from mxcubecore import HardwareRepository as HWR
from mxcubecore.HardwareObjects.abstract import AbstractEnergy

from mxcubeweb.core.adapter.actuator_adapter import ActuatorAdapter
from mxcubeweb.core.adapter.wavelength_adapter import WavelengthAdapter
from mxcubeweb.core.models.configmodels import ResourceHandlerConfigModel

resource_handler_config = ResourceHandlerConfigModel(
    commands=["set_value", "stop", "get_resolution_limits_for_energy"],
    attributes=["data", "get_value"],
)


class EnergyAdapter(ActuatorAdapter):
    """Adapter for Energy Hardware Object.

    A web socket is used to communicate information on longer running processes.
    """

    SUPPORTED_TYPES: ClassVar[list[object]] = [AbstractEnergy.AbstractEnergy]

    def __init__(  # noqa: D417
        self, ho, role, app
    ):
        """Initialize.

        Args:
            ho (object): Hardware object.
        """
        super().__init__(ho, role, app, resource_handler_config)
        self._add_adapter("wavelength", self._ho, WavelengthAdapter)
        self._type = "ENERGY"

    def get_resolution_limits_for_energy(self, energy: float) -> tuple:
        return HWR.beamline.resolution.get_limits_for_wavelength(
            self._ho.calculate_wavelength(energy)
        )

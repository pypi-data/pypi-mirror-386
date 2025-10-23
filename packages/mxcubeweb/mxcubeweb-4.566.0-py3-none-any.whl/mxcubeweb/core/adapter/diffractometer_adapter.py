from typing import ClassVar

from mxcubecore.HardwareObjects import GenericDiffractometer, MiniDiff

from mxcubeweb.core.adapter.adapter_base import AdapterBase
from mxcubeweb.core.models.configmodels import ResourceHandlerConfigModel

resource_handler_config = ResourceHandlerConfigModel(
    commands=["set_chip_layout", "set_phase"],
    attributes=["data", "get_value", "head_configuration"],
)


class DiffractometerAdapter(AdapterBase):
    ATTRIBUTES = ["head_configuration"]
    METHODS = ["set_chip_layout"]

    SUPPORTED_TYPES: ClassVar[list[object]] = [
        MiniDiff.MiniDiff,
        GenericDiffractometer.GenericDiffractometer,
    ]

    def __init__(  # noqa: D417
        self, ho, role, app
    ):
        """Initialize.

        Args:
            ho (object): Hardware object.
        """
        super().__init__(ho, role, app, resource_handler_config)
        ho.connect("stateChanged", self._state_change)
        ho.connect("valueChanged", self._state_change)
        ho.connect("phaseChanged", self._diffractometer_phase_changed)

    def _diffractometer_phase_changed(self, phase):
        self.app.server.emit(
            "diff_phase_changed",
            {"msg": "Diffractometer phase changed", "phase": phase},
            namespace="/hwr",
        )

    def _state_change(self, *args, **kwargs):
        self.state_change(*args, **kwargs)

    def get_value(self) -> dict:
        return {
            "currentPhase": self._ho.get_current_phase(),
            "phaseList": self._ho.get_phase_list(),
        }

    def stop(self):
        pass

    def state(self):
        return "READY" if self._ho.is_ready() else "BUSY"

    def head_configuration(self) -> dict:
        data = self._ho.get_head_configuration()
        return data.dict() if data else {}

    def set_chip_layout(
        self,
        layout_name: str,
    ) -> bool:
        self._ho.set_chip_layout(layout_name)
        return True

    def set_phase(self, phase: str) -> bool:
        self._ho.set_phase(phase)
        return True

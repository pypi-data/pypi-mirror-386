from typing import ClassVar

from mxcubecore import HardwareRepository as HWR
from mxcubecore.HardwareObjects.abstract import AbstractDetector

from mxcubeweb.core.adapter.adapter_base import AdapterBase
from mxcubeweb.core.models.configmodels import ResourceHandlerConfigModel

resource_handler_config = ResourceHandlerConfigModel(
    commands=["display_image"],
    attributes=["data", "get_value"],
)


class DetectorAdapter(AdapterBase):
    SUPPORTED_TYPES: ClassVar[list[object]] = [AbstractDetector.AbstractDetector]

    def __init__(  # noqa: D417
        self, ho, role, app
    ):
        """Initialize.

        Args:
            ho (object): Hardware object.
        """
        super().__init__(ho, role, app, resource_handler_config)
        ho.connect("stateChanged", self._state_change)

    def get_value(self) -> dict:
        """Get the file suffix of the data files."""
        return {"fileSuffix": HWR.beamline.detector.get_property("file_suffix", "?")}

    def _state_change(self, *args, **kwargs):
        self.state_change(*args, **kwargs)

    def state(self):
        return self._ho.get_state().name.upper()

    def display_image(self, path: str, img_num) -> dict:
        """Notify ADXV and/or Braggy of the image to display."""
        res = {"image_url": ""}

        if path:
            fpath, img = HWR.beamline.detector.get_actual_file_path(path, img_num)
            HWR.beamline.collect.adxv_notify(fpath, img)
            fpath = HWR.beamline.session.get_path_with_proposal_as_root(fpath)

            if self.app.config.braggy.USE_BRAGGY:
                res = {
                    "image_url": (
                        f"{self.app.config.braggy.BRAGGY_URL}/"
                        f"?file={fpath}/image_${img_num}.h5.dataset"
                    )
                }

        return res

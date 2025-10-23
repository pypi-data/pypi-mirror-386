import logging

import gevent.event
from mxcubecore import HardwareRepository as HWR
from mxcubecore.queue_entry.base_queue_entry import CENTRING_METHOD

from mxcubeweb.core.components.component_base import ComponentBase
from mxcubeweb.core.util.convertutils import (
    from_camel,
    to_camel,
)

SNAPSHOT_RECEIVED = gevent.event.Event()
SNAPSHOT = None


class SampleView(ComponentBase):
    def __init__(self, app, config):
        super().__init__(app, config)
        self._click_count = 0
        self._click_limit = 3
        self._centring_point_id = None

        HWR.beamline.sample_view.connect("shapesChanged", self._emit_shapes_updated)

        zoom_motor = HWR.beamline.diffractometer.get_object_by_role("zoom")

        if zoom_motor:
            zoom_motor.connect("stateChanged", self._zoom_changed)

    def _zoom_changed(self, *args, **kwargs):
        ppm = HWR.beamline.diffractometer.get_pixels_per_mm()
        self.app.server.emit(
            "update_pixels_per_mm",
            {"pixelsPerMm": ppm},
            namespace="/hwr",
        )

    def _emit_shapes_updated(self):
        shape_dict = {}

        for shape in HWR.beamline.sample_view.get_shapes():
            _s = to_camel(shape.as_dict())
            shape_dict.update({shape.id: _s})

        self.app.server.emit("update_shapes", {"shapes": shape_dict}, namespace="/hwr")

    def centring_clicks_left(self):
        return self._click_limit - self._click_count

    def centring_reset_click_count(self):
        self._click_count = 0

    def centring_click(self):
        self._click_count += 1

    def centring_remove_current_point(self):
        if self._centring_point_id:
            HWR.beamline.sample_view.delete_shape(self._centring_point_id)
            self._emit_shapes_updated()
            self._centring_point_id = None

    def centring_add_current_point(self, *args):
        shape = HWR.beamline.sample_view.get_shape(self._centring_point_id)

        # There is no current centered point shape when the centring is done
        # by software like Workflows, so we add one.
        if not shape:
            try:
                if args[0]:
                    motors = args[1]["motors"]
                    (x, y) = HWR.beamline.diffractometer.motor_positions_to_screen(
                        motors
                    )
                    self.centring_update_current_point(motors, x, y)
                    shape = HWR.beamline.sample_view.get_shape(self._centring_point_id)
            except Exception:
                logging.getLogger("MX3.HWR").exception("Centring failed !")

        if shape:
            shape.state = "SAVED"
            self._emit_shapes_updated()
            self._centring_point_id = None

    def centring_update_current_point(self, motor_positions, x, y):
        point = HWR.beamline.sample_view.get_shape(self._centring_point_id)

        if point:
            point.move_to_mpos([motor_positions], [x, y])
        else:
            point = HWR.beamline.sample_view.add_shape_from_mpos(
                [motor_positions], (x, y), "P"
            )
            point.state = "TMP"
            point.selected = True
            self._centring_point_id = point.id

        self._emit_shapes_updated()

    def wait_for_centring_finishes(self, *args, **kwargs):
        """Executed when a centring is finished.

        It updates the temporary centred point.
        """
        try:
            centring_status = args[1]
        except IndexError:
            centring_status = {"valid": False}

        # we do not send/save any centring data if there is no sample
        # to avoid the 2d centring when no sample is mounted
        if self.app.lims.get_current_sample().get("sampleID", "") == "":
            return

        # If centering is valid add the point, otherwise remove it
        if centring_status["valid"]:
            motor_positions = centring_status["motors"]
            motor_positions.pop("zoom", None)
            motor_positions.pop("beam_y", None)
            motor_positions.pop("beam_x", None)

            (x, y) = HWR.beamline.diffractometer.motor_positions_to_screen(
                motor_positions
            )

            self.centring_update_current_point(motor_positions, x, y)

            if self.app.AUTO_MOUNT_SAMPLE:
                HWR.beamline.diffractometer.accept_centring()

    def init_signals(self):
        """Connect relevant hardware object signals to callbacks.

        Connect all the relevant hwobj signals with the corresponding callback method.
        """
        from mxcubeweb.routes import signals

        dm = HWR.beamline.diffractometer
        dm.connect("centringStarted", signals.centring_started)
        dm.connect("centringSuccessful", self.wait_for_centring_finishes)
        dm.connect("centringFailed", self.wait_for_centring_finishes)
        dm.connect("centringAccepted", self.centring_add_current_point)
        HWR.beamline.sample_view.connect("newGridResult", self.handle_grid_result)
        self._click_limit = int(HWR.beamline.config.click_centring_num_clicks or 3)

    def set_image_size(self, width, height):
        HWR.beamline.sample_view.camera.restart_streaming((width, height))
        return self.get_viewport_info()

    def move_to_centred_position(self, point_id):
        point = HWR.beamline.sample_view.get_shape(point_id)

        if point:
            motor_positions = point.get_centred_position().as_dict()
            HWR.beamline.diffractometer.move_motors(motor_positions)

        return point

    def get_shapes(self):
        shape_dict = {}

        for shape in HWR.beamline.sample_view.get_shapes():
            s = shape.as_dict()
            # shape key comes case lowered from the to_camel (2dp1), this breaks UI
            # let's ensure it's upper case by only camel casing the dict data
            shape_dict.update({shape.id: to_camel(s)})
        return {"shapes": shape_dict}

    def get_shape_width_sid(self, sid):
        shape = HWR.beamline.sample_view.get_shape(sid)

        if shape is not None:
            shape = shape.as_dict()
            return {"shape": to_camel(shape)}

        return shape

    def shape_add_result(self, sid, result, data_file):
        from mxcubeweb.routes import signals

        shape = HWR.beamline.sample_view.get_shape(sid)
        HWR.beamline.sample_view.set_grid_data(sid, result, data_file)
        signals.grid_result_available(to_camel(shape.as_dict()))

    def handle_grid_result(self, shape):
        from mxcubeweb.routes import signals

        signals.grid_result_available(to_camel(shape.as_dict()))

    def update_shapes(self, shapes):
        updated_shapes = []
        for s in shapes:
            shape_data = from_camel(s)
            pos = []

            # Get the shape if already exists
            shape = HWR.beamline.sample_view.get_shape(shape_data.get("id", -1))

            # If shape does not exist add it
            if not shape:
                refs, t = shape_data.pop("refs", []), shape_data.pop("t", "")
                state = shape_data.pop("state", "SAVED")
                user_state = shape_data.pop("user_state", "SAVED")

                # Store pixels per mm for third party software, to facilitate
                # certain calculations

                shape_data["pixels_per_mm"] = (
                    HWR.beamline.diffractometer.get_pixels_per_mm()
                )

                shape_data["beam_pos"] = (
                    HWR.beamline.beam.get_beam_position_on_screen()[0],
                    HWR.beamline.beam.get_beam_position_on_screen()[1],
                )
                shape_data["beam_width"] = HWR.beamline.beam.get_value()[0]
                shape_data["beam_height"] = HWR.beamline.beam.get_value()[1]

                # Shape does not have any refs, create a new Centered position
                if not refs:
                    try:
                        x, y = shape_data["screen_coord"]
                        mpos = HWR.beamline.diffractometer.get_centred_point_from_coord(
                            x, y, return_by_names=True
                        )
                        pos.append(mpos)

                        # We also store the center of the grid
                        if t == "G":
                            # coords for the center of the grid
                            x_c = (
                                x
                                + (shape_data["num_cols"] / 2.0)
                                * shape_data["cell_width"]
                            )
                            y_c = (
                                y
                                + (shape_data["num_rows"] / 2.0)
                                * shape_data["cell_height"]
                            )
                            center_positions = HWR.beamline.diffractometer.get_centred_point_from_coord(
                                x_c, y_c, return_by_names=True
                            )
                            pos.append(center_positions)

                        shape = HWR.beamline.sample_view.add_shape_from_mpos(
                            pos, (x, y), t, state, user_state
                        )
                    except Exception:
                        logging.getLogger("MX3.HWR").info(shape_data)

                else:
                    shape = HWR.beamline.sample_view.add_shape_from_refs(
                        refs, t, state, user_state
                    )

            # shape will be none if creation failed, so we check if shape exists
            # before setting additional parameters
            if shape:
                shape.update_from_dict(shape_data)
                shape_dict = to_camel(shape.as_dict())
                updated_shapes.append(shape_dict)

        return {"shapes": updated_shapes}

    def rotate_to(self, sid):
        if sid:
            shape = HWR.beamline.sample_view.get_shape(sid)
            cp = shape.get_centred_position()
            phi_value = round(float(cp.as_dict().get("phi", None)), 3)
            if phi_value:
                try:
                    HWR.beamline.diffractometer.centringPhi.set_value(phi_value)
                except Exception:
                    raise

    def start_auto_centring(self):
        """Start automatic (lucid) centring procedure.

        :statuscode: 200: no error
        :statuscode: 409: error
        """
        if not HWR.beamline.diffractometer.current_centring_procedure:
            msg = "Starting automatic centring"
            logging.getLogger("user_level_log").info(msg)

            HWR.beamline.diffractometer.start_centring_method(
                HWR.beamline.diffractometer.C3D_MODE
            )
        else:
            msg = "Could not starting automatic centring, already centring."
            logging.getLogger("user_level_log").info(msg)

    def start_manual_centring(self):
        """Start Click centring procedure.

        :statuscode: 200: no error
        :statuscode: 409: error
        """
        if HWR.beamline.diffractometer.is_ready():
            if HWR.beamline.diffractometer.current_centring_procedure:
                logging.getLogger("user_level_log").info(
                    "Aborting current centring ..."
                )
                HWR.beamline.diffractometer.cancel_centring_method(reject=True)
            msg = "Centring using %s-click centring"
            logging.getLogger("user_level_log").info(
                msg, HWR.beamline.config.click_centring_num_clicks
            )

            HWR.beamline.diffractometer.start_centring_method(
                HWR.beamline.diffractometer.CENTRING_METHOD_MANUAL
            )

            self.centring_reset_click_count()
        else:
            logging.getLogger("user_level_log").warning(
                "Diffractometer is busy, cannot start centering"
            )
            msg = "Diffractometer is busy, cannot start centering"
            raise RuntimeError(msg)

        return {"clicksLeft": self.centring_clicks_left()}

    def abort_centring(self):
        try:
            logging.getLogger("user_level_log").info("User canceled centring")
            HWR.beamline.diffractometer.cancel_centring_method()
            self.centring_remove_current_point()
        except Exception:
            logging.getLogger("MX3.HWR").warning("Canceling centring failed")

    def centring_handle_click(self, x, y):
        if HWR.beamline.diffractometer.current_centring_procedure:
            try:
                HWR.beamline.diffractometer.image_clicked(x, y, x, y)
                self.centring_click()
            except Exception:
                return {"clicksLeft": -1}
        else:
            if not self.centring_clicks_left():
                self.centring_reset_click_count()
                HWR.beamline.diffractometer.cancel_centring_method()

                HWR.beamline.diffractometer.start_centring_method(
                    HWR.beamline.diffractometer.CENTRING_METHOD_MANUAL
                )

        return {"clicksLeft": self.centring_clicks_left()}

    def reject_centring(self):
        HWR.beamline.diffractometer.reject_centring()
        self.centring_remove_current_point()

    def move_to_beam(self, x, y):
        msg = "Moving point x: %s, y: %s to beam" % (x, y)
        logging.getLogger("user_level_log").info(msg)

        HWR.beamline.diffractometer.move_to_beam(x, y)

    def set_centring_method(self, method):
        if method == CENTRING_METHOD.LOOP:
            msg = "Using automatic loop centring when mounting samples"
            HWR.beamline.queue_manager.centring_method = CENTRING_METHOD.LOOP
        else:
            msg = "Using click centring when mounting samples"
            HWR.beamline.queue_manager.centring_method = CENTRING_METHOD.MANUAL

        logging.getLogger("user_level_log").info(msg)

    def get_viewport_info(self):
        """Get information about current "view port".

        Get information about current "view port" video dimension, beam position,
        pixels per mm, returns a dictionary with the format:

            data = {"pixelsPerMm": pixelsPerMm,
                    "imageWidth": width,
                    "imageHeight": height,
                    "format": fmt,
                    "sourceIsScalable": source_is_scalable,
                    "scale": scale,
                    "videoSizes": video_sizes,
                    "position": position,
                    "shape": shape,
                    "size_x": sx, "size_y": sy}

        :returns: Dictionary with view port data, with format described above
        :rtype: dict
        """
        fmt, source_is_scalable = "MJPEG", False

        if self.app.CONFIG.app.VIDEO_FORMAT == "MPEG1":
            fmt, source_is_scalable = "MPEG1", True
            video_sizes = HWR.beamline.sample_view.camera.get_available_stream_sizes()
            (width, height, scale) = HWR.beamline.sample_view.camera.get_stream_size()
        else:
            scale = 1
            width = HWR.beamline.sample_view.camera.get_width()
            height = HWR.beamline.sample_view.camera.get_height()
            video_sizes = [(width, height)]

        pixels_per_mm = HWR.beamline.diffractometer.get_pixels_per_mm()

        return {
            "pixelsPerMm": pixels_per_mm,
            "imageWidth": width,
            "imageHeight": height,
            "format": fmt,
            "sourceIsScalable": source_is_scalable,
            "scale": scale,
            "videoSizes": video_sizes,
            "videoHash": HWR.beamline.sample_view.camera.stream_hash,
            "videoURL": self.app.CONFIG.app.VIDEO_STREAM_URL,
        }

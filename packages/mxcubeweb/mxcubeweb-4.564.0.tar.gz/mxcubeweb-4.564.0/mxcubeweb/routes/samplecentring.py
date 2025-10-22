import io
import json
import logging

from flask import (
    Blueprint,
    Response,
    jsonify,
    request,
    send_file,
)
from mxcubecore import HardwareRepository as HWR


# Disabling C901 function is too complex (19)
def init_route(app, server, url_prefix):  # noqa: C901
    bp = Blueprint("sampleview", __name__, url_prefix=url_prefix)

    @bp.route("/camera/snapshot", methods=["POST"])
    @server.restrict
    def snapshot():
        """Take snapshot of the sample view.

        ``data = {"overlay": overlay_data}``
        ``overlay`` is the image data to overlay on sample image,
        it should normally contain the data of shapes drawn on canvas.

        Returns:
            Overlayed image URI, if successful.
            Status code ``500`` otherwise.
        """
        try:
            overlay = json.loads(request.data).get("overlay")
            mimetype, overlay_data = overlay.split(",")

            # Check if send data is a jpeg image
            if "image/jpeg" not in mimetype:
                msg = "Image type should be jpeg"
                raise ValueError(msg)

            image = HWR.beamline.sample_view.take_snapshot(
                overlay_data=overlay_data,
            )

            b = io.BytesIO()
            image.save(b, "JPEG")
            b.seek(0)

            return send_file(
                b,
                mimetype="image/jpeg",
                as_attachment=True,
                download_name="snapshot.jpeg",
            )
        except Exception:
            logging.getLogger("MX3.HWR").exception("Taking a snapshot failed")
            return jsonify({"error": "Taking a snapshot failed"})

    @bp.route("/camera", methods=["GET"])
    @server.restrict
    def get_image_data():
        """Get size of the image of the diffractometer.

        :response Content-type:application/json, example::
            {
                "imageHeight": 576,
                "imageWidth": 768,
                "pixelsPerMm": [1661.1295681063123, 1661.1295681063123],
            }

        :statuscode: 200: no error
        :statuscode: 409: error
        """
        data = app.sample_view.get_viewport_info()

        resp = jsonify(data)
        resp.status_code = 200
        return resp

    @bp.route("/camera", methods=["POST"])
    @server.restrict
    def set_image_size():
        params = request.get_json()

        res = app.sample_view.set_image_size(
            float(params["width"]), float(params["height"])
        )

        resp = jsonify(res)
        resp.status_code = 200
        return resp

    @bp.route("/centring/<point_id>/moveto", methods=["PUT"])
    @server.require_control
    @server.restrict
    def move_to_centred_position(point_id):
        """Move to the given centred position.

        :parameter id: centred position identifier, integer
        :statuscode: 200: no error
        :statuscode: 409: error
        """
        point = app.sample_view.move_to_centred_position(point_id)

        if point:
            return Response(status=200)
        return Response(status=409)

    @bp.route("/shapes", methods=["GET"])
    @server.restrict
    def get_shapes():
        """Retrieve all the stored centred positions.

        :response Content-type: application/json, the stored centred positions.
        :statuscode: 200: no error
        :statuscode: 409: error
        """
        shapes = app.sample_view.get_shapes()

        resp = jsonify(shapes)
        resp.status_code = 200
        return resp

    @bp.route("/shapes", methods=["POST"])
    @server.require_control
    @server.restrict
    def update_shapes():
        """Update shape information.

        :parameter shape_data: dict with shape information (id, type, ...)
        :response Content-type: application/json, the stored centred positions.
        :statuscode: 200: no error
        :statuscode: 409: error
        """
        shapes = request.get_json().get("shapes", [])

        resp = jsonify(app.sample_view.update_shapes(shapes))
        resp.status_code = 200

        return resp

    @bp.route("/shapes/<sid>", methods=["DELETE"])
    @server.require_control
    @server.restrict
    def delete_shape(sid):
        """Retrieve all the stored centred positions.

        :response Content-type: application/json, the stored centred positions.
        :statuscode: 200: no error
        :statuscode: 409: error
        """
        HWR.beamline.sample_view.delete_shape(sid)
        return Response(status=200)

    @bp.route("/shapes/rotate_to", methods=["POST"])
    @server.require_control
    @server.restrict
    def rotate_to():
        """Rotate Phi to the position where the given shape was defined.

        :parameter sid: The shape id
        :response Content-type: application/json, the stored centred positions.
        :statuscode: 200: no error
        :statuscode: 409: error
        """
        sid = request.get_json().get("sid", -1)

        try:
            app.sample_view.rotate_to(sid)
        except Exception:
            resp = Response(status=409)
        else:
            resp = Response(status=200)

        return resp

    @bp.route("/centring/start_click_centring", methods=["PUT"])
    @server.require_control
    @server.restrict
    def centre_click():
        """Start Click centring procedure.

        :statuscode: 200: no error
        :statuscode: 409: error
        """
        try:
            data = app.sample_view.start_manual_centring()
        except Exception:
            msg = "Could not start %s click centring"
            logging.getLogger("MX3.HWR").exception(
                msg, HWR.beamline.config.click_centring_num_clicks
            )
            resp = (
                "Could not move motor",
                409,
                {"Content-Type": "application/json"},
            )
        else:
            resp = jsonify(data)
            resp.status_code = 200

        return resp

    @bp.route("/centring/abort", methods=["PUT"])
    @server.require_control
    @server.restrict
    def abort_centring():
        """Abort centring procedure.

        :statuscode: 200: no error
        :statuscode: 409: error
        """
        app.sample_view.abort_centring()
        return Response(status=200)

    @bp.route("/centring/click", methods=["PUT"])
    @server.require_control
    @server.restrict
    def click():
        """The click method needs the input from the user.

        A running click centring procedure must be set before.

        :request Content-type: application/json, integer positions of the clicks,
                            {clickPos={"x": 123,"y": 456}}
        :response Content-type: application/json, integer, number of clicks
                                left {'clickLeft': 3 | 2 | 1}
        :statuscode: 200: no error
        :statuscode: 409: error
        """
        pos = json.loads(request.data).get("clickPos", None)

        data = app.sample_view.centring_handle_click(pos["x"], pos["y"])

        resp = jsonify(data)
        resp.status_code = 200
        return resp

    @bp.route("/centring/accept", methods=["PUT"])
    @server.require_control
    @server.restrict
    def accept_centring():
        """Accept the centring position."""
        HWR.beamline.diffractometer.accept_centring()
        return Response(status=200)

    @bp.route("/movetobeam", methods=["PUT"])
    @server.require_control
    @server.restrict
    def move_to_beam():
        """Go to the beam position from the given (x, y) position."""
        pos = json.loads(request.data).get("clickPos")

        app.sample_view.move_to_beam(pos["x"], pos["y"])

        return Response(status=200)

    @bp.route("/centring/centring_method", methods=["PUT"])
    @server.require_control
    @server.restrict
    def set_centring_method():
        """Set automatic (lucid) centring procedure when mounting samples.

        :statuscode: 200: no error
        :statuscode: 409: error
        """
        method = json.loads(request.data).get("centringMethod", None)
        app.sample_view.set_centring_method(method)
        return Response(status=200)

    return bp

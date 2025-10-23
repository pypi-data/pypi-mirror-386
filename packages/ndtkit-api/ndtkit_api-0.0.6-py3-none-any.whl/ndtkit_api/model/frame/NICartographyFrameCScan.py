from typing import Any, List
from ...ndtkit_socket_connection import call_api_method
from .NICartographyFrame import NICartographyFrame


class NICartographyFrameCScan(NICartographyFrame):

    def get_identifier(self) -> int:
        return self._java_object.getIdentifier()

    def set_identifier(self, id: int) -> None:
        return self._java_object.setIdentifier(id)

    def get_x_resolution(self) -> float:
        return self._java_object.getXResolution()

    def get_y_resolution(self) -> float:
        return self._java_object.getYResolution()

    def get_resolution(self):
        return self._java_object.getResolution()

    def get_x_origin(self) -> float:
        return self._java_object.getXOrigin()

    def get_intrinsic_x_origin(self) -> float:
        return self._java_object.getIntrinsicXOrigin()

    def get_y_origin(self) -> float:
        return self._java_object.getYOrigin()

    def get_intrinsic_y_origin(self) -> float:
        return self._java_object.getIntrinsicYOrigin()

    def get_flat_data(self):
        return self._java_object.getFlatData()

    def get_data_bound(self, roi) -> List[List[float]]:
        return self._java_object.getDataBound(roi)

    def get_flat_data(self, roi) -> List[Any]:
        return self._java_object.getFlatData(roi)

    def add_processing_into_historic_list(self, text: str) -> None:
        return self._java_object.addProcessingIntoHistoricList(text)

    def get_file_path(self) -> str:
        return self._java_object.getFilePath()

    def set_automation_identifier(self, report_identifier: str) -> None:
        return self._java_object.setAutomationIdentifier(report_identifier)

    def get_automation_identifier(self) -> str:
        return self._java_object.getAutomationIdentifier()

    def get_unit(self):
        return self._java_object.getUnit()

    def get_palette(self):
        return self._java_object.getPalette()

    def load_palette(self, palette_pathname: str) -> None:
        return self._java_object.loadPalette(palette_pathname)

    def get_defects_detection(self):
        return self._java_object.getDefectsDetection()

    def zoom(self, x: float, y: float, width: float, height: float, ignore_ratio: bool) -> None:
        return self._java_object.zoom(x, y, width, height, ignore_ratio)

    def zoom(self, x: float, y: float, width: float, height: float) -> None:
        return self._java_object.zoom(x, y, width, height)

    def rotate(self, angle: int) -> None:
        return self._java_object.rotate(angle)

    def get_type(self):
        return self._java_object.getType()

    def horizontal_symmetry(self) -> None:
        return self._java_object.horizontalSymmetry()

    def vertical_symmetry(self) -> None:
        return self._java_object.verticalSymmetry()

    def get_amplitude_reference(self) -> float:
        return self._java_object.getAmplitudeReference()

    def get_velocity(self) -> float:
        return self._java_object.getVelocity()

    def get_ply_thickness(self) -> float:
        return self._java_object.getPlyThickness()

    def get_screenshot(self, representation_type, display_palette: bool, display_roi_layer: bool, display_mask_layer: bool, display_defect_layer: bool, display_dressing_layer: bool, display_rulers: bool, display_at_real_size: bool):
        return self._java_object.getScreenshot(representation_type, display_palette, display_roi_layer, display_mask_layer, display_defect_layer, display_dressing_layer, display_rulers, display_at_real_size)

    def set_file_path(self, filepath: str) -> None:
        return self._java_object.setFilePath(filepath)

    def set_unit_without_conversion(self, unit) -> None:
        return self._java_object.setUnitWithoutConversion(unit)

    def set_resolution_unit(self, unit) -> None:
        return self._java_object.setResolutionUnit(unit)

    def set_y_origin_position(self, position_in_mm: float) -> None:
        return self._java_object.setYOriginPosition(position_in_mm)

    def set_x_origin_position(self, position_in_mm: float) -> None:
        return self._java_object.setXOriginPosition(position_in_mm)

    def get_comment(self) -> str:
        return self._java_object.getComment()

    def set_comment(self, comment: str) -> None:
        return self._java_object.setComment(comment)

    def get_min_value(self) -> float:
        return self._java_object.getMinValue()

    def get_max_value(self) -> float:
        return self._java_object.getMaxValue()

    def get_metadata(self, metadata_id: str) -> Any:
        return self._java_object.getMetadata(metadata_id)

    def set_metadata(self, metadata_id: str, metadata: Any) -> None:
        return self._java_object.setMetadata(metadata_id, metadata)

    def apply_zoom(self, zoom_fit) -> None:
        return self._java_object.applyZoom(zoom_fit)

    def get_event_manager(self):
        return self._java_object.getEventManager()

    def is_still_displayed(self) -> bool:
        return self._java_object.isStillDisplayed()

    def request_focus(self) -> None:
        return self._java_object.requestFocus()

    def get_zoom_factor_x(self) -> float:
        return self._java_object.getZoomFactorX()

    def get_zoom_factor_y(self) -> float:
        return self._java_object.getZoomFactorY()

    def get_dynamic_layer_manager(self):
        return self._java_object.getDynamicLayerManager()

    def refresh_layers(self) -> None:
        return self._java_object.refreshLayers()

    def duplicate(self):
        return self._java_object.duplicate()

    def json_of_scan_reader_parameter(self) -> str:
        return self._java_object.jsonOfScanReaderParameter()

    def set_auto_update_data(self, auto_update_data: bool) -> None:
        return self._java_object.setAutoUpdateData(auto_update_data)

    def update_data(self, update_palette: bool) -> None:
        return self._java_object.updateData(update_palette)

    def get_projection_cuboid(self):
        return self._java_object.getProjectionCuboid()

    def get_position3d(self, real_x: float, real_y: float):
        return self._java_object.getPosition3d(real_x, real_y)

    def get_horizontal_echodynamic_curve(self):
        return self._java_object.getHorizontalEchodynamicCurve()

    def get_vertical_echodynamic_curve(self):
        return self._java_object.getVerticalEchodynamicCurve()

    def get_data(self, roi=None) -> list[list[float]]:
        if (roi):
            return self._java_object.get_data(roi)

        parameters = [
            {
                "type": "agi.ndtkit.api.model.frame.NICartographyFrameCScan",
                "value": self.get_uuid(),
            }
        ]
        return call_api_method("agi.ndtkit.api.model.frame", "NICartographyFrameCScan", "getData", parameters)

    def set_data(self, data: list[list[float]]):
        parameters = [
            {
                "type": "agi.ndtkit.api.model.frame.NICartographyFrameCScan",
                "value": self.get_uuid(),
            },
            {
                "type": "float[][]",
                "value": str(data)
            }
        ]
        call_api_method("agi.ndtkit.api.model.frame", "NICartographyFrameCScan", "setData", parameters)

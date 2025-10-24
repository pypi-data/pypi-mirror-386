from .NICartographyFrame import NICartographyFrame
from ...model.scans.ascan.NIAScan import NIAScan
from py4j.java_gateway import JavaObject
from typing import Any, List


class NICartographyFrameAScan(NICartographyFrame):
    """Base class for NICartographyFrameAScan, generated from Java API."""

    def __init__(self, java_object: JavaObject):
        super().__init__(java_object)
        self._java_object = java_object

    def get_file_path(self) -> str:
        return self._java_object.getFilePath()

    def get_raw_data_values(self, row: int, column: int) -> NIAScan:
        return self._java_object.getRawDataValues(row, column)

    def get_raw_data_values_no_factor(self, row: int, column: int) -> NIAScan:
        return self._java_object.getRawDataValuesNoFactor(row, column)

    def get_ascan_length(self) -> int:
        return self._java_object.getAscanLength()

    def get_row(self, row_index: int) -> list[NIAScan]:
        row_of_ascans = self._java_object.getRow(row_index)
        return [NIAScan(ascan) for ascan in row_of_ascans]

    def get_column(self, row_column: int) -> List[Any]:
        return self._java_object.getColumn(row_column)

    def get_data_values(self, row: int, column: int) -> NIAScan:
        return self._java_object.getDataValues(row, column)

    def get_row_number(self) -> int:
        return self._java_object.getRowNumber()

    def get_column_number(self) -> int:
        return self._java_object.getColumnNumber()

    def set_file_path(self, filepath: str) -> None:
        return self._java_object.setFilePath(filepath)

    def get_x_resolution(self) -> float:
        return self._java_object.getXResolution()

    def get_y_resolution(self) -> float:
        return self._java_object.getYResolution()

    def get_num_rate(self) -> float:
        return self._java_object.getNumRate()

    def set_full_range_bscan(self) -> None:
        return self._java_object.setFullRangeBScan()

    def get_ascan_gates(self):
        return self._java_object.getAScanGates()

    def get_bscan_gate(self):
        return self._java_object.getBScanGate()

    def get_velocity_from_file(self) -> float:
        return self._java_object.getVelocityFromFile()

    def get_bscan_vertical_resolution(self) -> float:
        return self._java_object.getBScanVerticalResolution()

    def get_bscan_data(self, bscan_position: int) -> List[List[float]]:
        return self._java_object.getBScanData(bscan_position)

    def get_dscan_data(self, dscan_position: int) -> List[List[float]]:
        return self._java_object.getDScanData(dscan_position)

    def get_acquisition_type(self):
        return self._java_object.getAcquisitionType()

    def set_x_origin_position(self, x_offset: float) -> None:
        return self._java_object.setXOriginPosition(x_offset)

    def set_y_origin_position(self, y_offset: float) -> None:
        return self._java_object.setYOriginPosition(y_offset)

    def get_x_origin_position(self) -> float:
        return self._java_object.getXOriginPosition()

    def get_y_origin_position(self) -> float:
        return self._java_object.getYOriginPosition()

    def get_current_ascan(self) -> NIAScan:
        return self._java_object.getCurrentAscan()

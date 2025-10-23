from py4j.java_gateway import JavaObject


class NICartographyFrame:
    def __init__(self, java_object: JavaObject):
        self._java_object = java_object

    def minimize_frame(self, is_minimum: bool):
        return self._java_object.minimizeFrame(is_minimum)

    def set_title(self, title: str):
        return self._java_object.setTitle(title)

    def get_scan_type(self):
        return self._java_object.getScanType()

    def maximize_frame(self, is_maximum: bool):
        return self._java_object.maximizeFrame(is_maximum)

    def get_projection_cuboid(self):
        return self._java_object.getProjectionCuboid()

    def get_size(self):
        return self._java_object.getSize()

    def get_title(self):
        return self._java_object.getTitle()

    def json_of_scan_reader_parameter(self):
        return self._java_object.jsonOfScanReaderParameter()

    def get_uuid(self):
        return str(self._java_object.getUUID())

    def get_file_path(self):
        return self._java_object.getFilePath()

    def set_file_path(self, filepath: str):
        return self._java_object.setFilePath(filepath)

    def change_size(self, width: int, height: int):
        return self._java_object.changeSize(width, height)

    def close(self):
        return self._java_object.close()

    def get_ifi(self):
        return self._java_object.getIfi()

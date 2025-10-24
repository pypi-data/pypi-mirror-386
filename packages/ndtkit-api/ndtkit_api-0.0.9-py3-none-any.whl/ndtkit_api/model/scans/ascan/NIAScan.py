from py4j.java_gateway import JavaObject


class NIAScan:
    """Base class for NIAScan, generated from Java API."""

    def __init__(self, java_object: JavaObject, json_model=None):
        self._java_object = java_object
        self.json_model = json_model

    def get_all_tof_values_from_this_ascan_and_sub_ascans(self) -> list[float]:
        return self._java_object.getAllTofValuesFromThisAScanAndSubAscans()

    def get_all_amp_values_from_this_ascan_and_sub_ascans(self) -> list[float]:
        return self._java_object.getAllAmpValuesFromThisAScanAndSubAscans()

    def get_amp_values(self) -> list[float]:
        if self.json_model and "amp" in self.json_model:
            return self.json_model["amp"]
        return self._java_object.getAmpValues()

    def get_tof_values(self) -> list[float]:
        return self._java_object.getTofValues()

    def get_sub_ascans(self):
        return self._java_object.getSubAscans()

    def get_column(self) -> int:
        return self._java_object.getColumn()

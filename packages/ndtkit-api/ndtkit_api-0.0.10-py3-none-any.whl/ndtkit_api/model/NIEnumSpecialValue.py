from py4j.java_gateway import JavaObject
from ..ndtkit_socket_connection import gateway


class NIEnumSpecialValue:
    """Base class for NIAScanConfiguration, generated from Java API."""

    all_special_values = None

    def __init__(self, java_object: JavaObject):
        self._java_object = java_object

    @staticmethod
    def get_all_values() -> list[int]:
        if NIEnumSpecialValue.all_special_values is None:
            special_values_java = gateway.jvm.agi.ndtkit.api.model.NIEnumSpecialValue.getAllValues()
            NIEnumSpecialValue.all_special_values = [int(special_value) for special_value in special_values_java] if special_values_java else []
        return NIEnumSpecialValue.all_special_values

    @staticmethod
    def is_special_value(value: float) -> bool:
        for special_value in NIEnumSpecialValue.get_all_values():
            if abs(special_value - value) < 1E-6:
                return True
        return False

from py4j.java_gateway import JavaObject


class NIAScanGate:
    """Base class for NIAScanGate, generated from Java API."""

    def __init__(self, java_object: JavaObject):
        self._java_object = java_object

    def set_velocity(self, us_velocity: float) -> None:
        return self._java_object.setVelocity(us_velocity)

    def get_start(self) -> float:
        return  self._java_object.getStart()

    def get_end(self) -> float:
        return self._java_object.getEnd()

    def get_height(self) -> float:
        return self._java_object.getHeight()

    def get_name(self) -> str :
        return self._java_object.getName()
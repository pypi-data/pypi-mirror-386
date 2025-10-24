from py4j.java_gateway import JavaObject


class NIColorPalette:
    """Base class for NIAScanConfiguration, generated from Java API."""

    def __init__(self, java_object: JavaObject):
        self._java_object = java_object

    def real_limits(self):
        self._java_object.realLimits()

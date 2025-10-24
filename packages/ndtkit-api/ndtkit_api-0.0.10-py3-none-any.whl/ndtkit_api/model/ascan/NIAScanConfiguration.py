from py4j.java_gateway import JavaObject
from .NIAScanGate import NIAScanGate

class NIAScanConfiguration:
    """Base class for NIAScanConfiguration, generated from Java API."""

    def __init__(self, java_object: JavaObject):
        self._java_object = java_object


    def get_gates(self) -> list[NIAScanGate]:
      return [NIAScanGate(gate) for gate in self._java_object.getGates()]

    def get_gain(self) -> float:
        return self._java_object.getGain();

    def get_fft_gate(self):
        return NIAScanGate(self._java_object.getFftGate());
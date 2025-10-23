from .ndtkit_socket_connection import gateway
from .model.frame.NICartographyFrameAScan import NICartographyFrameAScan
from .model.ascan.NIAScanConfiguration import NIAScanConfiguration


def open_ascan(ascanFilePath: str, scanId: int = -1, displayResult: bool = True) -> NICartographyFrameAScan:
    return NICartographyFrameAScan(gateway.jvm.agi.ndtkit.api.NDTKitAScanInterface.openAScan(ascanFilePath, scanId, displayResult))

def read_nkap_file(nkap_file: str) -> NIAScanConfiguration:
    return NIAScanConfiguration(gateway.jvm.agi.ndtkit.api.NDTKitAScanInterface.readNKAPFile(nkap_file))
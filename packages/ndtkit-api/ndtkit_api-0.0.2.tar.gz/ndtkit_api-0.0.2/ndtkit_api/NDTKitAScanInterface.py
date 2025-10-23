from .ndtkit_socket_connection import gateway
from .model.frame.NICartographyFrameAScan import NICartographyFrameAScan


def openAScan(ascanFilePath: str, scanId: int = -1, displayResult: bool = True) -> NICartographyFrameAScan:
    return NICartographyFrameAScan(gateway.jvm.agi.ndtkit.api.NDTKitAScanInterface.openAScan(ascanFilePath, scanId, displayResult))

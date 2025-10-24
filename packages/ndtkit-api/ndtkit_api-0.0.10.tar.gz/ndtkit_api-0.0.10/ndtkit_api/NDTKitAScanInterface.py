from .ndtkit_socket_connection import gateway
from .model.frame.NICartographyFrameAScan import NICartographyFrameAScan
from .model.ascan.NIAScanConfiguration import NIAScanConfiguration


def open_ascan(ascanFilePath: str, scanId: int = -1, displayResult: bool = True) -> NICartographyFrameAScan:
    ascan_frame_java = gateway.jvm.agi.ndtkit.api.NDTKitAScanInterface.openAScan(ascanFilePath, scanId, displayResult)
    return NICartographyFrameAScan(ascan_frame_java)  # pyright: ignore[reportArgumentType]


def read_nkap_file(nkap_file: str) -> NIAScanConfiguration:
    ascan_config = gateway.jvm.agi.ndtkit.api.NDTKitAScanInterface.readNKAPFile(nkap_file)
    return NIAScanConfiguration(ascan_config)  # pyright: ignore[reportArgumentType]

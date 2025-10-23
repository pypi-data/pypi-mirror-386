from .ndtkit_socket_connection import gateway, call_api_method
from .model.frame.NICartographyFrameCScan import NICartographyFrameCScan


def openCScan(cscanFilePath: str, displayResult: bool = True) -> NICartographyFrameCScan:
    return NICartographyFrameCScan(gateway.jvm.agi.ndtkit.api.NDTKitCScanInterface.openCScan(cscanFilePath, displayResult)[0])


def saveCscan(cscan: NICartographyFrameCScan, filepath: str):
    return gateway.jvm.agi.ndtkit.api.NDTKitCScanInterface.saveCscan(cscan._java_object, filepath)


def createCscan(data: list[list[float]], acquisition_name: str, x_res: float, y_res: float) -> NICartographyFrameCScan:
    parameters = [
        {
            "type": "float[][]",
            "value": str(data)
        },
        {
            "type": "java.lang.String",
            "value": acquisition_name
        },
        {
            "type": "float",
            "value": x_res
        },
        {
            "type": "float",
            "value": y_res
        }
    ]
    return call_api_method("agi.ndtkit.api", "NDTKitCScanInterface", "createCscan", parameters)

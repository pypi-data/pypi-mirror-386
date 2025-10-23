class VisionBrowserAPIError(Exception): pass
class ProfileAlreadyStartingError(VisionBrowserAPIError): pass
def raise_from_response(response: dict) -> None:
    if isinstance(response, dict):
        if "error" in response:
            raise VisionBrowserAPIError(response["error"])
        if "data" in response and "error" in response["data"]:
            raise VisionBrowserAPIError(response["data"]["error"])

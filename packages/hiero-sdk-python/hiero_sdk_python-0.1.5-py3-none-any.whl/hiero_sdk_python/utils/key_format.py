from hiero_sdk_python.hapi.services.basic_types_pb2 import Key

def format_key(key: Key) -> str:
    """
    Converts a protobuf Key into a nicely formatted string:
      - If key is None, return "None"
      - If ed25519, show "ed25519(hex-encoded)"
      - If thresholdKey, keyList, or something else, show a short label.
    """
    if key is None:
        return "None"

    if key.HasField("ed25519"):
        return f"ed25519({key.ed25519.hex()})"
    elif key.HasField("thresholdKey"):
        return "thresholdKey(...)"
    elif key.HasField("keyList"):
        return "keyList(...)"
    elif key.HasField("contractID"):
        return f"contractID({key.contractID})"

    return str(key).replace("\n", " ")

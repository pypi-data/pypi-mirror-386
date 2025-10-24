import json
import requests
from importlib import resources

Offsets = {}
def ParseOffsets(*DataSources):
    for _, Data in enumerate(DataSources, start=1):
        for OffsetName in Data:
            try:
                FormattedOffsetName = OffsetName.replace(" ", "")
                OffsetHexadecimalValue = Data[OffsetName]

                Offsets[FormattedOffsetName] = int(OffsetHexadecimalValue, 16)
            except (ValueError, TypeError):
                pass


OffsetsRequest = requests.get("https://offsets.ntgetwritewatch.workers.dev/offsets.json")

try:
    LoadedOffsetsRequest = requests.get(
        "https://raw.githubusercontent.com/notpoiu/RobloxMemoryAPI/refs/heads/main/src/robloxmemoryapi/data/offsets.json"
    )
    LoadedOffsetsRequest.raise_for_status()

    LoadedOffsets = LoadedOffsetsRequest.json()
except Exception:
    try:
        with resources.files("robloxmemoryapi.data").joinpath("offsets.json").open("r", encoding="utf-8") as f:
            LoadedOffsets = json.load(f)
    except Exception:
        # Fallback defaults
        LoadedOffsets = {
            "Text": "0xC10",
            "Character": "0x340",
            "PrimaryPart": "0x260",
        }

ParseOffsets(LoadedOffsets, OffsetsRequest.json())

# CFrame Offsets
RotationMatriciesLengthBytes = 3 * 3 * 4

Offsets["CameraCFrame"] = Offsets["CameraPos"] - RotationMatriciesLengthBytes
Offsets["CFrame"] = Offsets["Position"] - RotationMatriciesLengthBytes


import re
from typing import Any

import pandas as pd

from imxInsights import ImxSingleFile
from imxInsights.repo.imxRepoProtocol import ImxRepoProtocol


def has_dot_number_dot(s: str) -> bool:
    """Check if a string contains a dot-number-dot pattern."""
    return bool(re.search(r"\.\d+\.", s))


def extract_numeric(ref: str) -> int:
    """Extracts the numeric part of a reference string for sorting."""
    match = re.search(r"\d+", ref)
    return int(match.group()) if match else 0


def create_base_switch(data: dict[str, str]) -> dict[str, str]:
    """Create a base switch entry from the data."""
    return {
        "ref": data["@switchMechanismRef"],
        "position": data["@position"],
        "type": "BaseSwitch",
    }


def extract_flank_protection_extension_data(
    data: dict[str, str],
) -> list[dict[str, str]]:
    """Extract flank protection details from the data."""
    results = [create_base_switch(data)]

    flank_protections = {}

    for key, value in data.items():
        if has_dot_number_dot(key):
            match = re.match(r"(\w+FlankProtection)\.(\d+)\.@(\w+)", key)
            if match:
                flank_type, index, attr = match.groups()
                unique_key = f"{flank_type}.{index}"

                if unique_key not in flank_protections:
                    flank_protections[unique_key] = {
                        "ref": data.get(f"{flank_type}.{index}.@switchMechanismRef"),
                        "position": data.get(f"{flank_type}.{index}.@position"),
                        "type": flank_type,
                    }

        elif re.match(r"(Mandatory|Optional)FlankProtection\.@", key):
            flank_type = key.split(".@")[0]
            if flank_type not in flank_protections:
                flank_protections[flank_type] = {
                    "ref": data.get(f"{flank_type}.@switchMechanismRef"),
                    "position": data.get(f"{flank_type}.@position"),
                    "type": flank_type,
                }

    results.extend(
        {
            key: {
                k: (v if isinstance(v, str) else str(v) if v is not None else "")
                for k, v in value.items()
            }
            for key, value in flank_protections.items()
        }.values()
    )
    return results


def get_flank_protections(
    imx_container: ImxRepoProtocol,
) -> list[list[dict[str, str]]]:
    """Extract and process flank protection data."""
    if imx_container.imx_version:
        major_imx_version = imx_container.imx_version.split(".")[0]
        if major_imx_version in ["11", "12"]:
            raise NotImplementedError(
                "FlankProtection overview not supported for imx version"
                f" {imx_container.imx_version}"
            )
    else:
        raise ValueError("IMX version is not defined.")

    flank_protections: list[list[dict[str, str]]] = []
    switch_mechs = imx_container.get_by_types(["SwitchMechanism"])

    for switch_mech in switch_mechs:
        for item in switch_mech.imx_extensions:
            if item.path == "FlankProtectionConfiguration":
                flank_data = extract_flank_protection_extension_data(item.properties)
                for item_2 in flank_data:
                    found_item = imx_container.find(item_2["ref"])
                    if found_item:
                        item_2["ref"] = found_item.name
                    else:
                        item_2["ref"] = (
                            "NOT_FOUND"  # Or handle the missing reference as needed
                        )

                flank_protections.append(flank_data)

    flank_protections.sort(
        key=lambda data: extract_numeric(
            next(item["ref"] for item in data if item["type"] == "BaseSwitch")
        )
    )
    return flank_protections


def flank_protection_to_dataframe(
    flank_protections: list[list[dict[str, str]]],
) -> pd.DataFrame:
    """Convert flank protection details into a Pandas DataFrame."""
    data: list[list[Any]] = []
    for data_list in flank_protections:
        base_switch = next(
            (item for item in data_list if item["type"] == "BaseSwitch"), None
        )
        if not base_switch:
            continue

        filtered_flank_protections: list[dict[str, str]] = [
            item
            for item in data_list
            if item["type"] in {"MandatoryFlankProtection", "OptionalFlankProtection"}
        ]
        for flank in filtered_flank_protections:
            data.append(
                [
                    base_switch.get("ref"),
                    base_switch.get("position"),
                    flank.get("ref"),
                    flank.get("position"),
                    flank.get("type"),
                ]
            )

    return pd.DataFrame(
        data,
        columns=[
            "Base Switch Ref",
            "Base Position",
            "Flank Protection Ref",
            "Flank Position",
            "Type",
        ],
    )


if __name__ == "__main__":
    imx_situation = ImxSingleFile(
        r"C:\Users\marti\OneDrive - ProRail BV\ENL\raakvlakproject gn d20\O_R-438700_000_100631_DO_2025-03-28T15_41_51Z\O_R-438700_000_100631_DO_2025-03-28T15_41_51Z.xml"
    )
    if imx_situation.new_situation:
        flanks = get_flank_protections(imx_situation.new_situation)
        df = flank_protection_to_dataframe(flanks)
        df.to_excel("flankConfigurationOverview.xlsx")
        print(df)

import re

import pandas as pd

from imxInsights import ImxSingleFile
from imxInsights.repo.imxRepoProtocol import ImxRepoProtocol


def has_dot_number_dot(s: str) -> bool:
    """Check if a string contains a dot-number-dot pattern."""
    return bool(re.search(r'\.\d+\.', s))


def extract_numeric(ref: str) -> int:
    """Extracts the numeric part of a reference string for sorting."""
    match = re.search(r'\d+', ref)
    return int(match.group()) if match else 0


def create_base_switch(data: dict[str, str]) -> dict[str, str]:
    """Create a base switch entry from the data."""
    return {
        "ref": data["@switchMechanismRef"],
        "position": data["@position"],
        "type": "BaseSwitch"
    }


def extract_flank_protection_extension_data(data: dict[str, str]) -> list[dict[str, str]]:
    """Extract flank protection details from the data."""
    results = [create_base_switch(data)]

    flank_protections = {}

    for key, value in data.items():
        if has_dot_number_dot(key):
            match = re.match(r'(\w+FlankProtection)\.(\d+)\.@(\w+)', key)
            if match:
                flank_type, index, attr = match.groups()
                unique_key = f"{flank_type}.{index}"

                if unique_key not in flank_protections:
                    flank_protections[unique_key] = {
                        "ref": data.get(f"{flank_type}.{index}.@switchMechanismRef"),
                        "position": data.get(f"{flank_type}.{index}.@position"),
                        "type": flank_type
                    }

        elif re.match(r'(Mandatory|Optional)FlankProtection\.@', key):
            flank_type = key.split(".@")[0]
            if flank_type not in flank_protections:
                flank_protections[flank_type] = {
                    "ref": data.get(f"{flank_type}.@switchMechanismRef"),
                    "position": data.get(f"{flank_type}.@position"),
                    "type": flank_type
                }

    results.extend(flank_protections.values())

    return results


def get_flank_protections(imx_container: ImxRepoProtocol) -> list[list[dict[str, str]]]:
    """Extract and process flank protection data."""
    major_imx_version = imx_container.imx_version.split(".")[0]
    if major_imx_version in ["11", "12"]:
        raise NotImplementedError(f"FlankProtection overview not supported for imx version {imx_container.imx_version}")

    flank_protections = []
    switch_mechs = imx_container.get_by_types(["SwitchMechanism"])

    for switch_mech in switch_mechs:
        for item in switch_mech.imx_extensions:
            if item.path == 'FlankProtectionConfiguration':
                flank_data = extract_flank_protection_extension_data(item.properties)
                for item_2 in flank_data:
                    item_2['ref'] = imx_container.find(item_2['ref']).name
                flank_protections.append(flank_data)
    flank_protections.sort(key=lambda data: extract_numeric(next(item['ref'] for item in data if item['type'] == 'BaseSwitch')))
    return flank_protections


def flank_protection_to_dataframe(flank_protections: list[list[dict[str, str]]]) -> pd.DataFrame:
    """Convert flank protection details into a Pandas DataFrame."""
    data = []
    for data_list in flank_protections:
        base_switch = next((item for item in data_list if item["type"] == "BaseSwitch"), None)
        if not base_switch:
            continue

        flank_protections = [item for item in data_list if item["type"] in {"MandatoryFlankProtection", "OptionalFlankProtection"}]
        for flank in flank_protections:
            data.append([
                base_switch['ref'],
                base_switch['position'],
                flank['ref'],
                flank['position'],
                flank['type']
            ])

    return pd.DataFrame(data, columns=["Base Switch Ref", "Base Position", "Flank Protection Ref", "Flank Position", "Type"])



if __name__ == "__main__":
    imx_situation = ImxSingleFile(r"C:\Users\marti\OneDrive - ProRail BV\ENL\raakvlakproject gn d20\O_R-438700_000_100631_DO_2025-03-28T15_41_51Z\O_R-438700_000_100631_DO_2025-03-28T15_41_51Z.xml")
    flanks = get_flank_protections(imx_situation.new_situation)
    df = flank_protection_to_dataframe(flanks)
    df.to_excel("flankConfigurationOverview.xlsx")
    print(df)

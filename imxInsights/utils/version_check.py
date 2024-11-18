import re
import urllib.request
import warnings

from packaging import version

GITHUB_INIT_URL = "https://raw.githubusercontent.com/open-imx/imxInsights/refs/heads/main/imxInsights/__init__.py"


def fetch_raw_init_file(url: str) -> str | None:
    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                return response.read().decode("utf-8")
            else:
                warnings.warn(
                    f"❌ Could not fetch version info from GitHub (HTTP {response.status})."
                )
    except Exception as e:
        warnings.warn(f"❌ Error fetching the version from GitHub: {e}")
    return None


def extract_version_from_text(text: str) -> str | None:
    match = re.search(r"__version__ = ['\"]([^'\"]+)['\"]", text)
    if match:
        return match.group(1).strip()
    warnings.warn("❌ Could not find the __version__ in the raw file.")
    return None


def get_version_from_raw_file() -> str | None:
    raw_text = fetch_raw_init_file(GITHUB_INIT_URL)
    return extract_version_from_text(raw_text) if raw_text else None


def compare_versions(current_version_str: str, latest_version_str: str):
    try:
        current_version = version.parse(current_version_str)
        latest_version = version.parse(latest_version_str)

        if current_version < latest_version:
            warnings.warn(
                f"⚠️ WARNING: You are using imxInsights version {current_version_str}, but version {latest_version} is available. "
                "Please update to the latest version.",
                UserWarning,
            )
        elif current_version > latest_version:
            warnings.warn(
                f"⚠️ WARNING: You are using a development version ({current_version_str}) "
                f"ahead of the latest stable release ({latest_version}).",
                UserWarning,
            )
    except version.InvalidVersion as e:
        warnings.warn(f"❌ Invalid version format in comparison: {e}")


def check_for_updates(current_version_str: str):
    latest_version_str = get_version_from_raw_file()
    if latest_version_str:
        compare_versions(current_version_str, latest_version_str)

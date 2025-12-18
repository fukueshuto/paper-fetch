import os
import questionary
from typing import Dict, Any


def run_wizard():
    """Run the interactive configuration wizard."""
    print("Welcome to PaperFetch Configuration Wizard! 🧙‍♂️")
    print("This will guide you through creating a config.toml file.")
    print("-" * 50)

    # Core Settings
    source = questionary.select(
        "Default Search Source:", choices=["arxiv", "ieee", "3gpp"], default="arxiv"
    ).ask()

    search_limit = questionary.text(
        "Default Search Limit (number):",
        default="10",
        validate=lambda text: text.isdigit() or "Please enter a number",
    ).ask()

    download_limit = questionary.text(
        "Default Download Limit (empty for unlimited):", default=""
    ).ask()

    output_dir = questionary.text(
        "Default Output Directory:", default="downloads"
    ).ask()

    convert_md = questionary.confirm(
        "Enable Markdown Conversion by default?", default=False
    ).ask()

    # Advanced Settings
    configure_advanced = questionary.confirm(
        "Do you want to configure advanced settings (Wait Times, API Keys)?",
        default=False,
    ).ask()

    uspto_key = ""
    dl_wait_min = "10.0"
    dl_wait_max = "40.0"

    if configure_advanced:
        uspto_key = questionary.text("USPTO API Key (optional):", default="").ask()

        dl_wait_min = questionary.text(
            "Minimum Download Wait Time (seconds):",
            default="10.0",
            validate=lambda text: _is_float(text) or "Please enter a number",
        ).ask()

        dl_wait_max_default = str(float(dl_wait_min) + 30.0)
        dl_wait_max = questionary.text(
            "Maximum Download Wait Time (seconds):",
            default=dl_wait_max_default,
            validate=lambda text: _is_float(text) or "Please enter a number",
        ).ask()

    # Construct Config Dictionary
    config_data = {
        "core": {
            "default_source": source,
            "search_limit": int(search_limit),
            "download_limit": int(download_limit) if download_limit.isdigit() else None,
            "output_dir": output_dir,
            "convert_to_md": convert_md,
        },
        "advanced": {
            "download_wait_min": float(dl_wait_min),
            "download_wait_max": float(dl_wait_max),
            "search_wait_min": 0.0,  # Keep defaults for search
            "search_wait_max": 2.0,
        },
        "api_keys": {
            "uspto": uspto_key,
        },
        "3gpp": {"convert_to_pdf": True},
    }

    # Generate TOML Content manually (since pyproject.toml doesn't include toml writer)
    # We could use a library, but to keep dependencies minimal (standard lib only mostly),
    # we'll write a simple TOML serializer for this specific structure.
    toml_content = _generate_toml(config_data)

    target_path = os.path.join(os.getcwd(), "config.toml")

    if os.path.exists(target_path):
        overwrite = questionary.confirm(
            f"File {target_path} already exists. Overwrite?", default=False
        ).ask()
        if not overwrite:
            print("Aborted.")
            return

    try:
        with open(target_path, "w") as f:
            f.write(toml_content)
        print(f"\n✅ Configuration saved to: {target_path}")
    except Exception as e:
        print(f"\n❌ Failed to save config: {e}")


def _is_float(val: str) -> bool:
    try:
        float(val)
        return True
    except ValueError:
        return False


def _generate_toml(data: Dict[str, Any]) -> str:
    """Simple TOML generator for our dictionary structure."""
    lines = []

    # Core
    lines.append("[core]")
    for k, v in data["core"].items():
        lines.append(f"{k} = {_format_toml_value(v)}")
    lines.append("")

    # Advanced
    lines.append("[advanced]")
    for k, v in data["advanced"].items():
        lines.append(f"{k} = {_format_toml_value(v)}")
    lines.append("")

    # API Keys
    lines.append("[api_keys]")
    for k, v in data["api_keys"].items():
        # Ensure empty strings are quoted
        lines.append(f"{k} = {_format_toml_value(v)}")
    lines.append("")

    # 3GPP
    lines.append("[3gpp]")
    for k, v in data["3gpp"].items():
        lines.append(f"{k} = {_format_toml_value(v)}")
    lines.append("")

    return "\n".join(lines)


def _format_toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, str):
        return f'"{value}"'
    elif value is None:
        # TOML doesn't strictly have null, but usually omitted.
        # However, for our config structure, we might want to use a convention or just not write it?
        # Let's map None to empty string or 0 depending on context?
        # For download_limit, None means "no limit".
        # But since we are writing a file user will edit...
        # Let's just comment it out if None, or set a special value.
        # Simplest approach for this wizard: write explicit large number or -1?
        # Or just don't write it? The reader expects a key.
        # Let's write 'null' string if string, or just handle specifically.
        # Actually our reader uses tomllib.load(). TOML doesn't support None.
        # Common practice is to omit the key.
        # But here we are generating the file.
        # Let's change our strategy: if None, use 0 (for limit).
        # And handle 0 as unlimited in loading logic if needed?
        # CLI already handles 0 as unlimited.
        return "0"
    else:
        return str(value)

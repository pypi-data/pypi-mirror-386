"""Python module to convert JSON data to YAML format for RichTreeCLI."""


def build_yaml(json_data: dict) -> str:
    """Convert JSON data to YAML format."""
    import yaml  # noqa: PLC0415

    return yaml.safe_dump(json_data, sort_keys=False)

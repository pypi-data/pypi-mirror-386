"""Python module to build a JSON representation of a directory structure for RichTreeCLI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    from rich_tree_cli.main import RichTreeCLI


def build_json(cli: RichTreeCLI, path: Path) -> dict:
    """Build a dictionary representation of the directory structure."""
    if path == cli.root:
        tree_data: dict[str, str] = build_tree_dict(cli, path)
        return {
            "metadata": {
                "total_dirs": cli.dir_count,
                "total_files": cli.file_count,
                "root_path": str(path),
            },
            "tree": tree_data,
        }
    return build_tree_dict(cli, path)


def build_tree_dict(cli: RichTreeCLI, path: Path) -> dict:
    """Build a more compact tree representation."""
    result: dict[str, Any] = {}
    for item in cli.get_items(path):
        if cli.ignore_handler.should_ignore(item.path):
            continue
        if item.is_dir():
            result[item.name + "/"] = build_tree_dict(cli, item.path)
        else:
            result[item.name] = {"size": item.size, "lines": item.length}
    return result

"""Xml export for RichTreeCLI."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pathlib import Path

    from rich_tree_cli.main import RichTreeCLI


def build_xml(cli: RichTreeCLI) -> str:
    """Build an XML representation of the directory structure."""
    from xml.etree.ElementTree import Element, ElementTree, SubElement, indent  # noqa: PLC0415

    def add_element(path: Path, parent: Element) -> None:
        tag: Literal["directory", "file"] = "directory" if path.is_dir() else "file"
        element: Element = SubElement(parent, tag, name=path.resolve().name)
        if path.is_dir():
            for item in cli.get_items(path):
                if cli.ignore_handler.should_ignore(item.path):
                    continue
                add_element(item.path, element)
        else:
            element.set("size", str(path.stat().st_size))
            try:
                lines: int = len(path.read_text(encoding="utf-8").splitlines())
            except UnicodeDecodeError:
                lines = 0
            element.set("lines", str(lines))

    root_element: Element = Element(
        "structure",
        {
            "total_dirs": str(cli.dir_count),
            "total_files": str(cli.file_count),
            "root_path": str(cli.root.resolve()),
        },
    )
    add_element(cli.root, root_element)

    tree: ElementTree = ElementTree(root_element)
    indent(tree, space="  ")
    xml_io = io.StringIO()
    tree.write(xml_io, encoding="unicode")
    return xml_io.getvalue()

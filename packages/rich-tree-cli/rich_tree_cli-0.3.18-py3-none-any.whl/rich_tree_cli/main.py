"""Rich Tree CLI: A command-line interface for displaying directory trees in a rich format."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback
from typing import TYPE_CHECKING, Any

from rich.tree import Tree

from ._args import get_args
from ._get_console import get_console
from .constants import MetaDataChoice
from .export.icons import IconManager, get_mode
from .file_info import FileInfo
from .ignore_handler import IgnoreHandler
from .output_manager import OutputManager, RunResult

if TYPE_CHECKING:
    from argparse import Namespace

    from rich.console import Console


class RichTreeCLI:
    """RichTreeCLI class to build and display a directory tree with various options."""

    def __init__(
        self,
        directory: Path | str,
        output: Path | None = None,
        max_depth: int = 0,
        sort_order: str = "files",
        metadata: MetaDataChoice = "none",
        disable_color: bool = False,
        output_format: list | None = None,
        gitignore_path: Path | None = None,
        exclude: list[str] | None = None,
        no_console: bool = False,
        icons: str = "emoji",
        replace_path: Path | None = None,
        replace_tag: str | None = None,
    ) -> None:
        """Initialize the RichTree with a directory, optional output file, maximum depth, and sort order."""
        self.root = Path(directory)
        self.output: Path | None = output
        self.max_depth: int = abs(max_depth)
        self.sort_order: str = sort_order
        self.metadata: MetaDataChoice = metadata
        self.file_count = 0
        self.dir_count = 0
        self.ignore_handler = IgnoreHandler(gitignore_path)
        self.icon = IconManager(mode=get_mode(icons))
        if exclude:
            self.ignore_handler.add_patterns(exclude)
        self.output_format: list[str] = output_format or ["text"]
        self.disable_color: bool = disable_color
        self.no_console: bool = no_console
        self.output_console: Console = get_console(disable_color)
        self.replace_path: Path | None = replace_path
        self.replace_tag: str | None = replace_tag
        self.tree = Tree(f"{self.icon.folder_default}  {self.root.resolve().name}")

    def get_file_string(self, item: Path) -> str:
        """Generate a string representation of a file with its metadata."""
        is_symlink: bool = item.is_symlink()

        item_string: str = f"{self.icon.get(item)} {item.name}"

        if is_symlink:
            target: Path = item.resolve()
            item_string += f" -> {target.relative_to(item.parent)}"
        if self.metadata == "none":
            return item_string
        if self.metadata in ["size", "all"]:
            file_size: int = item.stat().st_size
            item_string += f" ({file_size} bytes)"
        if self.metadata in ["lines", "all"]:
            try:
                number_of_lines: int = len(item.read_text(encoding="utf-8").splitlines())
                item_string += f" ({number_of_lines} lines)"
            except UnicodeDecodeError:
                item_string += " (binary)"
        return item_string

    def get_items(self, path: Path) -> list[FileInfo]:
        """Get items in the directory, sorted by the specified order."""
        return (
            [FileInfo(item) for item in sorted(path.iterdir(), key=lambda x: (x.is_dir(), x.name.lower()))]
            if self.sort_order == "files"
            else [FileInfo(item) for item in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))]
        )

    def add_to_tree(self, path: Path, tree_node: Tree, current_depth: int = 0) -> None:
        """Recursively add items to the tree structure."""
        if self.max_depth and current_depth >= self.max_depth:
            return

        for item in self.get_items(path):
            if self.ignore_handler.should_ignore(item.path):
                continue
            is_dir: bool = item.is_dir()
            icon: str = item.to_string(self.icon, self.metadata)
            if is_dir:
                branch: Tree = (
                    tree_node.add(icon, highlight=True, style="bold green")
                    if not self.disable_color
                    else tree_node.add(icon)
                )
                self.dir_count += 1
                self.add_to_tree(item.path, branch, current_depth + 1)
            else:
                (
                    tree_node.add(icon, highlight=False, style="dim white")
                    if not self.disable_color
                    else tree_node.add(icon)
                )
                self.file_count += 1

    @property
    def totals(self) -> str:
        """Return a string with the total counts of directories and files."""
        return f"{self.dir_count} directories, {self.file_count} files"

    def run(self) -> RunResult:
        """Build the tree and return results for the :class:`OutputManager`."""
        self.add_to_tree(path=self.root, tree_node=self.tree)
        return RunResult(tree=self.tree, totals=self.totals, cli=self)


def main(arguments: list[str] | None = None) -> int:
    """Main function to run the RichTreeCLI."""
    try:
        args: Namespace = get_args(arguments)
        output_manager = OutputManager(disable_color=args.disable_color)
        if not args.directory.is_dir() or not args.directory.exists():
            output_manager.error(f"Error: {args.directory} is not a valid directory.")
            sys.exit(1)
        input_args: dict[str, Any] = vars(args)
        input_args.pop("gitignore", None)
        cli = RichTreeCLI(**input_args)
        result: RunResult = cli.run()
        output_manager.set_cli(cli)
        output_manager.output(result=result, output_formats=args.output_format, output_path=args.output)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

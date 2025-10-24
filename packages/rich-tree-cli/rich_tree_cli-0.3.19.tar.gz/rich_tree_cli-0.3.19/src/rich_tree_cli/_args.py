from argparse import ArgumentParser, Namespace
from pathlib import Path
import sys

from .constants import OutputFormat, __version__
from .export._common import DEFAULT_GITIGNORE_PATH


def get_args(args: list[str] | None = None) -> Namespace:
    """Parse command line arguments."""
    if args is None:
        args = sys.argv[1:]

    parser = ArgumentParser(description="Display a directory tree in a rich format.", prog="rTree")
    parser.add_argument("directory", nargs="?", default=".", help="Directory to display")

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output file path, the extension will be determined by the output format, default is None (console output only)",
    )

    parser.add_argument(
        "--max_depth",
        "--depth",
        "--level",
        "-d",
        "-l",
        type=int,
        default=0,
        help="Maximum depth of the tree (0 for no limit)",
    )

    parser.add_argument(
        "--sort_order",
        "-s",
        choices=["files", "dirs"],
        default="files",
        help="Order of items in the tree (default: files)",
    )

    parser.add_argument(
        "--metadata",
        "-m",
        choices=["none", "all", "size", "lines"],
        default="none",
        help="Metadata to display for files (default: none)",
    )

    parser.add_argument(
        "--disable_color",
        "-dc",
        action="store_true",
        help="Disable colored output",
    )

    parser.add_argument(
        "--gitignore_path",
        "-gi",
        default=None,
        help="Path to .gitignore file",
    )

    parser.add_argument(
        "-g",
        "--gitignore",
        action="store_true",
        help="Use .gitignore if one exists in the directory",
    )

    parser.add_argument(
        "--exclude",
        "-e",
        default=None,
        nargs="+",
        help="Exclude files or directories matching this pattern",
    )

    parser.add_argument(
        "--output_format",
        "-f",
        choices=OutputFormat.choices(),
        nargs="+",
        default=OutputFormat.default(),
        help=(f"Output format(s). Can specify multiple: --format {' '.join(OutputFormat.choices())} (default: text)"),
    )

    parser.add_argument(
        "--icons",
        "-i",
        type=str,
        default="emoji",
        choices=["plain", "emoji", "glyphs"],
        help=(
            "Format of console output. "
            "'plain' for no icons, "
            "'emoji' for emoji icons, "
            "'glyphs' for rich glyphs (default: emoji)"
        ),
    )

    parser.add_argument(
        "--no_console",
        "-no",
        action="store_true",
        help="Disable console output",
    )

    parser.add_argument(
        "--replace_path",
        "-r",
        type=str,
        default=None,
        help="File path of file to inject into the output tree. "
        "Typically with in markdown or html files. "
        "Content inside tags like '<!-- rTree -->{{ content replaced }}<!-- /rTree -->' "
        "will be replaced with the tree output.",
    )

    parser.add_argument(
        "--replace_tag",
        "-rt",
        type=str,
        default=None,
        help=(
            "Tag used for replacement. Provide a full tag pair like '<replace>'"
            " or '<!-- rTree -->'. Closing tag is inferred."
        ),
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"rTree v{__version__}",
        help="Show the version of rTree",
    )

    arguments: Namespace = parser.parse_args(args)
    arguments.directory = Path(arguments.directory).resolve()
    arguments.output = Path(arguments.output).resolve() if arguments.output else None
    arguments.gitignore_path = (
        Path(arguments.gitignore_path).resolve()
        if arguments.gitignore_path is not None
        else DEFAULT_GITIGNORE_PATH
        if arguments.gitignore
        else None
    )
    arguments.replace_path = Path(arguments.replace_path).resolve() if arguments.replace_path is not None else None
    return arguments

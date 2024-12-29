"""
This module contains utility functions.
"""

import pathlib


def get_assets_path() -> pathlib.Path:
    """
    Returns the path to the assets folder.
    """
    return pathlib.Path(__file__).parent.parent.parent / 'assets'


def directory_content(path: pathlib.Path) -> list[str]:
    """
    Hashes the contents of a directory.
    """
    contents = []
    for file in path.rglob('*'):
        if file.is_file():
            contents.append(file.read_text())
    return contents

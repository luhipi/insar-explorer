#!/usr/bin/env python3
"""
Create a clean ZIP archive for submission to the QGIS Plugin Repository.

The script:
- copies the plugin to a temporary directory,
- removes development-only files,
- creates dist/<plugin>-<version>.zip.
"""

from pathlib import Path
import shutil
import tempfile
import zipfile


EXCLUDE_NAMES = {
    ".git",
    ".github",
    ".pytest_cache",
    "__pycache__",
    ".readthedocs.yaml",
    ".gitignore",
    ".pre-commit-config.yaml",
}

EXCLUDE_SUFFIXES = {
    ".pyc",
    ".pyo",
}


def read_version(metadata_file: Path) -> str:
    """Read the plugin version from metadata.txt."""
    with metadata_file.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("version="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("No version found in metadata.txt")


def should_exclude(path: Path) -> bool:
    """Return True if the file or directory should be excluded."""
    if path.name in EXCLUDE_NAMES:
        return True

    if path.suffix in EXCLUDE_SUFFIXES:
        return True

    return False


def main():
    script_dir = Path(__file__).resolve().parent
    plugin_dir = script_dir.parent

    metadata = plugin_dir / "metadata.txt"
    version = read_version(metadata)

    plugin_name = "insar_explorer-dev"

    dist_dir = plugin_dir / "dist"
    dist_dir.mkdir(exist_ok=True)

    zip_path = dist_dir / f"{plugin_name}.zip"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_plugin = Path(tmp) / plugin_name

        shutil.copytree(
            plugin_dir,
            tmp_plugin,
            ignore=shutil.ignore_patterns(
                ".git",
                ".github",
                ".pytest_cache",
                "__pycache__",
                "*.pyc",
                "*.pyo",
                ".gitignore",
                ".idea"
                ".pre-commit-config.yaml",
                ".readthedocs.yaml",
                ".coverage"
                "dist",
                "scripts",
                "test",
                "icons"
                "help",
                "plugin_builder"
                ".DS_Store",
                "._*",
            ),
        )

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in tmp_plugin.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(tmp_plugin.parent))

    print(f"Created: {zip_path}")


if __name__ == "__main__":
    main()

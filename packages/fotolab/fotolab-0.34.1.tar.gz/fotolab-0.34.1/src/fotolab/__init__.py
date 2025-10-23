# Copyright (C) 2024,2025 Kian-Meng Ang
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""A console program that manipulate images."""

from importlib import metadata
from pathlib import Path
import argparse
import logging
import os
import subprocess
import sys

from PIL import Image

__version__ = metadata.version("fotolab")

log = logging.getLogger(__name__)


def save_gif_image(
    args: argparse.Namespace,
    image_filepath: Path,
    original_image: Image.Image,
    after_image: Image.Image,
    subcommand: str,
) -> None:
    """Save the original and after image."""
    gif_kwargs = {
        "format": "gif",
        "append_images": [after_image],
        "save_all": True,
        "duration": 2500,
        "loop": 0,
        "optimize": True,
    }
    save_image(args, original_image, image_filepath, subcommand, **gif_kwargs)


def save_image(
    args: argparse.Namespace,
    image: Image.Image,
    output_filepath: Path,
    subcommand: str,
    **kwargs,
) -> None:
    """Save image with additional options and handle opening.

    Args:
        args (argparse.Namespace): Config from command line arguments.
        image (Image.Image): The image to save.
        output_filepath (Path): The path to save the image to.
        subcommand (str): The name of the subcommand.
        **kwargs: Additional keyword arguments for Image.save().
    """
    new_filename = _get_output_filename(args, output_filepath, subcommand)
    log.info("%s image: %s", subcommand, new_filename.resolve())
    image.save(new_filename, **kwargs)

    if args.open:
        open_image(new_filename)


def _get_output_filename(
    args: argparse.Namespace, image_file: Path, subcommand: str
) -> Path:
    """Build and return output filename based on the command line options."""
    if args.overwrite:
        return image_file.with_name(image_file.name)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / image_file.with_name(f"{subcommand}_{image_file.name}")


def open_image(filename: Path):
    """Open generated image using default program."""
    try:
        if sys.platform == "linux":
            subprocess.call(["xdg-open", filename])
        elif sys.platform == "darwin":
            subprocess.call(["open", filename])
        elif sys.platform == "win32":
            os.startfile(filename)
        log.info("open image: %s", filename.resolve())

    except (OSError, FileNotFoundError) as error:
        log.error("Error opening image: %s -> %s", filename, error)

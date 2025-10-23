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

"""Contrast subcommand."""

import argparse
import logging
from pathlib import Path

from PIL import Image, ImageOps

from fotolab import save_image

log = logging.getLogger(__name__)


# pylint: disable=protected-access
def _validate_cutoff(value: str) -> float:
    """Validate the cutoff value."""
    try:
        f_value = float(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"invalid float value: '{value}'"
        ) from e
    if not 0 <= f_value <= 50:
        raise argparse.ArgumentTypeError(
            f"cutoff value {f_value} must be between 0 and 50"
        )
    return f_value


def build_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Build the subparser."""
    contrast_parser = subparsers.add_parser(
        "contrast", help="contrast an image."
    )

    contrast_parser.set_defaults(func=run)

    contrast_parser.add_argument(
        dest="image_paths",
        help="set the image filename",
        nargs="+",
        type=str,
        default=None,
        metavar="IMAGE_PATHS",
    )

    contrast_parser.add_argument(
        "-c",
        "--cutoff",
        dest="cutoff",
        type=_validate_cutoff,
        default=1.0,
        help=(
            "set the percentage (0-50) of lightest or darkest pixels"
            " to discard from histogram"
            " (default: '%(default)s')"
        ),
        metavar="CUTOFF",
    )

    contrast_parser.add_argument(
        "-op",
        "--open",
        default=False,
        action="store_true",
        dest="open",
        help="open the image using default program (default: '%(default)s')",
    )

    contrast_parser.add_argument(
        "-od",
        "--output-dir",
        dest="output_dir",
        default="output",
        help="set default output folder (default: '%(default)s')",
    )


def run(args: argparse.Namespace) -> None:
    """Run contrast subcommand.

    Args:
        args (argparse.Namespace): Config from command line arguments

    Returns:
        None
    """
    log.debug(args)

    for image_path_str in args.image_paths:
        original_image = Image.open(image_path_str)

        if original_image.mode == "RGBA":
            # Split the image into RGB and Alpha channels
            rgb_image = original_image.convert("RGB")
            alpha_channel = original_image.getchannel("A")

            # Apply autocontrast to the RGB part
            contrasted_rgb = ImageOps.autocontrast(
                rgb_image, cutoff=args.cutoff
            )

            # Merge the contrasted RGB part with the original Alpha channel
            contrasted_rgb.putalpha(alpha_channel)
            contrast_image = contrasted_rgb
        else:
            # For other modes (like RGB, L, etc.), apply autocontrast directly
            contrast_image = ImageOps.autocontrast(
                original_image, cutoff=args.cutoff
            )

        save_image(args, contrast_image, Path(image_path_str), "contrast")

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

"""Resize subcommand."""

import argparse
import logging
import math
import sys
from pathlib import Path

from PIL import Image, ImageColor

from fotolab import save_image

log = logging.getLogger(__name__)

DEFAULT_WIDTH = 600
DEFAULT_HEIGHT = 277


def build_subparser(subparsers) -> None:
    """Build the subparser."""
    resize_parser = subparsers.add_parser("resize", help="resize an image")

    resize_parser.set_defaults(func=run)

    resize_parser.add_argument(
        dest="image_paths",
        help="set the image filename",
        nargs="+",
        type=str,
        default=None,
        metavar="IMAGE_PATHS",
    )

    resize_parser.add_argument(
        "-c",
        "--canvas",
        default=False,
        action="store_true",
        dest="canvas",
        help="paste image onto a larger canvas",
    )

    resize_parser.add_argument(
        "-l",
        "--canvas-color",
        default="black",
        dest="canvas_color",
        help=(
            "the color of the extended larger canvas(default: '%(default)s')"
        ),
    )

    if "-c" in sys.argv or "--canvas" in sys.argv:
        resize_parser.add_argument(
            "-W",
            "--width",
            dest="width",
            help="set the width of the image (default: '%(default)s')",
            type=int,
            required=True,
            metavar="WIDTH",
        )

        resize_parser.add_argument(
            "-H",
            "--height",
            dest="height",
            help="set the height of the image (default: '%(default)s')",
            type=int,
            required=True,
            metavar="HEIGHT",
        )
    else:
        group = resize_parser.add_mutually_exclusive_group(required=False)

        group.add_argument(
            "-W",
            "--width",
            dest="width",
            help="set the width of the image (default: '%(default)s')",
            type=int,
            default=DEFAULT_WIDTH,
            metavar="WIDTH",
        )

        group.add_argument(
            "-H",
            "--height",
            dest="height",
            help="set the height of the image (default: '%(default)s')",
            type=int,
            default=DEFAULT_HEIGHT,
            metavar="HEIGHT",
        )

    resize_parser.add_argument(
        "-op",
        "--open",
        default=False,
        action="store_true",
        dest="open",
        help="open the image using default program (default: '%(default)s')",
    )

    resize_parser.add_argument(
        "-od",
        "--output-dir",
        dest="output_dir",
        default="output",
        help="set default output folder (default: '%(default)s')",
    )


def run(args: argparse.Namespace) -> None:
    """Run resize subcommand.

    Args:
        args (argparse.Namespace): Config from command line arguments

    Returns:
        None
    """
    log.debug(args)

    for image_filepath in [Path(f) for f in args.image_paths]:
        original_image = Image.open(image_filepath)
        if args.canvas:
            resized_image = _resize_image_onto_canvas(original_image, args)
        else:
            resized_image = _resize_image(original_image, args)
        save_image(args, resized_image, image_filepath, "resize")


def _resize_image_onto_canvas(original_image, args):
    resized_image = Image.new(
        "RGB",
        (args.width, args.height),
        (*ImageColor.getrgb(args.canvas_color), 128),
    )
    x_offset = (args.width - original_image.width) // 2
    y_offset = (args.height - original_image.height) // 2
    resized_image.paste(original_image, (x_offset, y_offset))
    return resized_image


def _resize_image(original_image, args):
    new_width, new_height = _calc_new_image_dimension(original_image, args)
    resized_image = original_image.copy()
    resized_image = resized_image.resize(
        (new_width, new_height), Image.Resampling.LANCZOS
    )
    return resized_image


def _calc_new_image_dimension(image, args) -> tuple:
    old_width, old_height = image.size
    log.debug("old image dimension: %d x %d", old_width, old_height)

    new_width = args.width
    new_height = args.height

    original_aspect_ratio = old_width / old_height

    if new_width != DEFAULT_WIDTH and new_height == DEFAULT_HEIGHT:
        # user provided width, calculate height to maintain aspect ratio
        new_height = math.ceil(new_width / original_aspect_ratio)
        log.debug("new height calculated based on width: %d", new_height)
    elif new_height != DEFAULT_HEIGHT and new_width == DEFAULT_WIDTH:
        # user provided height, calculate width to maintain aspect ratio
        new_width = math.ceil(new_height * original_aspect_ratio)
        log.debug("new width calculated based on height: %d", new_width)

    # if both are default, no calculation needed, use defaults
    # due to argparse's mutually exclusive group, it's not possible for both
    # new_width and new_height to be non-default when --canvas is False

    log.debug("new image dimension: %d x %d", new_width, new_height)
    return (new_width, new_height)

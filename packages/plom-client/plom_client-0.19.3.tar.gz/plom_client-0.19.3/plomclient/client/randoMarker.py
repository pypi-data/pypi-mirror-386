#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2020-2025 Andrew Rechnitzer
# Copyright (C) 2020-2023, 2025 Colin B. Macdonald
# Copyright (C) 2020 Victoria Schuster
# Copyright (C) 2021 Elizabeth Xiao
# Copyright (C) 2023 Julian Lapenna

"""Randomly scribble marks and annotations on papers for testing purposes.

This is a very very cut-down version of Annotator, and a command-line
tool used to automate some random marking of papers.
"""

__copyright__ = "Copyright (C) 2020-2025 Andrew Rechnitzer, Colin B. Macdonald, et al"
__credits__ = "The Plom Project Developers"
__license__ = "AGPL-3.0-or-later"

import argparse
import os
import sys

from stdiomask import getpass

from plomclient.common import Default_Port

from .random_marking_utils import (
    build_random_rubrics,
    do_rando_marking,
)

__all__ = [
    "do_rando_marking",
    "build_random_rubrics",
]


def get_parser():
    parser = argparse.ArgumentParser(
        description="Perform marking tasks randomly, generally for testing."
    )

    parser.add_argument(
        "-w",
        "--password",
        type=str,
        help="""
            by default, for the "scanner" user', also checks the
            environment variable PLOM_SCAN_PASSWORD.
        """,
    )
    parser.add_argument("-u", "--user", help='Override default of "scanner"')
    parser.add_argument(
        "-s",
        "--server",
        metavar="SERVER[:PORT]",
        action="store",
        help=f"""
            Which server to contact, port defaults to {Default_Port}.
            Also checks the environment variable PLOM_SERVER if omitted.
        """,
    )
    parser.add_argument(
        "--partial",
        metavar="PERCENTAGE",
        type=float,
        default=100.0,
        action="store",
        help="""
            What percentage of questions to mark?
            Default is 100; mark all of them.
            Technically, this is a i.i.d. probability of grading
            each task that the server has.
        """,
    )
    parser.add_argument(
        "-q",
        "--question",
        metavar="N",
        action="store",
        help="""
            Question number to mark.  If omitted, mark all of them.
        """,
    )
    # potentially confusing with --verbose and software --version :(
    parser.add_argument(
        "-v",
        "--version",
        action="store",
        help="""
            Which version to mark.  If omitted, mark all of them.
        """,
    )
    # whether to make own rubrics, or use ones in the system.
    parser.add_argument(
        "--download-rubrics",
        action="store_true",
        default=False,
        help="Download rubrics from the server rather than creating own.",
    )
    parser.add_argument(
        "--allow-half",
        action="store_true",
        default=False,
        help="Make use of half-mark rubrics if present",
    )
    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    args.server = args.server or os.environ.get("PLOM_SERVER")

    if not args.user:
        args.user = "scanner"

    if args.user == "scanner":
        args.password = args.password or os.environ.get("PLOM_SCAN_PASSWORD")

    if not args.password:
        args.password = getpass(f"Please enter the '{args.user}' password: ")

    sys.exit(
        do_rando_marking(
            args.server,
            args.user,
            args.password,
            partial=args.partial,
            question=args.question,
            version=args.version,
            download_rubrics=args.download_rubrics,
            allow_half=args.allow_half,
        )
    )

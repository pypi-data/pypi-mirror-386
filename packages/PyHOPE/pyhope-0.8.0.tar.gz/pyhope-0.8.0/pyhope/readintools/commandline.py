#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of PyHOPE
#
# Copyright (c) 2024 Numerics Research Group, University of Stuttgart, Prof. Andrea Beck
#
# PyHOPE is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# PyHOPE is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# PyHOPE. If not, see <http://www.gnu.org/licenses/>.

# ==================================================================================================================================
# Mesh generation library
# ==================================================================================================================================
# ----------------------------------------------------------------------------------------------------------------------------------
# Standard libraries
# ----------------------------------------------------------------------------------------------------------------------------------
import os
from argparse import Namespace
from typing import Optional, final
# ----------------------------------------------------------------------------------------------------------------------------------
# Third-party libraries
# ----------------------------------------------------------------------------------------------------------------------------------
import argparse
# ----------------------------------------------------------------------------------------------------------------------------------
# Local imports
# ----------------------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------------------
# Local definitions
# ----------------------------------------------------------------------------------------------------------------------------------
STD_LENGTH = 79  # Standard length for output to console
PAR_LENGTH = 32
DEF_LENGTH = 20
# ==================================================================================================================================


def info(string: str, newline: bool = False) -> None:
    if newline:
        print('\n!', string)
    else:
        print('!', string)


def separator(length: int = STD_LENGTH) -> str:
    return '!' + '-'*(length-1)


@final
class CommandLine:
    """ Parse command line arguments, both explicit [*.ini] and flags [--]
    """
    def __init__(self, argv, name: str, version: str, commit: Optional[str]) -> None:
        # Local imports ----------------------------------------
        import pyhope.config.config as config
        from pyhope.output.output import Colors
        # ------------------------------------------------------

        # Read the command line arguments and store everything
        self.argv    = argv
        self.name    = name
        self.version = version
        self.commit  = commit
        # self.help    = ''

        # Print the header
        self.help = (Colors.BANNERA + '!' + '='*(STD_LENGTH-1))
        self.helpjoin(f'! {name} version {version}' + (f' [commit {commit}]' if commit else ''))
        self.helpjoin(Colors.BANNERA + '!' + '='*(STD_LENGTH-1) + Colors.END)

        # Assemble the help output
        for key in config.prms:
            # Check if we encountered a section
            if config.prms[key]['type'] == 'section':
                self.helpjoin(separator())
                self.helpjoin('! {}'.format(key))
                self.helpjoin(separator())
                continue

            if config.prms[key]['default'] is not None:
                default = config.prms[key]['default']
            else:
                default = ''

            # Convert booleans to strings
            if isinstance(default, bool):
                default = 'T' if default else 'F'

            if config.prms[key]['help']:
                help    = config.prms[key]['help']
            else:
                help    = ''

            self.helpjoin(f'{key:<{PAR_LENGTH}} = {default:>{DEF_LENGTH}} ! {help}')

        return None

    def __enter__(self) -> tuple[Namespace, list]:
        # Setup an argument parser and add know arguments
        _ = parser = argparse.ArgumentParser(prog   = self.name,                              # noqa: E251
                                             epilog = self.help,                              # noqa: E251
                                             usage  ='PyHOPE [-h] [-V] ' +                    # noqa: E251
                                                     '[--verify[-install] [tutorials] | --verify-health] ' +
                                                     '[<parameter.ini / mesh.h5>]',
                                             formatter_class=argparse.RawDescriptionHelpFormatter)

        _ = parser.add_argument('-V', '--version',
                                action = 'store_true',                                        # noqa: E251
                                help   = 'display the version number and exit')               # noqa: E251

        verifyParser = parser.add_argument_group('Verification options')
        _ = verifyParser.add_argument('--verify',
                                      nargs   = '?',                                          # noqa: E251
                                      const   = True,                                         # noqa: E251
                                      metavar = 'tutorials',                                  # noqa: E251
                                      help    = 'verify the installation and exit')           # noqa: E251
        _ = verifyParser.add_argument('--verify-health',
                                      action  = 'store_true',                                 # noqa: E251
                                      help    = 'check health and (optional) dependencies')   # noqa: E251
        _ = verifyParser.add_argument('--verify-install',
                                      nargs   = '?',                                          # noqa: E251
                                      const   = True,                                         # noqa: E251
                                      metavar = 'tutorials',                                  # noqa: E251
                                      help    = 'verify the installation and exit')           # noqa: E251
        _ = verifyParser.add_argument('--skip-checks',
                                      action  = 'store_true',                                 # noqa: E251
                                      # Hidden: Disable checks for verification
                                      help    = argparse.SUPPRESS)                            # noqa: E251
        _ = parser.add_argument('input',
                                nargs   = '?',                                                # noqa: E251
                                metavar = '<parameter.ini / mesh.h5>',                        # noqa: E251
                                help    = 'PyHOPE parameter or mesh file')                    # noqa: E251

        # Parse known arguments and return other flags for further processing
        args, argv = parser.parse_known_args()
        return args, argv

    def __exit__(self, *args: object) -> None:
        return None

    def helpjoin(self, end) -> None:
        self.help = os.linesep.join([self.help, end])

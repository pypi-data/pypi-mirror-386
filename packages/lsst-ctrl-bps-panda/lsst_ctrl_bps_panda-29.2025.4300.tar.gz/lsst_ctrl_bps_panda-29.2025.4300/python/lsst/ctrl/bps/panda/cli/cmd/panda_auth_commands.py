# This file is part of ctrl_bps.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This software is dual licensed under the GNU General Public License and also
# under a 3-clause BSD license. Recipients may choose which of these licenses
# to use; please see the files gpl-3.0.txt and/or bsd_license.txt,
# respectively.  If you choose the GPL option then the following text applies
# (but note that there is still no warranty even if you opt for BSD instead):
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Subcommand definitions for the PanDA auth commands."""

__all__ = [
    "clean",
    "refresh",
    "reset",
    "status",
]


import click

from lsst.daf.butler.cli.utils import MWCommand

from ...panda_auth_drivers import (
    panda_auth_clean_driver,
    panda_auth_refresh_driver,
    panda_auth_reset_driver,
    panda_auth_status_driver,
)


class PandaAuthCommand(MWCommand):
    """Command subclass with panda-auth-command specific overrides."""

    extra_epilog = "See 'panda_auth --help' for more options."


@click.command(cls=PandaAuthCommand)
def status(*args, **kwargs):
    """Print informatino about auth token."""
    panda_auth_status_driver(*args, **kwargs)


@click.command(cls=PandaAuthCommand)
def reset(*args, **kwargs):
    """Get new auth token."""
    panda_auth_reset_driver(*args, **kwargs)


@click.command(cls=PandaAuthCommand)
def clean(*args, **kwargs):
    """Clean up token and token cache files."""
    panda_auth_clean_driver(*args, **kwargs)


@click.command(cls=PandaAuthCommand)
@click.option("--days", default=4, help="The earlist remaining days to refresh the token.")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def refresh(*args, **kwargs):
    """Refresh auth tocken."""
    days = kwargs.get("days", 4)
    verbose = kwargs.get("verbose", False)
    panda_auth_refresh_driver(days, verbose)

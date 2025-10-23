#!/usr/bin/env python3

# This file is a part of the LinkAhead project.
#
# Copyright (C) 2025 IndiScale GmbH <www.indiscale.com>
# Copyright (C) 2025 Daniel Hornung <d.hornung@indiscale.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""Remove null elements from list properties.
"""

import argparse
import logging

import linkahead as db
from linkahead.common.datatype import is_list_datatype

logger = logging.getLogger()


def strip(dry_run: bool = False, strip_empty_string: bool = False) -> None:
    """Implementation of null element removal.

    Parameters
    ----------
    dry_run : bool, default=False
      If True, only print indicative output, do not remove anything

    strip_empty_string : bool, default=False
      If True, also strip empty strings.

    Limitations
    -----------

    For efficiency reasons, this function only looks for properties which are LIST<> valued in their
    Property definition.  For example a ``my_prop: LIST<TEXT>`` is covered.  On the other hand, if
    ``other_prop: DOUBLE``, but a specific Entity uses ``other_prop`` as ``LIST<DOUBLE>``, this will
    not be found.
    """

    # Overview: For each list property, find all relevant records. Then clean this property on these
    # records.
    properties = db.execute_query("FIND PROPERTY")
    for prop in properties:
        if not is_list_datatype(prop.datatype):
            continue
        records = db.execute_query(f"FIND RECORD WITH {prop.name}")
        for record in records:
            for rec_prop in record.get_properties():
                to_update = False
                if not rec_prop.id == prop.id or not rec_prop.value:
                    continue
                if not isinstance(rec_prop.value, list):
                    raise ValueError(f"Expected list for property {prop.name}\n{record}")
                value = rec_prop.value
                copied = value.copy()
                while (popped := copied.pop()) is None or (strip_empty_string and popped == ""):
                    value.pop()
                    to_update = True
                rec_prop.value = value
                if to_update:
                    logger.info(f"Stripping {record.id}/{prop.name}")
        if not dry_run:
            records.update(unique=False)


def _parse_arguments():
    """Parse the arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", "--dry-run", help=(
        "Take no action, only list records / properties from which null elements would be "
        "removed."), action="store_true")
    parser.add_argument("--empty-string", help="Also strip empty strings", action="store_true")

    return parser.parse_args()


def main():
    """The main function of this script."""
    args = _parse_arguments()
    strip(dry_run=args.dry_run, strip_empty_string=args.empty_string)


if __name__ == "__main__":
    main()

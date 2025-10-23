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

"""Reset name / description overrides of properties.

The following entities have their property reset:

FIND <Role> [<Entity name>] WITH <property-name>

"""

import argparse

import linkahead as db
from linkahead import cached


def reset_overrides(role: str, ent_name: str, prop_name: str, dry_run: bool = False):
    """Reset name and description overrides for the given entities.

    Parameters
    ----------
    role : str
      The role to search for.

    ent_name : str
      The entity name to search for.

    prop_name : str
      The property name to search for.

    dry_run: bool, default=False
      If True, make no changes to the database.
    """
    query = f"FIND {role} {ent_name} WITH '{prop_name}'"
    ents = db.execute_query(query)
    if not ents:
        print(f"Could not find any entities for this query:\n{query}\n")
    assert isinstance(ents, db.Container)
    for ent in ents:
        prop = ent.get_property(prop_name)
        if prop is None:  # Look for original names.
            found = False
            props = ent.get_properties()
            assert isinstance(props, list)
            for prop in ent.get_properties():
                orig_prop = cached.cached_get_entity_by(eid=prop.id)
                assert isinstance(orig_prop, db.Entity)
                if orig_prop.name == prop_name:
                    found = True
                    break
            if not found:
                raise RuntimeError(
                    f"Could not find Property {prop_name} for entity {ent.id} ({ent.name})")

        prop.name = None
        prop.description = None
        if not dry_run:
            ent.update()
        else:
            orig_prop = cached.cached_get_entity_by(eid=prop.id)
            assert isinstance(orig_prop, db.Entity)
            print("Not updating this entity/property:\n"
                  f"{ent.id} ({ent.name}) > "
                  f"{prop.id} ({orig_prop.name})")


def reset_overrides_all(role: str, dry_run: bool = False):
    """Reset all name and description overrides, for the given role.

    Parameters
    ----------
    role : str
      The role to search for

    dry_run : bool, default=False
      If True, make no changes to the database.
    """
    query = f"FIND {role}"
    ents = db.execute_query(query)
    assert isinstance(ents, db.Container)
    for ent in ents:
        ent_str = f"{ent.id} ({ent.name})\n"
        prop_strings = []
        for prop in ent.get_properties():
            prop.name = None
            prop.description = None
            if dry_run:
                orig_prop = cached.cached_get_entity_by(eid=prop.id)
                assert isinstance(orig_prop, db.Entity)
                prop_strings.append(
                    f"  - {prop.id} ({orig_prop.name})"
                )
        if not dry_run:
            assert isinstance(ent, db.Entity)
            ent.update()
        else:
            ent_str += "\n".join(prop_strings)
            print(f"Not updating this entity:\n{ent_str}")


def _parse_arguments():
    """Parse the arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", choices=["RECORDTYPE", "RECORD", "ENTITY"], default="RECORDTYPE",
                        help="Which role to search for.  Default is RECORDTYPE.")
    parser.add_argument("--entity-name", default="",
                        help="The name of the entity which contains the property to reset."
                        )
    parser.add_argument("--property-name", default="", help=(
        "The name of the property to be reset.  Required if `--all` is not given.")
                        )
    parser.add_argument("--all", action="store_true",
                        help=("If given, reset overrides for all entities of the given role.  "
                              "Mutually exclusive with `--entity-name` and `--property-name`.")
                        )
    parser.add_argument("--dry-run", action="store_true",
                        help="Make no changes, only tell what would be done.")

    args = parser.parse_args()
    if args.all and (args.entity_name or args.property_name):
        raise argparse.ArgumentError(parser._option_string_actions["--all"],
                                     message=("The argument `--all` is mutually exclusive with "
                                              "`--entity-name` and `--property-name`."))
    if not args.all and not args.property_name:
        raise argparse.ArgumentError(parser._option_string_actions["--entity-name"],
                                     message=("The argument `--entity-name` is required."))
    return args


def main():
    """The main function of this script."""
    args = _parse_arguments()
    if args.all:
        reset_overrides_all(role=args.role, dry_run=args.dry_run)
    else:
        reset_overrides(role=args.role, ent_name=args.entity_name, prop_name=args.property_name,
                        dry_run=args.dry_run)


if __name__ == "__main__":
    main()

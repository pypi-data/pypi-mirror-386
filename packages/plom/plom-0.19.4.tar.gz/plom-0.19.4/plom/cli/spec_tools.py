# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2025 Colin B. Macdonald
# Copyright (C) 2025 Philip D. Loewen

from pathlib import Path

from plom.cli import with_messenger

from plom.plom_exceptions import (
    PlomAuthenticationException,
    PlomConflict,
    PlomNoPermission,
)


@with_messenger
def upload_spec(spec_toml: Path, *, force_public_code: bool = False, msgr) -> bool:
    """Upload a new spec from a local toml file.

    Args:
        spec_toml: Path to a .toml file containing a valid assessment spec.

    Keyword Args:
        force_public_code: Usually the spec must not include "publicCode"
            Pass True to cancel that rule.
        msgr: An active Messenger object.

    Returns:
        True if the server's specification was updated, otherwise False.
    """
    try:
        check = msgr.new_server_upload_spec(
            spec_toml, force_public_code=force_public_code
        )
    except (
        PlomAuthenticationException,
        PlomConflict,
        PlomNoPermission,
        ValueError,
    ) as e:
        print(f"Upload failed with exception: {e}")
        return False

    print(f"Success: Server spec now addresses {check['name']}, {check['longName']}.")
    return True

# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2021 Andrew Rechnitzer
# Copyright (C) 2021-2024 Colin B. Macdonald

from plom.solutions import with_manager_messenger


@with_manager_messenger
def getSolutionImage(question, version, *, msgr):
    """Get a solution image from the server.

    Args:
        question (int): which question.
        version (int): which version.

    Keyword Args:
        msgr (plom.Messenger/tuple): either a connected Messenger or a
            tuple appropriate for credientials.

    Returns:
        bytes: the bitmap of the solution or None if there was no
        solution.  If you wish to know what sort of image it is,
        see recent changes to `get_annotations_image` which could
        expose this.

    Raises:
        PlomNoSolutionException: the question/version asked for does
            not have a solution image on the server.  This is also
            returned if the values are out of range.
    """
    return msgr.getSolutionImage(question, version)

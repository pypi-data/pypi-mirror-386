# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2023-2024 Andrew Rechnitzer
# Copyright (C) 2025 Colin B. Macdonald

from django.contrib.auth.models import User, Group
from django.db import transaction

from plom_server.API.services import TokenService
from plom_server.Mark.services import MarkingTaskService
from plom_server.Identify.services import IdentifyTaskService


@transaction.atomic
def get_users_groups(username: str):
    try:
        user_obj = User.objects.get_by_natural_key(username)
    except User.DoesNotExist:
        raise ValueError(f"No such user {username}")
    return list(user_obj.groups.values_list("name", flat=True))


@transaction.atomic
def toggle_user_active(username: str) -> None:
    """Toggle whether as user is "active", and if now inactive, force logout.

    An inactive user can be thought of as a "soft delete" [1].
    Apparently it "doesn't necessarily control whether or not the user
    can login" [1].

    [1] https://docs.djangoproject.com/en/5.1/ref/contrib/auth/#django.contrib.auth.models.User.is_active
    """
    user = User.objects.get_by_natural_key(username)
    user.is_active = not user.is_active
    user.save()
    # if user is now inactive and a marker then make sure that they are logged
    # out of the API system by removing their API access token.
    if not user.is_active:
        marker_group_obj = Group.objects.get_by_natural_key("marker")
        if marker_group_obj in user.groups.all():
            MarkingTaskService.surrender_all_tasks(user)
            IdentifyTaskService.surrender_all_tasks(user)
            TokenService.drop_api_token(user)


@transaction.atomic
def set_all_users_in_group_active(group_name: str, active: bool):
    """Set the 'is_active' field of all users in the given group to the given boolean."""
    for user in Group.objects.get(name=group_name).user_set.all():
        # explicitly exclude managers here
        if user.groups.filter(name="manager"):
            continue
        user.is_active = active
        user.save()


def set_all_scanners_active(active: bool):
    """Set the 'is_active' field of all scanner-users to the given boolean."""
    set_all_users_in_group_active("scanner", active)


def set_all_markers_active(active: bool):
    """Set the 'is_active' field of all marker-users to the given boolean.

    If de-activating markers, then those users also have their
    marker-client access-token revoked (ie client is logged out) and
    any outstanding tasks revoked.
    """
    # if de-activating markers then we also need to surrender tasks and log them out
    # of the API, see Issue #3084.
    set_all_users_in_group_active("marker", active)
    # loop over all (now) deactivated markers, log them out and surrender their tasks
    if not active:
        for user in Group.objects.get(name="marker").user_set.all():
            MarkingTaskService.surrender_all_tasks(user)
            IdentifyTaskService.surrender_all_tasks(user)
            TokenService.drop_api_token(user)


@transaction.atomic
def add_user_to_group(username, groupname):
    try:
        user_obj = User.objects.get_by_natural_key(username)
    except User.DoesNotExist:
        raise ValueError(f"Cannot find user with name {username}.")
    try:
        group_obj = Group.objects.get_by_natural_key(groupname)
    except Group.DoesNotExist:
        raise ValueError(f"Cannot find group with name {groupname}.")

    user_obj.groups.add(group_obj)


@transaction.atomic
def remove_user_from_group(username, groupname):
    try:
        user_obj = User.objects.get_by_natural_key(username)
    except User.DoesNotExist:
        raise ValueError(f"Cannot find user with name {username}.")
    try:
        group_obj = Group.objects.get_by_natural_key(groupname)
    except Group.DoesNotExist:
        raise ValueError(f"Cannot find group with name {groupname}.")

    user_obj.groups.remove(group_obj)


@transaction.atomic
def toggle_user_membership_in_group(username, groupname):
    try:
        user_obj = User.objects.get_by_natural_key(username)
    except User.DoesNotExist:
        raise ValueError(f"Cannot find user with name {username}.")
    try:
        group_obj = Group.objects.get_by_natural_key(groupname)
    except Group.DoesNotExist:
        raise ValueError(f"Cannot find group with name {groupname}.")

    if group_obj in user_obj.groups.all():
        user_obj.groups.remove(group_obj)
    else:
        user_obj.groups.add(group_obj)


def is_user_in_group(username, groupname):
    try:
        user_obj = User.objects.get_by_natural_key(username)
    except User.DoesNotExist:
        raise ValueError(f"Cannot find user with name {username}.")
    try:
        group_obj = Group.objects.get_by_natural_key(groupname)
    except Group.DoesNotExist:
        raise ValueError(f"Cannot find group with name {groupname}.")

    return group_obj in user_obj.groups.all()


@transaction.atomic
def toggle_lead_marker_group_membership(username: str):
    if not is_user_in_group(username, "marker"):
        raise ValueError(f"User {username} not a marker.")

    toggle_user_membership_in_group(username, "lead_marker")

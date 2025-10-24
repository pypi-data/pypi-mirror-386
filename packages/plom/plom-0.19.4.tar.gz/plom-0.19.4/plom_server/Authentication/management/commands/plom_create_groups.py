# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2022 Brennen Chiu
# Copyright (C) 2022 Edith Coates
# Copyright (C) 2023 Andrew Rechnitzer
# Copyright (C) 2023-2024 Colin B. Macdonald

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User
from django.db import transaction


class Command(BaseCommand):
    """Create the user groups.

    This is the command for "python manage.py plom_create_groups".
    It creates "admin", "manager", "marker", and "scanner" groups, as
    well as "demo" and "lead_marker".

    Any existing superusers will be automatically added to the admin
    group (but you can add others later).
    """

    def handle(self, *args, **options):
        group_list = ["admin", "manager", "marker", "scanner", "demo", "lead_marker"]

        for group in group_list:
            _, created = Group.objects.get_or_create(name=group)
            if created:
                self.stdout.write(f'Group "{group}" has been added')
            else:
                self.stderr.write(f'Group "{group}" already exists')

        with transaction.atomic():
            admin_group = Group.objects.get(name="admin")
            # get all existing superusers and ensure they are in the admin group
            for user in User.objects.filter(is_superuser=True).select_for_update():
                if user.groups.filter(name="admin").exists():
                    self.stderr.write(
                        f"Superuser {user.username} is already in the 'admin' group."
                    )
                else:
                    user.groups.add(admin_group)
                    user.save()
                    self.stdout.write(
                        f"Added superuser {user.username} to the 'admin' group"
                    )

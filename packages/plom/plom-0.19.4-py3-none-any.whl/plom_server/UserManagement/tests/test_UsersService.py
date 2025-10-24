# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2025 Aidan Murphy

from django.contrib.auth.models import User
from django.test import TestCase, Client
from model_bakery import baker
from ..services.UsersService import delete_user


class UsersService_delete_user(TestCase):
    def setUp(self) -> None:
        # documented under #3817
        # Aidan thinks the CI runner acts as user with id 1 when making requests to the demo server,
        # the middleware tracking who is online will then cache user id 1 as being online.
        # This is a buffer user representing the CI runner (id=1) so it doesn't interfere with unit tests
        baker.make(
            User,
            username="CI_runner",
            email="self_user@example.com",
            password="password123",
        )

    def test_delete_unused_user(self) -> None:
        """Check users can be deleted as intended."""
        baker.make(
            User,
            username="dummyMarker1",
            email="dummyMarker1@example.com",
            password="password123",
        )
        delete_user("dummyMarker1")
        self.assertFalse(User.objects.filter(username="dummyMarker1").exists())

    def test_delete_admin_fails(self) -> None:
        """Check deleting admin (super) users fails."""
        baker.make(
            User,
            username="dummyAdmin1",
            email="dummyAdmin1@example.com",
            password="password123",
            is_superuser=True,
        )
        with self.assertRaisesRegex(ValueError, "admin"):
            delete_user("dummyAdmin1")

    def test_delete_self_user_fails(self) -> None:
        """Check a user can't delete themselves."""
        requesting_user = baker.make(
            User,
            username="dummyMarker1",
            email="dummyMarker1@example.com",
            password="password123",
        )  # type: User
        with self.assertRaisesRegex(ValueError, "themselves"):
            delete_user(requesting_user.username, requesting_user.id)

    def test_delete_user_post_login_fails(self) -> None:
        """Check users can't be deleted after they've logged in."""
        user_in_use = baker.make(
            User,
            username="dummyMarker1",
            email="dummyMarker1@example.com",
            password="password123",
        )  # type: User
        user_in_use.set_password("password123")  # baker doesn't hash the password
        user_in_use.save()

        auth_client = Client()
        auth_client.login(username=user_in_use.username, password="password123")
        user_in_use.refresh_from_db()

        self.assertIsNotNone(user_in_use.last_login)
        with self.assertRaisesRegex(ValueError, "login"):
            delete_user("dummyMarker1")

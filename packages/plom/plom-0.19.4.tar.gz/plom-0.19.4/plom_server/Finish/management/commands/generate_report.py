# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2023 Julian Lapenna
# Copyright (C) 2023 Colin B. Macdonald

from django.core.management.base import BaseCommand

from ...services import ReportPDFService


class Command(BaseCommand):
    """Generates a PDF report of the marking progress."""

    help = """Generates a PDF report of the marking progress.

    Report is saved as a pdf in the server `plom_server` directory.

    Requires matplotlib, pandas, seaborn, and weasyprint. If calling on demo
    data, run `python manage.py plom_demo --randomarker` first.
    """

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument(
            "--versions",
            action="store_true",
            default=True,
            help="Include details about versions in the report (default behaviour)",
        )
        group.add_argument(
            "--no-versions",
            action="store_false",
            dest="versions",
            help="Do not include details about versions.",
        )

    def handle(self, *args, **options):
        versions = options["versions"]

        d = ReportPDFService.pdf_builder(versions, verbose=True, _use_tqdm=True)

        print(f"Writing to {d['filename']}...")
        with open(d["filename"], "wb") as f:
            f.write(d["bytes"])
        print("Finished saving report.")

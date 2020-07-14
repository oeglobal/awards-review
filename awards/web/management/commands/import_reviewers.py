import xlrd

from django.core.management import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "imports reviewers"

    def add_arguments(self, parser):
        parser.add_argument(
            "filename", type=str, help="Filename of XLS",
        )

    def handle(self, *args, **options):
        wb = xlrd.open_workbook(options.get("filename"))
        sheet = wb.sheet_by_index(0)

        for row_idx in range(0, sheet.nrows):
            first_name = sheet.cell(row_idx, 0).value
            last_name = sheet.cell(row_idx, 1).value
            email = sheet.cell(row_idx, 2).value

            User.objects.get_or_create(
                username=first_name + last_name,
                first_name=first_name,
                last_name=last_name,
                email=email,
                is_active=True,
            )

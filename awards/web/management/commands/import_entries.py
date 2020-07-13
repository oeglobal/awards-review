import requests
from django.conf import settings
from django.core.management import BaseCommand

from web.models import Entry, Category


class Command(BaseCommand):
    help = "imports OE Awards entries from Gravity Forms"

    def handle(self, *args, **options):
        self._import_awards()

    @staticmethod
    def _import_awards():
        request = requests.get(
            settings.GFORMS_URL + "?paging[page_size]=300&_labels=1",
            auth=(settings.GFORM_KEY, settings.GFORM_SECRET),
        ).json()

        labels = request["_labels"]

        entries = []
        for raw_entry in request["entries"]:
            entry = {}

            for key, value in raw_entry.items():
                if not value:
                    continue

                try:
                    float(key)
                    if "." in key:
                        j, k = key.split(".")
                        label = labels[j][key]
                    else:
                        label = labels[key]

                    label = label.strip(":")

                    entry[label] = value

                    if "Subcategory" in label:
                        entry["Subcategory"] = value
                except ValueError:
                    if key == "id":
                        entry["entry_id"] = value

            entries.append(entry)

        Entry.objects.all().delete()
        for data in entries:
            category, is_created = Category.objects.get_or_create(
                name=data.get("Main Category")
            )

            Entry.objects.create(
                title=data.get("Title")
                or "{} {}".format(data.get("First"), data.get("Last")),
                entry_id=data["entry_id"],
                data=data,
                subcategory=data.get("Subcategory", ""),
                category=category,
            )

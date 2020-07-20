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
                        if j == "1":
                            label = "N_" + label
                        if j == "67" or j == "5":
                            label = "C_" + label
                    else:
                        label = labels[key]

                        if key in ["2", "65", "24"]:
                            label = "N_" + label

                        if key in ["6", "23", "64"]:
                            label = "C_" + label

                    label = label.strip(":")
                    print(label)
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
                id=data["entry_id"],
                title=data.get("Title")
                or "{} {}".format(data.get("C_First"), data.get("C_Last")),
                entry_id=data["entry_id"],
                data=data,
                subcategory=data.get("Subcategory", ""),
                category=category,
            )

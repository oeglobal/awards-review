import random
from math import ceil

from django.contrib.auth.models import User
from django.core.management import BaseCommand

from web.models import Entry, Rating


class Command(BaseCommand):
    help = "Creates blank ratings and assign them to reviewers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit", action="store_true", dest="commit", help="Commit the changes",
        )
        parser.add_argument(
            "--reviews",
            action="store",
            dest="reviews",
            help="Number of reviews per entry",
        )

    def handle(self, *args, **options):
        self._create_ratings(
            commit=options.get("commit"), reviews=int(options.get("reviews"))
        )

    def _create_ratings(self, commit=False, reviews=3):
        if not commit:
            self.stdout.write("===== DRY RUN =====")
        else:
            self.stdout.write("===== Commiting =====")

        users = User.objects.filter(is_staff=False, is_active=True)
        entries = Entry.objects.all()
        ballots_per_reviewer = entries.count() * reviews / users.count()

        self.stdout.write(
            "There are {} reviewers in the system and {} entries".format(
                users.count(), entries.count()
            )
        )
        self.stdout.write(
            "With {} reviews per entry this means ~{} entries for each reviewer.".format(
                reviews, ballots_per_reviewer
            )
        )

        ballots_per_reviewer = ceil(ballots_per_reviewer)
        users = [u for u in users]

        if commit:
            Rating.objects.all().delete()

            for entry in entries:
                assigned_ballots = 0
                assigned_users = []
                while assigned_ballots < reviews:
                    random_user = random.choice(users)
                    if random_user in assigned_users:
                        continue

                    rating = Rating.objects.create(
                        user=random_user, entry=entry, status="empty"
                    )
                    self.stdout.write("{}".format(rating))
                    assigned_ballots += 1
                    assigned_users.append(random_user)

                self.stdout.write(
                    "Entry #{} has {} reviews assigned".format(
                        entry.entry_id, entry.rating_set.count()
                    )
                )

                for user in assigned_users:
                    if user.rating_set.count() >= ballots_per_reviewer:
                        users.remove(user)
                        self.stdout.write(
                            "Removed {} from additional assignments as they already have {}".format(
                                user.username, ballots_per_reviewer
                            )
                        )

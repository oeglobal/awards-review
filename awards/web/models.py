import statistics
import uuid

from django.core.mail import send_mail
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse


class Category(models.Model):
    name = models.CharField(max_length=120)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Entry(models.Model):
    title = models.TextField()
    entry_id = models.IntegerField(null=True)

    category = models.ForeignKey(
        Category, blank=True, null=True, on_delete=models.CASCADE
    )
    subcategory = models.CharField(max_length=125, blank=True)

    material = models.TextField(blank=True, null=True)
    video = models.TextField(blank=True, null=True)
    slideshare = models.TextField(blank=True, null=True)

    data = JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "Entry"
        verbose_name_plural = "Entries"

    def __str__(self):
        return "#{} - {}".format(self.entry_id, self.title)

    def conflicts(self):
        return self.rating_set(manager="conflicts")

    def dones(self):
        return self.rating_set(manager="dones")

    def drafts(self):
        return self.rating_set(manager="drafts")

    def get_reviewers(self):
        reviewers = []
        for user in User.objects.filter(is_staff=False).order_by("first_name"):
            reviewers.append(
                {
                    "user": user,
                    "assigned": self.rating_set.filter(
                        user=user, status__in=["empty", "draft", "conflict"]
                    ).exists(),
                }
            )
        return reviewers

    def get_entry_link(self):
        return self.data.get("Link")

    def get_absolute_url(self):
        return reverse("entry-detail", kwargs={"pk": self.pk})


RATING_CHOICES = (
    ("empty", "Empty ballot"),
    ("draft", "Draft rating"),
    ("conflict", "Conflict of interest or can't understand the language"),
    ("done", "Completed rating"),
)


class DraftsRatingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status__in=["empty", "draft"])


class DonesRatingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status__in=["done"])


class ConflictsRatingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status__in=["conflict"])


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)

    access = models.IntegerField(
        null=True,
        verbose_name="Access",
        help_text="Resources are easily accessible and readily available to anyone.",
    )
    quality = models.IntegerField(
        null=True,
        verbose_name="Quality",
        help_text="Exemplary quality in the presentation of content (in breadth, depth, creativity)",
    )
    visual = models.IntegerField(
        null=True,
        verbose_name="Visual representation",
        help_text="Uses multiple means of visual representation through accessible embedded multimedia content.",
    )
    engagement = models.IntegerField(
        null=True,
        verbose_name="Engagement",
        help_text="Provides multiple means of engagement through social learning connections, networks and/or communities.",
    )
    inclusion = models.IntegerField(
        null=True,
        verbose_name="Inclusion",
        help_text="Promotes inclusiveness and diversity through the use of a variety of languages and cultural contexts.",
    )
    licensing = models.IntegerField(
        null=True,
        verbose_name="Licensing",
        help_text="Copyright and Fair Use guidelines are followed with proper use of citations. An open license is clearly stated.",
    )
    accessibility = models.IntegerField(
        null=True,
        verbose_name="Accessibility",
        help_text="The resource supports learners with diverse needs.",
    )
    currency = models.IntegerField(
        null=True,
        verbose_name="Currency",
        help_text="Information is current and up to date. Date of materials is clearly indicated.",
    )
    individual = models.IntegerField(null=True, verbose_name="Individual Rating")

    comment = models.TextField(blank=True, verbose_name="Comment (optional)")

    status = models.CharField(max_length=20, choices=RATING_CHOICES, default="empty")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    drafts = DraftsRatingManager()
    dones = DonesRatingManager()
    conflicts = ConflictsRatingManager()

    def __str__(self):
        return "Rating of #{} by {}".format(self.entry.entry_id, self.user.username)

    @property
    def average(self):
        scores = []
        for item in [
            self.access,
            self.quality,
            self.visual,
            self.engagement,
            self.inclusion,
            self.licensing,
            self.accessibility,
            self.currency,
        ]:
            if item:
                scores.append(item)

        if scores:
            return round(statistics.mean(scores), 2)


class LoginKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    key = models.CharField(max_length=32)

    used = models.BooleanField(default=False)
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} - {}".format(self.user, self.email)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = uuid.uuid4().hex

        super(LoginKey, self).save(*args, **kwargs)

    def send_email(self):
        body = render_to_string(
            "mail-login/mail_body.txt", {"url": self.get_absolute_url()}
        )
        send_mail(
            "OE Awards Review login information",
            body,
            "memberservices@oeglobal.org",
            [self.email],
        )

    def get_absolute_url(self):
        return reverse_lazy("login-key-check", kwargs={"key": self.key})

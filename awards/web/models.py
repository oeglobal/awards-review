import uuid

from django.core.mail import send_mail
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.urls import reverse_lazy


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


RATING_CHOICES = (
    ("draft", "Draft rating"),
    ("conflict", "Conflict of interest or can't understand the language"),
    ("done", "Completed rating"),
)


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)

    access = models.IntegerField(null=True, verbose_name="Access")
    quality = models.IntegerField(null=True, verbose_name="Quality")
    visual = models.IntegerField(null=True, verbose_name="Visual representation")
    engagement = models.IntegerField(null=True, verbose_name="Engagement")
    inclussion = models.IntegerField(null=True, verbose_name="Inclussion")
    licensing = models.IntegerField(null=True, verbose_name="Licensing")
    accessibility = models.IntegerField(null=True, verbose_name="Accessibility")
    currency = models.IntegerField(null=True, verbose_name="Currency")
    assessment = models.IntegerField(null=True, verbose_name="Assessment")

    status = models.CharField(max_length=20, choices=RATING_CHOICES, default="draft")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Rating of #{} by {}".format(self.entry.entry_id, self.user.username)


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

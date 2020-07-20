from django import forms
from django.contrib.auth.models import User
from django.forms import Textarea

from .models import Rating


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.TextInput(attrs={"class": "form-input w-3/4"})
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email", "").strip()

        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "E-mail you entered is not in our system. Please contact support.",
                code="invalid-email",
            )

        return cleaned_data


class RatingForm(forms.ModelForm):
    is_draft = forms.BooleanField(
        label="I'm not yet done with the review", required=False
    )
    is_conflict = forms.BooleanField(
        label="I can't review this submission due to conflict of interest or not understanding the language",
        required=False,
    )

    class Meta:
        model = Rating
        fields = [
            "access",
            "quality",
            "visual",
            "engagement",
            "inclusion",
            "licensing",
            "accessibility",
            "currency",
            "assessment",
            "comment",
        ]
        widgets = {
            "comment": Textarea(attrs={"cols": 80, "rows": 4}),
        }

    def __init__(self, data=None, instance=None, *args, **kwargs):
        super().__init__(data, *args, instance=instance, **kwargs)

        if instance and instance.status == "conflict":
            self.fields["is_conflict"].initial = True

        if instance and instance.status == "draft":
            self.fields["is_draft"].initial = True

        if data and (data.get("is_conflict") or data.get("is_draft")):
            for field in self.Meta.fields:
                self.fields[field].required = False

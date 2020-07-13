from django import forms
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={"class": "form-input"}))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email", "").strip()

        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "E-mail you entered is not in our system. Please contact support.",
                code="invalid-email",
            )

        return cleaned_data

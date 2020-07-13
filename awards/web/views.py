import datetime

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.generic import FormView, TemplateView

from .models import LoginKey
from .forms import LoginForm


class IndexView(FormView):
    template_name = "web/index.html"
    form_class = LoginForm

    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        user = User.objects.get(email__iexact=email)
        ctx = {"email": email}

        key = LoginKey(user=user, email=email)
        key.save()
        key.send_email()

        return render(self.request, "mail-login/mail_sent.html", ctx)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_staff:
            return redirect("/staff/")
        if request.user.is_authenticated:
            return redirect("/submissions/")

        return super().dispatch(request, *args, **kwargs)


class LoginKeyCheckView(TemplateView):
    template_name = "mail-login/login_failed.html"

    def dispatch(self, request, *args, **kwargs):
        key = kwargs.pop("key")
        today = datetime.datetime.today()
        if LoginKey.objects.filter(
            key=key, pub_date__gte=(today - datetime.timedelta(days=7))
        ).exists():
            login_key = LoginKey.objects.get(
                key=key, pub_date__gte=(today - datetime.timedelta(days=7))
            )

            login_key.user.backend = "django.contrib.auth.backends.ModelBackend"
            login(self.request, login_key.user)

            return redirect(request.GET.get("next", "/submissions/"))

        return super(LoginKeyCheckView, self).dispatch(request, *args, **kwargs)


class SubmissionsView(LoginRequiredMixin, TemplateView):
    template_name = "web/sumissions.html"
    pass

import datetime

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.generic import FormView, TemplateView, ListView, DetailView

from .utils import StaffuserRequiredMixin
from .models import LoginKey, Entry
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
    template_name = "web/submissions.html"


class StaffIndexView(StaffuserRequiredMixin, TemplateView):
    template_name = "web-staff/index.html"


class StaffSubmissionsView(StaffuserRequiredMixin, ListView):
    template_name = "web-staff/submissions.html"
    model = Entry

    def get_queryset(self):
        return self.model.objects.all().order_by("category")


class EntryDetailView(LoginRequiredMixin, DetailView):
    model = Entry

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        data = self.object.data

        materials = "\n".join(data.get("Additional Support Material (optional)", []))

        groups = [
            {
                "name": "Nominator's Information",
                "fields": {
                    "Name": "{} {}".format(data.get("N_First"), data.get("N_Last")),
                    "Email": data.get("N_Email"),
                    "Institution": data.get("N_Institution"),
                    "Twitter": data.get("N_Twitter"),
                },
            },
            {
                "name": "Nominee's Information",
                "fields": {
                    "Title": data.get("Title"),
                    "Link": data.get("Link"),
                    "License": data.get("License"),
                    "Description": data.get("Description"),
                    "Name": "{} {}".format(data.get("C_First"), data.get("C_Last")),
                    "Email": data.get("C_Email"),
                    "Institution": data.get("C_Institution"),
                    "Twitter": data.get("C_Twitter"),
                    "Location": "{}, {}".format(data.get("City"), data.get("Country")),
                },
            },
            {
                "name": "Supporting materials",
                "fields": {
                    "Proposed Citation": data.get("Proposed Citation"),
                    "Background": data.get("Background"),
                    "Youtube video": data.get(
                        "Link to Youtube video (optional, but encouraged)"
                    ),
                    "Letter of Support": data.get(
                        "Letter of Support (required if self-nominating)"
                    ),
                    "Additional Support Material": materials,
                    "Slideshare presentation": data.get(
                        "Link to Slideshare presentation (optional)"
                    ),
                },
            },
        ]

        context["groups"] = groups
        return context


class UserListView(StaffuserRequiredMixin, ListView):
    model = User
    template_name = "web-staff/user_list.html"

    def get_queryset(self):
        return self.model.objects.filter(is_active=True, is_superuser=False)

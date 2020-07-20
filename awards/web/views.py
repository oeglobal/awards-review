import datetime

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView, TemplateView, ListView, DetailView
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin

from .utils import StaffuserRequiredMixin
from .models import LoginKey, Entry, Rating
from .forms import LoginForm, RatingForm


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
            return redirect(reverse_lazy("staff-index"))
        if request.user.is_authenticated:
            return redirect(reverse_lazy("submissions"))

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

            return redirect(request.GET.get("next", reverse_lazy("submissions")))

        return super(LoginKeyCheckView, self).dispatch(request, *args, **kwargs)


class SubmissionsView(LoginRequiredMixin, TemplateView):
    template_name = "web/submissions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context.update(
            {
                "draft_entries": Rating.drafts.filter(user=user),
                "done_entries": Rating.dones.filter(user=user),
                "conflict_entries": Rating.conflicts.filter(user=user),
            }
        )

        return context


class StaffIndexView(StaffuserRequiredMixin, TemplateView):
    template_name = "web-staff/index.html"


class StaffSubmissionsView(StaffuserRequiredMixin, ListView):
    template_name = "web-staff/submissions.html"
    model = Entry

    def get_queryset(self):
        return self.model.objects.all().order_by("category")


class EntryView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        view = EntryDetailView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = EntryFormView.as_view()
        return view(request, *args, **kwargs)


class EntryDetailView(DetailView):
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

        try:
            rating_instance = Rating.objects.get(
                entry=self.object, user=self.request.user
            )
            context["form"] = RatingForm(instance=rating_instance)
        except Rating.DoesNotExist:
            pass

        return context


class EntryFormView(SingleObjectMixin, FormView):
    template_name = "web/entry_detail.html"
    form_class = RatingForm
    model = Entry
    object = None
    rating_instance = None

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        rating = form.save()

        if form.cleaned_data.get("is_conflict"):
            for field in [
                "access",
                "quality",
                "visual",
                "engagement",
                "inclusion",
                "licensing",
                "accessibility",
                "currency",
                "assessment",
            ]:
                setattr(rating, field, None)

            rating.status = "conflict"
        elif form.cleaned_data.get("is_draft"):
            rating.status = "draft"
        else:
            rating.status = "done"

        rating.save()

        return super().form_valid(form)

    def get_form(self, form_class=None):
        self.rating_instance = Rating.objects.get(
            entry=self.object, user=self.request.user
        )
        return self.form_class(instance=self.rating_instance, **self.get_form_kwargs())

    def get_success_url(self):
        if self.rating_instance.status == "draft":
            messages.add_message(
                self.request, messages.INFO, "Your draft review has been saved."
            )
            return reverse("entry-detail", kwargs={"pk": self.object.pk})

        messages.add_message(self.request, messages.INFO, "Your review has been saved.")
        return reverse_lazy("submissions")


class UserListView(StaffuserRequiredMixin, ListView):
    model = User
    template_name = "web-staff/user_list.html"

    def get_queryset(self):
        return self.model.objects.filter(is_active=True, is_superuser=False)

import datetime

import xlwt
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe
from django.views.generic import FormView, TemplateView, ListView, DetailView
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin

from .utils import StaffuserRequiredMixin
from .models import LoginKey, Entry, Rating
from .forms import LoginForm, RatingForm, IndividualRatingForm


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
                "draft_entries": Rating.drafts.filter(user=user).order_by(
                    "entry__category", "entry__subcategory"
                ),
                "done_entries": Rating.dones.filter(user=user).order_by(
                    "entry__category", "entry__subcategory"
                ),
                "conflict_entries": Rating.conflicts.filter(user=user).order_by(
                    "entry__category", "entry__subcategory"
                ),
            }
        )

        return context


class StaffIndexView(StaffuserRequiredMixin, TemplateView):
    template_name = "web-staff/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "drafts": Rating.drafts.count(),
                "dones": Rating.dones.count(),
                "conflicts": Rating.conflicts.count(),
            }
        )

        return context


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

        materials = []
        for material in data.get("Additional Support Material (optional)", []):
            if material:
                materials.append(
                    '<a href="{}" target="_blank">{}</a><br /><br />'.format(
                        material, material.split("/")[-1]
                    )
                )
        materials = mark_safe("\n".join(materials))

        letters = []
        for letter in data.get("Letter of Support (required if self-nominating)", []):
            if letter:
                letters.append(
                    '<a href="{}" target="_blank">{}</a><br /><br />'.format(
                        letter, letter.split("/")[-1]
                    )
                )
        letters = mark_safe("\n".join(letters))

        nominee_fields = {}
        if self.request.user.is_staff:
            nominee_fields = {
                "Name": "{} {}".format(data.get("C_First"), data.get("C_Last")),
                "Email": data.get("C_Email"),
                "Twitter": data.get("C_Twitter"),
            }

        groups = [
            {
                "name": "Nominee's Information",
                "fields": dict(
                    {
                        "Title": data.get("Title"),
                        "Link": data.get("Link"),
                        "License": data.get("License"),
                        "Description": data.get("Description")
                        or data.get("Description (optional)"),
                        "Institution": data.get("C_Institution"),
                        "Location": "{}, {}".format(
                            data.get("City"), data.get("Country")
                        ),
                    },
                    **nominee_fields
                ),
            },
        ]

        if (
            data.get("Proposed Citation")
            or data.get("Background")
            or data.get("Link to Youtube video (optional, but encouraged)")
            or letters
            or materials
            or data.get("Link to Slideshare presentation (optional)")
        ):
            groups.append(
                {
                    "name": "Supporting materials",
                    "fields": {
                        "Proposed Citation": data.get("Proposed Citation"),
                        "Background": data.get("Background"),
                        "Youtube video": data.get(
                            "Link to Youtube video (optional, but encouraged)"
                        ),
                        "Letter of Support": letters,
                        "Additional Support Material": materials,
                        "Slideshare presentation": data.get(
                            "Link to Slideshare presentation (optional)"
                        ),
                    },
                },
            )

        category = self.object.category
        if self.request.user.is_staff or category.name not in [
            "Open Assets Awards",
            "Open Practices Awards",
        ]:
            nominator_ppi = {}
            if self.request.user.is_staff:
                nominator_ppi = {
                    "Email": data.get("N_Email"),
                    "Twitter": data.get("N_Twitter"),
                }

            groups.append(
                {
                    "name": "Nominator's Information",
                    "fields": dict(
                        {
                            "Name": "{} {}".format(
                                data.get("N_First"), data.get("N_Last")
                            ),
                            "Institution": data.get("N_Institution"),
                        },
                        **nominator_ppi
                    ),
                },
            ),

        context["groups"] = groups

        try:
            rating_instance = Rating.objects.get(
                entry=self.object, user=self.request.user
            )
            if self.object.category.name == "Individual Awards":
                context["form"] = IndividualRatingForm(instance=rating_instance)
            else:
                context["form"] = RatingForm(instance=rating_instance)
        except Rating.DoesNotExist:
            pass

        return context


class EntryFormView(SingleObjectMixin, FormView):
    template_name = "web/entry_detail.html"
    model = Entry
    object = None
    rating_instance = None

    def get_form_class(self):
        if self.object.category.name == "Individual Awards":
            return IndividualRatingForm

        return RatingForm

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
        return self.get_form_class()(
            instance=self.rating_instance, **self.get_form_kwargs()
        )

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
        return self.model.objects.filter(is_active=True, is_superuser=False).order_by(
            "first_name", "last_name"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        data = []
        for user in self.get_queryset():
            data.append(
                {
                    "user": user,
                    "dones": user.rating_set(manager="dones").count(),
                    "conflicts": user.rating_set(manager="conflicts").count(),
                    "drafts": user.rating_set(manager="drafts").count(),
                }
            )

        context["data"] = data
        return context


class EntryAssignUser(StaffuserRequiredMixin, View):
    def post(self, request, pk, user_id, *args, **kwargs):
        user = User.objects.get(pk=user_id)
        entry = Entry.objects.get(pk=pk)

        # if user doesn't have a rating ballot yet, create it
        if not Rating.objects.filter(user=user, entry=entry).exists():
            Rating.objects.create(user=user, entry=entry)
        else:
            if Rating.conflicts.filter(user=user, entry=entry):
                Rating.conflicts.filter(user=user, entry=entry).delete()

            if Rating.drafts.filter(user=user, entry=entry):
                Rating.drafts.filter(user=user, entry=entry).delete()

        return HttpResponse("ok")


class AssignmentView(StaffuserRequiredMixin, ListView):
    model = Entry
    template_name = "web-staff/assignment.html"
    cat = None

    def get_queryset(self):
        self.cat = self.request.GET.get("cat")
        if self.cat:
            return self.model.objects.filter(category=self.cat).order_by(
                "category", "entry_id"
            )
        else:
            return self.model.objects.all().order_by("category", "entry_id")

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        context["categories"] = (
            self.model.objects.all().values("category__name", "category__id").distinct()
        )
        context["filtering"] = bool(self.cat)

        return context


class ExportReviews(StaffuserRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = "attachment; filename=reviews.xls"
        wb = xlwt.Workbook(encoding="utf-8")
        ws = wb.add_sheet("Individual Awards", cell_overwrite_ok=True)

        row_num = 0
        columns = [
            ("Subcategory", 120),
            ("ID #", 20),
            ("Name", 80),
            ("Reviewer", 70),
            ("Total", 20),
            ("Comment", 450),
        ]

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num][0], font_style)
            ws.col(col_num).width = columns[col_num][1] * 100

        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1

        underline = xlwt.XFStyle()
        underline.font.underline = True

        for obj in Rating.objects.filter(
            entry__category__name="Individual Awards", status="done",
        ).order_by("entry__subcategory", "entry__id"):
            row_num += 1

            row = [
                obj.entry.subcategory,
                obj.entry.pk,
                obj.entry.title,
                "{} {}".format(obj.user.first_name, obj.user.last_name),
                obj.individual,
                obj.comment,
            ]

            for col_num in range(len(row)):
                if isinstance(row[col_num], list):
                    ws.write(row_num, col_num, row[col_num][0], row[col_num][1])
                else:
                    ws.write(row_num, col_num, row[col_num], font_style)

            ws.write(
                row_num,
                2,
                xlwt.Formula(
                    'HYPERLINK("{}";"{}")'.format(
                        "https://review.awards.oeglobal.org/{}".format(
                            obj.entry.get_absolute_url()
                        ),
                        obj.entry.title,
                    )
                ),
                underline,
            )

        for category in [
            "Open Assets Awards",
            "Open Practices Awards",
            "Special Awards",
        ]:
            ws = wb.add_sheet(category, cell_overwrite_ok=True)

            row_num = 0
            columns = [
                ("Subcategory", 100),
                ("ID #", 20),
                ("Title", 140),
                ("Reviewer", 70),
                ("Access", 20),
                ("Quality", 20),
                ("Visual", 20),
                ("Engagement", 35),
                ("Inclusion", 30),
                ("Licensing", 30),
                ("Accessibility", 40),
                ("Currency", 30),
                ("Average Score", 60),
                ("Comment", 450),
            ]

            font_style = xlwt.XFStyle()
            font_style.font.bold = True

            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num][0], font_style)
                ws.col(col_num).width = columns[col_num][1] * 100

            font_style = xlwt.XFStyle()
            font_style.alignment.wrap = 1

            for obj in Rating.objects.filter(
                entry__category__name=category, status="done",
            ).order_by("entry__subcategory", "entry__id"):
                row_num += 1

                row = [
                    obj.entry.subcategory,
                    obj.entry.pk,
                    obj.entry.title,
                    "{} {}".format(obj.user.first_name, obj.user.last_name),
                    obj.access,
                    obj.quality,
                    obj.visual,
                    obj.engagement,
                    obj.inclusion,
                    obj.licensing,
                    obj.accessibility,
                    obj.currency,
                    obj.average,
                    obj.comment,
                ]

                for col_num in range(len(row)):
                    if isinstance(row[col_num], list):
                        ws.write(row_num, col_num, row[col_num][0], row[col_num][1])
                    else:
                        ws.write(row_num, col_num, row[col_num], font_style)

                ws.write(
                    row_num,
                    2,
                    xlwt.Formula(
                        'HYPERLINK("{}";"{}")'.format(
                            "https://review.awards.oeglobal.org/{}".format(
                                obj.entry.get_absolute_url()
                            ),
                            obj.entry.title,
                        )
                    ),
                    underline,
                )

        wb.save(response)
        return response

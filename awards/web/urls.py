from django.conf.urls import url
from django.views.generic import TemplateView
from django.urls import path
from .views import (
    LoginKeyCheckView,
    IndexView,
    SubmissionsView,
    StaffSubmissionsView,
    EntryDetailView,
    StaffIndexView,
    UserListView,
)


def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [
    path("login/<str:key>/", LoginKeyCheckView.as_view(), name="login-key-check"),
    path("submissions/", SubmissionsView.as_view(), name="submissions"),
    path("submissions/<int:pk>/", EntryDetailView.as_view(), name="entry-detail"),
    path("staff/", StaffIndexView.as_view(), name="staff-index"),
    path(
        "staff/submissions/", StaffSubmissionsView.as_view(), name="staff-submissions"
    ),
    path("staff/users/", UserListView.as_view(), name="staff-user-list"),
    path("", IndexView.as_view(), name="index"),
]

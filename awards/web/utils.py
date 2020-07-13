from django.contrib.auth.mixins import AccessMixin


class StaffuserRequiredMixin(AccessMixin):
    """
    Mixin allows you to require a user with `is_staff` set to True.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission(request)

        return super(StaffuserRequiredMixin, self).dispatch(request, *args, **kwargs)

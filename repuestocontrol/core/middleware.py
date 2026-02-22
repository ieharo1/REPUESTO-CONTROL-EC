from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse


class RoleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/") and not request.user.is_staff:
            return HttpResponseForbidden("Acceso denegado")

        if request.path.startswith("/dashboard/") and not request.user.is_authenticated:
            login_url = reverse("core:login")
            next_param = request.path
            return HttpResponseRedirect(f"{login_url}?next={next_param}")

        return self.get_response(request)

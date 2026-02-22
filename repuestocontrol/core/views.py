from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from .forms import LoginForm


def login_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("/dashboard/")

    if request.method == "POST":
        form = LoginForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.POST.get("next") or request.GET.get(
                    "next", "/dashboard/"
                )
                return HttpResponseRedirect(next_url)
            else:
                messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = LoginForm()
    return render(request, "core/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("core:login")


@login_required
def forbidden_view(request):
    return render(request, "core/forbidden.html", status=403)

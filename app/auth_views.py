from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.shortcuts import render, redirect
from django.views.generic import FormView

from app.auth_forms import CustomPasswordResetForm, CustomSetPasswordForm, CustomUserCreationForm
from .auth_forms import CustomAuthenticationForm


# Create your views here.
def index(request):
    context = {}
    # return render(request, 'app/index.html', context)

    return redirect('rack-list')


class RegisterFormView(FormView):
    form_class = CustomUserCreationForm
    template_name = "registration/register.html"
    success_url = '/index/'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Registration successful.", extra_tags='success')
        return redirect("index")


def register_request(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.", extra_tags='success')
            return redirect("index")
        messages.error(request, "Unsuccessful registration. Invalid information.", extra_tags='danger')
    form = CustomUserCreationForm()
    return render(request=request, template_name="registration/register.html", context={"register_form": form})


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = CustomAuthenticationForm
    success_url = 'index'

    def get_success_url(self):
        url = 'home/'  # --> /accounts/login/home/
        url = '/home/'  # --> /home/
        return '/home/'


class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    form_class = CustomPasswordResetForm


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    form_class = CustomSetPasswordForm


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "registration/password_reset_complete.html"


def logout_view(request):
    logout(request)
    return redirect('index')

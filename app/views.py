from django.contrib.auth import logout
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.shortcuts import render, redirect
from app.forms import CustomPasswordResetForm, CustomSetPasswordForm
from .forms import CustomAuthenticationForm


# Create your views here.
def index(request):
    context = {}
    return render(request, 'app/index.html', context)


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

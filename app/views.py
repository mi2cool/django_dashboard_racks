from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect

from .forms import LoginForm


# Create your views here.
def index(request):
    context = {}
    return render(request, 'app/index.html', context)


class Login(LoginView):
    template_name = 'registration/login.html'
    authentication_form = LoginForm
    success_url = 'index'

    def get_success_url(self):
        url = 'home/'  # --> /accounts/login/home/
        url = '/home/'  # --> /home/
        return '/home/'


def logout_view(request):
    logout(request)
    return redirect('index')

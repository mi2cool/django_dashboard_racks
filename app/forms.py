from django.contrib import messages
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, UsernameField, PasswordResetForm, SetPasswordForm
from django import forms
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

UserModel = get_user_model()


class CustomAuthenticationForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={"autofocus": True, 'class': 'form-control'}))
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", 'class': 'form-control'}),
    )


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email", 'class': 'form-control'}),
    )


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", 'class': 'form-control'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", 'class': 'form-control'}),
    )

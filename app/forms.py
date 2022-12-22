from django.contrib import messages
from django import forms
from django.forms import TextInput
from django.template import loader
from django.utils.translation import gettext_lazy as _

from dashboard_racks import settings
from .models import Rack


class CreateRackForm(forms.ModelForm):
    name = forms.CharField(
        label='Name',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Name'},

        ))

    class Meta:
        model = Rack
        fields = ['name', ]

class UpdateRackForm(CreateRackForm):
    pass
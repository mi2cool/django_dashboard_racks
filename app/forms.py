import os
import platform
from time import sleep

from django.contrib import messages
from django import forms
from django.core.mail import send_mail
from django.forms import TextInput
from django.template import loader
from django.utils.translation import gettext_lazy as _

from dashboard_racks import settings
from .models import Rack, SshConfig, ReportConfig
from .tasks import write_log_file
from .widgets import TimePickerInput

REPORT_STATUS = (('PASSED', 'Passed'), ('ERROR', 'Failed'), ('ALL', 'All'))


class ReportFilterForm(forms.Form):
    result = forms.ChoiceField(
        choices=REPORT_STATUS,
        widget=forms.Select(
            choices=REPORT_STATUS,
            attrs={'class': 'form-control'}
        )
    )


class CreateRackForm(forms.ModelForm):
    name = forms.CharField(
        label='Name',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Name'},

        ))

    class Meta:
        model = Rack
        fields = ['name']

    def __str__(self):
        return "CreateRackForm"


class UpdateRackForm(CreateRackForm):
    def __str__(self):
        return "UpdateRackForm"


class CreateSshConfigForm(forms.ModelForm):
    hostname = forms.CharField(
        label='Hostname',
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control'},
        ))

    username = forms.CharField(
        label="Username",
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control'},
        )
    )

    password = forms.CharField(
        label="Password",
        required=False,

        widget=forms.PasswordInput(
            attrs={'class': 'form-control', "autocomplete": "current-password"},
            render_value=True
        )
    )

    private_key = forms.FileField(
        label='Private Key',
        required=False,
        widget=forms.FileInput(
            attrs={'class': 'form-control'}
        )
    )

    port = forms.IntegerField(
        label='Port',
        widget=forms.NumberInput(
            attrs={'class': 'form-control'}
        )
    )

    class Meta:
        model = SshConfig
        fields = ['hostname', 'username', 'password', 'private_key', 'port']

    def __str__(self):
        return "CreateSshConfigForm"


class UpdateSshConfigForm(CreateSshConfigForm):
    def __str__(self):
        return "UpdateSshConfigForm"


class CreateReportConfigForm(forms.ModelForm):
    remote_report_path = forms.CharField(
        label='Remote Directory',
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control'},
        ))

    class Meta:
        model = ReportConfig
        fields = ['remote_report_path', ]

    def __str__(self):
        return "CreateReportConfigForm"


class UpdateReportConfigForm(CreateReportConfigForm):
    def __str__(self):
        return "UpdateReportConfigForm"

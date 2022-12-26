from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import FormView, DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from .forms import CreateRackForm, UpdateRackForm, UpdateSshConfigForm, UpdateReportConfigForm
from .models import Rack, SshConfig, ReportConfig
from .utils.paramiko_wrapper import SftpApi

from collections import namedtuple

sftp = None
sftp_api = None

# Create your views here.
def index(request):
    context = {}
    # return render(request, 'app/index.html', context)
    return redirect('rack-list')


class RackCreateView(CreateView):
    model = Rack
    form_class = CreateRackForm
    template_name = "app/rack_create_form.html"

    def form_valid(self, form):
        self.object = form.save()
        self.object.ssh_config = SshConfig.objects.create()
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class RackUpdateView(UpdateView):
    model = Rack
    form_class = UpdateRackForm
    ssh_config_form_class = UpdateSshConfigForm
    report_config_form_class = UpdateReportConfigForm
    template_name = "app/rack_update_form.html"

    def get_success_url(self):
        return reverse_lazy('rack-update', kwargs={'pk': self.kwargs.get('pk')})

    def get_context_data(self, **kwargs):
        context = super(RackUpdateView, self).get_context_data(**kwargs)
        rack = context['rack']
        if 'rack_config_form' not in context:
            context['rack_config_form'] = self.form_class(initial={'name': rack.name})

        if 'ssh_config_form' not in context:
            context['ssh_config_form'] = self.ssh_config_form_class(
                initial={
                    'hostname': rack.ssh_config.hostname,
                    'username': rack.ssh_config.username,
                    'password': rack.ssh_config.password,
                    'private_key': rack.ssh_config.private_key,
                    'port': rack.ssh_config.port,
                }
            )

        if 'report_config_form' not in context:

            if not rack.report_config:
                rack.report_config = ReportConfig.objects.create()
                rack.report_config.save()
                rack.save()

            context['report_config_form'] = self.report_config_form_class(
                initial={
                    'remote_report_path': rack.report_config.remote_report_path,
                    'report_archive_path': rack.report_config.report_archive_path,
                })

        return context

    def get_object(self, queryset=None):
        return get_object_or_404(Rack, pk=self.kwargs.get('pk'))

    def form_invalid(self, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))

    def post(self, request, *args, **kwargs):
        form_class = None
        # get the user instance
        self.object = self.get_object()

        # determine which form is being submitted
        # uses the name of the form's submit button
        if 'UpdateRackForm' in request.POST:

            # get the primary form
            form_class = self.get_form_class()
            form_name = 'form'
            form = self.get_form(form_class)

        elif 'UpdateSshConfigForm' in request.POST:

            # get the secondary form
            form_class = self.ssh_config_form_class
            form_name = 'ssh_config_form'
            form = self.get_form(form_class)
            form.instance = self.object.ssh_config

        elif 'UpdateReportConfigForm' in request.POST:

            # get the secondary form
            form_class = self.report_config_form_class
            form_name = 'report_config_form'
            form = self.get_form(form_class)
            form.instance = self.object.report_config

        # validate
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(**{form_name: form})


class RackDetailView(DetailView):
    model = Rack
    template_name = "app/rack_detail.html"

    def get(self, request, *args, **kwargs):
        return super(RackDetailView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        reports = []

        context = super(RackDetailView, self).get_context_data()

        global sftp_api, sftp
        if not sftp_api:
            sftp_api = SftpApi(
                remote_ip=self.object.ssh_config.hostname,
                username=self.object.ssh_config.username,
                password=self.object.ssh_config.password,
                private_key=self.object.ssh_config.private_key or '',
                port=self.object.ssh_config.port,
            )

        try:
            if not sftp_api.is_connected:
                sftp_api.connect()

            sftp = sftp_api.get_sftp()
            reports = sftp.listdir(self.object.report_config.remote_report_path)

            ReportCollection = []
            Report = namedtuple('report', ['name', 'tag'])
            _err_cnt = 0
            for r in reports:
                _tag = 'success'
                if 'error' in r.lower():
                    _tag = 'danger'
                    _err_cnt+=1
                ReportCollection.append(Report(r, _tag))

            context['remote_reports_failed'] = _err_cnt
            context['ReportCollection'] = ReportCollection

        except Exception as ex:
            messages.success(self.request, f"Failed to connect to {self.object.ssh_config.hostname}", extra_tags='danger')
            messages.success(self.request, f"Error message: {str(ex)}", extra_tags='danger')

        context['test'] = 'test'
        if reports:
            context['reports'] = reports
        return context


class RackListView(ListView):
    model = Rack
    template_name = "app/rack_list.html"


class RackDeleteView(DeleteView):
    model = Rack
    template_name = "app/rack_confirm_delete.html"
    success_url = reverse_lazy('rack-list')


# SSH CONFIG
class SshConfigCreateView(CreateView):
    model = SshConfig
    template_name = "app/sshconfig_create_form.html"


class SshConfigUpdateView(UpdateView):
    model = SshConfig
    template_name = "app/sshconfig_update_form.html"

    # def get_success_url(self):
    #     return reverse_lazy('rack-detail', kwargs={self.kwargs.get('rack')})


class SshConfigDetailView(DetailView):
    model = SshConfig
    template_name = "app/sshconfig_detail.html"


class SshConfigDeleteView(DeleteView):
    model = SshConfig
    template_name = 'app/sshconfig_confirm_delete.html'


class SshConfigListView(ListView):
    model = SshConfig
    template_name = "app/sshconfig_list.html"

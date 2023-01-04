import os

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import FormView, DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from dashboard_racks import settings
from .filters import ReportFilter
from .forms import CreateRackForm, UpdateRackForm, UpdateSshConfigForm, UpdateReportConfigForm, ReportFilterForm
from .models import Rack, SshConfig, ReportConfig, Report
from .utils.paramiko_wrapper import SftpApi, sftp_instances, get_sftp_instance_by_hostname

from collections import namedtuple


# Create your views here.
class FilteredListView(ListView):
    filterset_class = None

    def get_queryset(self):
        # Get the queryset however you usually would.  For example:
        queryset = super().get_queryset()
        # Then use the query parameters and the queryset to
        # instantiate a filterset and save it as an attribute
        # on the view instance for later.
        self.filterset = self.filterset_class(self.request.GET, queryset=queryset)
        # Return the filtered queryset
        return self.filterset.qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass the filterset to the template - it provides the form.
        context['filterset'] = self.filterset
        return context


def index(request):
    context = {}
    # return render(request, 'app/index.html', context)
    return redirect('rack-list')


def rack_archive_report_list_filtered(request, pk):
    form = None
    rack = get_object_or_404(Rack, pk=pk)
    report_config = rack.report_config
    filter_form = ReportFilterForm()
    Report = namedtuple('report', ['name', 'result', 'path'])
    report_list = [Report(x, 'FAILED' if 'error' in x.lower() else 'PASSED', report_config.report_archive_path + os.sep + rack.name + os.sep + x)
                   for x in os.listdir(report_config.report_archive_path + os.sep + rack.name) if x.endswith('.html')]

    context = {
        'rack': rack,
        'filter_form': filter_form,
        'report_list': report_list,
    }

    if request.method == 'GET' and request.GET:
        form = ReportFilterForm(request.GET)
        if form.is_valid():
            if result := form.data.get('result', None):
                r = ''
                if result.upper() == 'ERROR':
                    report_list = [r for r in context.get('report_list', None) if 'error' in r.name.lower()]
                elif result.upper() == 'PASSED':
                    report_list = [r for r in context.get('report_list', None) if 'error' not in r.name.lower()]

                context['report_list'] = report_list

    return render(request, 'app/rack_report_list_filtered.html', context)


class RackCreateView(CreateView):
    model = Rack
    form_class = CreateRackForm
    template_name = "app/rack_create_form.html"

    def form_valid(self, form):
        self.object = form.save()
        self.object.ssh_config = SshConfig.objects.create()
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('rack-update', kwargs={'pk': self.object.pk})


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
        ssh_config: SshConfig = self.object.ssh_config
        report_config: ReportConfig = self.object.report_config

        sftp_api = get_sftp_instance_by_hostname(
            hostname=ssh_config.hostname,
            username=ssh_config.username,
            password=ssh_config.password,
            private_key=ssh_config.private_key,
            port=ssh_config.port,
        )

        try:
            if not sftp_api.is_connected:
                sftp_api.connect()

            sftp = sftp_api.get_sftp()
            reports = [x for x in sftp.listdir(self.object.report_config.remote_report_path) if x.endswith('.html')]

            remote_report_collection = []
            Report = namedtuple('report', ['name', 'tag'])
            _err_cnt = 0
            for r in reports:
                _tag = 'success'
                if 'error' in r.lower():
                    _tag = 'danger'
                    _err_cnt += 1
                remote_report_collection.append(Report(r, _tag))

            context['remote_reports_failed'] = _err_cnt
            context['remote_reports_passed'] = len(remote_report_collection) - _err_cnt
            context['remote_report_collection'] = remote_report_collection

        except Exception as ex:
            messages.success(self.request, f"Failed to connect to {self.object.ssh_config.hostname}", extra_tags='danger')
            messages.success(self.request, f"Error message: {str(ex)}", extra_tags='danger')

        # try:
        #     self._extracted_from_get_context_data_42(report_config, context)
        # except Exception as ex:
        #     messages.success(self.request, f"Failed to load report archive of {self.object.name}", extra_tags='danger')
        #     messages.success(self.request, f"Error message: {str(ex)}", extra_tags='danger')

        context['test'] = 'test'
        if reports:
            context['reports'] = reports
        return context

    # TODO Rename this here and in `get_context_data`
    def _extracted_from_get_context_data_42(self, report_config, context):
        # get archive files
        archive_path = report_config.report_archive_path + os.sep + self.object.name
        archive_report_list = [x for x in self.object.archive.reports if x.name.endswith('.html')]
        archive_reports_failed = [x for x in archive_report_list if 'error' in x.name.lower()]
        archive_reports_passed = [x for x in archive_report_list if 'error' not in x.name.lower()]
        context['archive_report_list'] = archive_report_list
        context['archive_reports_failed'] = archive_reports_failed
        context['archive_reports_passed'] = archive_reports_passed


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


@method_decorator(xframe_options_exempt, name='dispatch')
class ReportDetailView(DetailView):
    model = Report
    template_name = "app/report_detail.html"

    def get_context_data(self, **kwargs):
        reports = []
        context = super(ReportDetailView, self).get_context_data()
        context['placeholder'] = 'placeholder'
        return context


class ReportFilteredListView(FilteredListView):
    model = Report
    filterset_class = ReportFilter
    template_name = "app/rack_report_list_filtered.html"
    paginate_by = 250


    def get_context_data(self, **kwargs):
        context = super(ReportFilteredListView, self).get_context_data(**kwargs)
        rack = get_object_or_404(Rack, pk=self.kwargs.get('rack_pk', None))
        context['rack'] = rack


        # for report in rack.archive.reports.all():
        #     report.verdict = 'FAILED' if 'error' in report.name.lower() else 'PASSED'
        #     report.save()

        return context


class ReportDeleteView(DeleteView):
    model = Report
    template_name = "app/report_confirm_delete.html"

    def form_valid(self, form):
        success_url = self.get_success_url()
        report: Report = self.object
        os.remove(os.path.abspath(os.path.join(os.path.join(settings.MEDIA_ROOT, report.file.name))))
        report.delete()
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse_lazy('rack-report-list-filtered', kwargs={'rack_pk': self.kwargs.get('rack_pk')})

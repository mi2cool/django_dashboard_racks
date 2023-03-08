import json
import os
from celery.result import AsyncResult
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import FormView, DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from dashboard_racks import settings
from .filters import ReportFilter
from .forms import CreateRackForm, UpdateRackForm, UpdateSshConfigForm, UpdateReportConfigForm, ReportFilterForm
from .models import Rack, SshConfig, ReportConfig, Report
from .utils.paramiko_wrapper import SftpApi, sftp_instances, get_sftp_instance_by_hostname
from .tasks import print_message, archive_reports
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
        self.filterset = self.filterset_class(self.request.GET, queryset=queryset, request=self.request)
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

    import logging
    log = logging.getLogger('mydjanog')
    log.debug("THis is index")

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
                    'name': f'rc_{rack.name}',
                    'hostname': rack.ssh_config.hostname,
                    'username': rack.ssh_config.username,
                    'password': rack.ssh_config.password,
                    'private_key': rack.ssh_config.private_key,
                    'port': rack.ssh_config.port,
                }
            )

        if 'report_config_form' not in context:

            if not rack.report_config:
                rack.report_config = ReportConfig.objects.create(name=f"rc_{rack.name}")
                rack.report_config.save()
                rack.save()

            if not rack.report_config.periodic_task:
                schedule, created = IntervalSchedule.objects.get_or_create(
                    every=30,
                    period=IntervalSchedule.MINUTES,
                )
                pt = PeriodicTask.objects.create(
                    interval=schedule,  # we created this above.
                    name=f'pt_{rack.name}',  # simply describes this periodic task.
                    task='archive_reports',  # name of task.
                    kwargs=json.dumps({
                        'rack_pk': rack.pk,
                    }),
                )
                rack.report_config.periodic_task = pt
                rack.report_config.save()
                rack.save()

            context['report_config_form'] = self.report_config_form_class(
                initial={
                    'remote_report_path': rack.report_config.remote_report_path,
                    # 'pull_reports_time': rack.report_config.pull_reports_time,
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


def init_rack_detail_view(request, context, rack):
    reports = []
    ssh_config: SshConfig = rack.ssh_config
    report_config: ReportConfig = rack.report_config

    sftp_api = get_sftp_instance_by_hostname(
        hostname=ssh_config.hostname,
        username=ssh_config.username,
        password=ssh_config.password,
        private_key=ssh_config.private_key.path if ssh_config.private_key else '',
        port=ssh_config.port,
    )

    try:
        if not sftp_api.is_connected:
            sftp_api.connect()

        sftp = sftp_api.get_sftp()
        reports = [x for x in sftp.listdir(rack.report_config.remote_report_path) if x.endswith('.html')]

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
        messages.success(request, f"Failed to connect to {rack.ssh_config.hostname}",
                         extra_tags='danger')
        messages.success(request, f"Error message: {str(ex)}", extra_tags='danger')

    if reports:
        context['reports'] = reports
    return context


def rack_detail(request, pk):
    rack = get_object_or_404(Rack, pk=pk)

    context = {
        'rack': rack,
        'spinner': True,
    }
    load_remote_reports = request.GET.get('load_remote_reports')

    if load_remote_reports:
        context = init_rack_detail_view(
            request=request,
            context=context,
            rack=rack
        )
        context['spinner'] = False

    if '_pull_reports' in request.GET:
        # result = archive_reports(self.object.pk)  # asymc with celery
        result = archive_reports.delay(rack.pk)  # asymc with celery
        context['task_id'] = result.task_id

    return render(request, "app/rack_detail.html", context)


class RackListView(ListView):
    model = Rack
    template_name = "app/rack_list.html"

    def get(self, request, *args, **kwargs):
        _get = super().get(request, *args, **kwargs)
        return _get


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
    paginate_by = 50

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


def rack_reports_delete_all(request, rack_pk):
    rack = get_object_or_404(Rack, pk=rack_pk)
    if request.POST:
        for r in rack.archive.reports.all():
            os.remove(r.file.path)
            r.delete()
            print(os.path.join(settings.MEDIA_ROOT, r.file.path))

        return redirect('rack-report-list-filtered', rack_pk=rack_pk)

    return render(request, 'app/reports_confim_delete_all.html', context={'rack': rack})

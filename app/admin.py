from django_celery_beat.models import PeriodicTasks, PeriodicTask
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Rack, SshConfig, ReportConfig, Report, ReportArchive
from django.contrib import admin


# Register your models here.


class RackResource(resources.ModelResource):
    class Meta:
        model = Rack


class RackAdmin(ImportExportModelAdmin):
    list_display = ('name', 'pk',)
    resource_class = RackResource


class ArchiveResource(resources.ModelResource):
    class Meta:
        model = ReportArchive


class ArchiveAdmin(ImportExportModelAdmin):
    resource_class = ArchiveResource


class SshConfigResource(resources.ModelResource):
    class Meta:
        model = SshConfig


class SshConfigAdmin(ImportExportModelAdmin):
    list_display = ('pk', 'rack_name', 'hostname', 'username', 'port',)
    resource_class = SshConfigResource

    @admin.display(ordering='rack_name')
    def rack_name(self, obj):
        return obj.rack.name


class ReportConfigResource(resources.ModelResource):
    class Meta:
        model = ReportConfig


class ReportConfigAdmin(ImportExportModelAdmin):
    list_display = ('name', 'pk', 'remote_report_path',)
    resource_class = ReportConfigResource



class ReportResource(resources.ModelResource):
    class Meta:
        model = Report


class ReportAdmin(ImportExportModelAdmin):
    list_display = ('pk', 'name', 'verdict', 'created', 'file',)
    resource_class = ReportResource

    @admin.display(ordering='rack_name')
    def rack_name(self, obj):
        return obj.rack.name


class PeriodicTasksResource(resources.ModelResource):
    class Meta:
        model = PeriodicTasks


admin.site.register(ReportArchive, ArchiveAdmin)
admin.site.register(Rack, RackAdmin)
admin.site.register(SshConfig, SshConfigAdmin)
admin.site.register(ReportConfig, ReportConfigAdmin)
admin.site.register(Report, ReportAdmin)

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Watchtdog, Rack, SshConfig, ReportConfig, Report, ReportArchive
from django.contrib import admin


# Register your models here.


class RackResource(resources.ModelResource):
    class Meta:
        model = Rack


class RackAdmin(ImportExportModelAdmin):
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
    resource_class = SshConfigResource


class ReportConfigResource(resources.ModelResource):
    class Meta:
        model = ReportConfig


class ReportConfigAdmin(ImportExportModelAdmin):
    resource_class = ReportConfigResource


class ReportResource(resources.ModelResource):
    class Meta:
        model = Report


class ReportAdmin(ImportExportModelAdmin):

    resource_class = ReportResource


class WatchtdogResource(resources.ModelResource):
    class Meta:
        model = Watchtdog


class WatchtdogAdmin(ImportExportModelAdmin):
    list_display = ('counter', 'name',)
    resource_class = WatchtdogResource


admin.site.register(ReportArchive, ArchiveAdmin)
admin.site.register(Rack, RackAdmin)
admin.site.register(SshConfig, SshConfigAdmin)
admin.site.register(ReportConfig, ReportConfigAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(Watchtdog, WatchtdogAdmin)

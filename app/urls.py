# -*- coding: utf-8 -*-
from django.urls import path, re_path
from . import auth_views, views, api

urlpatterns = [
    # path('', auth_views.index, name='index'),
    path('', views.index, name='index'),
    path('home/', auth_views.index, name='home'),

    # RACK
    path('rack/create', views.RackCreateView.as_view(), name='rack-create'),
    path('rack/<int:pk>/update', views.RackUpdateView.as_view(), name='rack-update'),
    path('rack/<int:pk>/detail', views.RackDetailView.as_view(), name='rack-detail'),
    path('rack/<int:pk>/delete', views.RackDeleteView.as_view(), name='rack-delete'),
    path('racks/', views.RackListView.as_view(), name='rack-list'),

    # SSH CONFIG
    path('rack/<int:rack_pk>/ssh-config/create', views.SshConfigCreateView.as_view(), name='rack-sshconfig-create'),
    path('rack/<int:rack_pk>/ssh-config/<int:pk>/update', views.SshConfigUpdateView.as_view(), name='rack-sshconfig-update'),
    path('rack/<int:rack_pk>/ssh-config/<int:pk>/detail', views.SshConfigDetailView.as_view(), name='rack-sshconfig-detail'),
    path('rack/<int:rack_pk>/ssh-config/<int:pk>/delete', views.SshConfigDeleteView.as_view(), name='rack-sshconfig-delete'),
    path('sshconfigs/', views.SshConfigListView.as_view(), name='sshconfig-list'),

    # SSH COMMANDS
    path('rack/<int:rack_pk>/sftp/move_all/', api.archive_reports, name='rack-download-report'),

    # REPORTS
    path('rack/<int:rack_pk>/report/<int:pk>/detail/', views.ReportDetailView.as_view(), name='rack-report-detail'),
    path('rack/<int:rack_pk>/report/<int:pk>/delete/', views.ReportDeleteView.as_view(), name='rack-report-delete'),
    path('rack/<int:rack_pk>/reports/delete/selected/', api.delete_selected_reports, name='rack-reports-delete-selected'),
    # path('racks/<int:pk>/reports/filtered', views.rack_archive_report_list_filtered, name='rack-report-list-filtered'),
    path('rack/<int:rack_pk>/reports/filtered', views.ReportFilteredListView.as_view(), name='rack-report-list-filtered'),
]

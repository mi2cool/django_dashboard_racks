# -*- coding: utf-8 -*-


import django_filters
from django.db.models import QuerySet
from django.forms import DateTimeInput
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters import FilterSet, filters, widgets
from django import forms
from django_filters import DateFilter, CharFilter, ChoiceFilter

from .models import Report, ReportArchive, Rack
from .widgets import XDSoftDateTimePickerInput


class ReportFilter(FilterSet):
    def __init__(self, data, request=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)

        self.request = request

    name = filters.CharFilter(
        label='Name',
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    verdict = filters.CharFilter(
        label='Verdict',
        lookup_expr='iexact',
        widget=forms.Select(
            attrs={'class': 'form-control'},
            choices=Report.VERDICT_CHOICES,
        ))

    created = filters.DateTimeFilter(
        label='Created From',
        # lookup_expr='gte',
        input_formats=['%d.%m.%Y %H:%M'],
        method='filter_created',
        widget=XDSoftDateTimePickerInput(
            attrs={'class': 'form-control'}
        ),
    )

    class Meta:
        model = Report
        fields = ['name', 'verdict', 'created']
        exclude = ['']
        ordering = 'created'

    @property
    def qs(self):
        _qs = super().qs
        rack = get_object_or_404(Rack, pk=self.request.resolver_match.kwargs.get('rack_pk', None))

        _qs = _qs.filter(archive_id=rack.archive.id)
        _qs = _qs.order_by('created').reverse()
        return _qs

    def filter_created(self, qs: QuerySet, name, value):
        qs_date_gt = qs.filter(created__date__gt=value)
        qs_date_exact = qs.filter(created__date__exact=value)
        qs_date_exact_time_gt = qs_date_exact.filter(created__time__gte=value)
        new_qs = qs_date_gt | qs_date_exact_time_gt
        return new_qs

    def __str__(self):
        self.name

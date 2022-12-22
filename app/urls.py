# -*- coding: utf-8 -*-
from django.urls import path, re_path
from . import auth_views, views

urlpatterns = [
    path('', auth_views.index, name='index'),
    path('', views.index, name='index'),
    path('home/', auth_views.index, name='home'),

    path('rack/create', views.RackCreateView.as_view(), name='rack-create'),
    path('rack/<int:pk>/detail', views.RackDetailView.as_view(), name='rack-detail'),
    path('rack/<int:pk>/update', views.RackUpdateView.as_view(), name='rack-update'),
    path('racks', views.RackListView.as_view(), name='rack-list'),
]

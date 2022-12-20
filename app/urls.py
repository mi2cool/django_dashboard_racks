# -*- coding: utf-8 -*-
from django.urls import path, re_path
from . import views


urlpatterns = [
	path('', views.index, name='index'),
	path('home/', views.index, name='home'),


	path('accounts/login/', views.Login.as_view(), name='login'),
	path('accounts/logout/', views.logout_view, name='logout'),
	]
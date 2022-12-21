# -*- coding: utf-8 -*-
from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.index, name='home'),

    # path('accounts/register/', views.register_request, name='user-register'),
    path('accounts/register/', views.RegisterFormView.as_view(), name='user-register'),
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/password_reset', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('accounts/password_reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # accounts/login/ [name='login']
    # accounts/logout/ [name='logout']
    # accounts/password_change/ [name='password_change']
    # accounts/password_change/done/ [name='password_change_done']
    # accounts/password_reset/ [name='password_reset']
    # accounts/password_reset/done/ [name='password_reset_done']
    # accounts/reset/<uidb64>/<token>/ [name='password_reset_confirm']
    # accounts/reset/done/ [name='password_reset_complete']
]

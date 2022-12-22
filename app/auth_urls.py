# -*- coding: utf-8 -*-
from django.urls import path
from . import auth_views

urlpatterns = [
    # path('accounts/register/', views.register_request, name='user-register'),
    path('register/', auth_views.RegisterFormView.as_view(), name='user-register'),
    path('login/', auth_views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('password_reset', auth_views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>', auth_views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

]


from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from members.paypal_webhooks import paypal_webhook
from django.shortcuts import redirect


def performance_redirect(request):
    return redirect('dashboard')

urlpatterns = [
    # Homepage
    path('', views.home, name='home'),

    # Membership Plans
    path('membership/', views.membership, name='membership'),
    
    #Paypal Webhook
    path('paypal/webhook/', paypal_webhook, name='paypal_webhook'),
    
    # Checkout and Payment
    path('checkout/', views.checkout, name='checkout'),
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),
    
    # Performance Page
    path('performance/', performance_redirect, name='performance'),

    # Contact Us
    path('contact/', views.contact, name='contact'),

    # Dashboard (Members Only)
    path('dashboard/', views.dashboard, name='dashboard'),

    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='members/login.html'), name='login'),
    path('register/', views.register, name='register'),

    # Password Reset
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='members/password_reset.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='members/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='members/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='members/password_reset_complete.html'), name='password_reset_complete'),
]

from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('requests/', views.manage_requests_view, name='manage_requests'),
    path('inventory/', views.manage_inventory_view, name='manage_inventory'),
    path('donors/', views.donor_list_admin_view, name='donors'),
    path('donations/', views.donation_records_view, name='donations'),
    path('camps/', views.manage_camps_view, name='manage_camps'),
    path('analytics/', views.analytics_view, name='analytics'),
]

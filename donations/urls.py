from django.urls import path

from . import views

app_name = 'donations'

urlpatterns = [
    path('request/', views.blood_request_view, name='blood_request'),
    path('requests/', views.request_list_view, name='request_list'),
    path('requests/<int:request_id>/', views.request_detail_view, name='request_detail'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('my-requests/', views.my_requests_view, name='my_requests'),
    path('donate/', views.donate_view, name='donate'),
    path('certificate/<int:donation_id>/', views.donation_certificate_view, name='certificate'),
    path('camps/', views.camps_view, name='camps'),
    path('camps/<int:camp_id>/register/', views.camp_register_view, name='camp_register'),
]

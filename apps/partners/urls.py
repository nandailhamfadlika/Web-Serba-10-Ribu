from django.urls import path
from . import views

app_name = 'partners'

urlpatterns = [
    path('absensi/', views.attendance_h1_view, name='attendance_h1'),
    path('api/absensi/toggle/', views.api_toggle_attendance, name='attendance_toggle_api'),
    path('api/quick-create/', views.api_create_partner_quick, name='quick_create_api'),
]

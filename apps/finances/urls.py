from django.urls import path
from . import views

app_name = 'finances'

urlpatterns = [
    path('matriks/', views.monthly_matrix_view, name='monthly_matrix'),
    path('kasir/', views.cashier_closure_view, name='cashier_closure'),
    path('komparasi/', views.branch_comparison_view, name='branch_comparison'),
    path('api/komparasi/', views.branch_comparison_api, name='branch_comparison_api'),
]

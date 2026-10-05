from django.urls import path
from . import views

app_name = 'branches'

urlpatterns = [
    path('', views.public_home_view, name='home'),
    path('api/branches/nearest/', views.nearest_branch_api, name='nearest_api'),
    path('api/branches/', views.branch_list_api, name='list_api'),
]

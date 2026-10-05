from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('intake/', views.pos_intake_view, name='pos_intake'),
    path('api/partner/<int:partner_id>/products/', views.api_partner_products, name='partner_products_api'),
]

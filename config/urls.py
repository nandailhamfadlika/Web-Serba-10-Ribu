"""
URL configuration for Serba 10 Ribu Group Web-GIS Application.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.views.generic import RedirectView

from apps.inventory import views as inventory_views
from apps.partners import views as partners_views
from apps.finances import views as finances_views

urlpatterns = [
    # 1. Primary Operational Workspace Routes under /admin/
    path('admin/pos/', include('apps.inventory.urls', namespace='inventory')),
    path('admin/mitra/', include('apps.partners.urls', namespace='partners')),
    path('admin/laporan/', include('apps.finances.urls', namespace='finances')),

    # 2. Django Admin Site
    path('admin/', admin.site.urls),

    # 3. Direct Redirects & API backward compatibility
    path('pos/intake/', RedirectView.as_view(url='/admin/pos/intake/', permanent=False)),
    path('mitra/absensi/', RedirectView.as_view(url='/admin/mitra/absensi/', permanent=False)),
    path('laporan/matriks/', RedirectView.as_view(url='/admin/laporan/matriks/', permanent=False)),
    path('laporan/kasir/', RedirectView.as_view(url='/admin/laporan/kasir/', permanent=False)),
    path('laporan/komparasi/', RedirectView.as_view(url='/admin/laporan/komparasi/', permanent=False)),

    path('pos/api/partner/<int:partner_id>/products/', inventory_views.api_partner_products),
    path('mitra/api/absensi/toggle/', partners_views.api_toggle_attendance),
    path('mitra/api/quick-create/', partners_views.api_create_partner_quick),
    path('laporan/api/komparasi/', finances_views.branch_comparison_api),

    # 4. Public Web-GIS Storefront
    path('', include('apps.branches.urls', namespace='branches')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

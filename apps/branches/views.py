from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Branch
from .serializers import BranchSerializer
from apps.inventory.models import DailyStock
from apps.partners.models import DailyAttendance
from apps.products.models import Product


def public_home_view(request):
    """
    Halaman Utama Publik Web-GIS Serba 10 Ribu Group.
    Menampilkan Store Locator, Branch Switcher (Ciomas & Dramaga),
    Live In-Store Inventory (Stok Pagi), dan Intip Menu Besok (H-1).
    """
    branches = Branch.objects.filter(is_active=True).order_by('name')
    selected_slug = request.GET.get('branch', 'ciomas')
    
    # Ambil cabang terpilih atau fallback ke cabang pertama
    selected_branch = branches.filter(slug=selected_slug).first()
    if not selected_branch and branches.exists():
        selected_branch = branches.first()

    today = date.today()
    tomorrow = today + timedelta(days=1)

    # 1. Live In-Store Inventory Hari Ini (Optimized with select_related to prevent N+1)
    live_stocks = (
        DailyStock.objects
        .filter(branch=selected_branch, date=today, stock_in__gt=0)
        .select_related('partner', 'product')
        .order_by('product__category', 'product__name')
    )

    # 2. Intip Menu Besok (H-1) dari absensi 'hadir'
    attendances_tomorrow = (
        DailyAttendance.objects
        .filter(branch=selected_branch, date=tomorrow, status='hadir')
        .select_related('partner')
        .order_by('estimated_arrival_time', 'partner__name')
    )

    # Dapatkan produk yang terafiliasi dengan mitra yang hadir besok
    partner_ids_tomorrow = [att.partner_id for att in attendances_tomorrow]
    tomorrow_products = (
        Product.objects
        .filter(branch=selected_branch, partner_id__in=partner_ids_tomorrow, is_active=True)
        .select_related('partner')
        .order_by('category', 'name')
    )

    # Data JSON cabang untuk di-inject ke script Leaflet di frontend
    branches_json = [
        {
            'id': b.id,
            'name': b.name,
            'slug': b.slug,
            'address': b.address,
            'lat': float(b.latitude),
            'lng': float(b.longitude),
            'gmaps_url': b.gmaps_url,
            'opening_hours': b.opening_hours,
            'logo_url': b.logo_url,
        }
        for b in branches
    ]

    context = {
        'branches': branches,
        'selected_branch': selected_branch,
        'live_stocks': live_stocks,
        'attendances_tomorrow': attendances_tomorrow,
        'tomorrow_products': tomorrow_products,
        'branches_json': branches_json,
        'today': today,
        'tomorrow': tomorrow,
    }
    return render(request, 'public/home.html', context)


@api_view(['GET'])
def nearest_branch_api(request):
    """
    API Kalkulasi Jarak Geolocation Pengguna ke Cabang Ciomas vs Dramaga.
    Menerima parameter query: ?lat=-6.59&lng=106.75
    Mengembalikan cabang terurut berdasarkan jarak terdekat (dalam km).
    """
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')

    if not lat or not lng:
        return JsonResponse(
            {'error': 'Parameter lat dan lng wajib disertakan.'},
            status=400
        )

    try:
        user_lat = float(lat)
        user_lng = float(lng)
    except ValueError:
        return JsonResponse(
            {'error': 'Format koordinat lat dan lng tidak valid.'},
            status=400
        )

    branches = Branch.objects.filter(is_active=True)
    branch_distances = []

    for b in branches:
        dist = b.distance_to(user_lat, user_lng)
        branch_distances.append({
            'id': b.id,
            'name': b.name,
            'slug': b.slug,
            'address': b.address,
            'latitude': float(b.latitude),
            'longitude': float(b.longitude),
            'gmaps_url': b.gmaps_url,
            'opening_hours': b.opening_hours,
            'distance_km': dist,
        })

    # Urutkan berdasarkan jarak terdekat (ascending)
    branch_distances.sort(key=lambda x: x['distance_km'])

    nearest = branch_distances[0] if branch_distances else None

    return Response({
        'status': 'success',
        'user_location': {'latitude': user_lat, 'longitude': user_lng},
        'nearest_branch': nearest,
        'branches': branch_distances,
    })


@api_view(['GET'])
def branch_list_api(request):
    """
    API Daftar Seluruh Cabang Fisik.
    """
    branches = Branch.objects.filter(is_active=True).order_by('name')
    serializer = BranchSerializer(branches, many=True)
    return Response(serializer.data)

import calendar
import csv
import json
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q
from apps.branches.models import Branch
from apps.partners.models import Partner, DailyAttendance
from apps.inventory.models import DailyStock
from .models import DailyCashflow


@staff_member_required(login_url='admin:login')
def monthly_matrix_view(request):
    """
    Laporan 1: Matriks Summary Bulanan Mitra UMKM.
    Mengadopsi format spreadsheet asli mitra:
    - Baris: Nama Mitra
    - Kolom: Hari ke 1 s.d. 31
    - Nilai: Pcs terjual (0 untuk hari libur / absen)
    - Kolom Rekap: Total Pcs, Total Bagi Hasil Mitra (Rp9.000/pcs), Margin Platform (Rp1.000/pcs).
    """
    branches = Branch.objects.filter(is_active=True).order_by('name')
    selected_slug = request.GET.get('branch', 'ciomas')
    selected_branch = branches.filter(slug=selected_slug).first()
    if not selected_branch and branches.exists():
        selected_branch = branches.first()

    today = date.today()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year = today.year
        month = today.month

    # Dapatkan jumlah hari dalam bulan terpilih (28 s.d. 31 hari)
    _, num_days = calendar.monthrange(year, month)
    days_range = list(range(1, num_days + 1))

    # Ambil semua data stok harian di bulan & cabang terpilih
    month_stocks = (
        DailyStock.objects
        .filter(branch=selected_branch, date__year=year, date__month=month)
        .select_related('partner')
    )

    # Petakan penjualan per partner dan per tanggal
    # matrix_data[partner_id][day] = pcs_terjual
    sales_map = {}
    for st in month_stocks:
        pid = st.partner_id
        day = st.date.day
        if pid not in sales_map:
            sales_map[pid] = {}
        sales_map[pid][day] = sales_map[pid].get(day, 0) + st.stock_sold

    # Ambil absensi libur untuk menandai 0
    libur_map = {}
    libur_qs = DailyAttendance.objects.filter(
        branch=selected_branch, date__year=year, date__month=month, status='libur'
    )
    for att in libur_qs:
        pid = att.partner_id
        day = att.date.day
        if pid not in libur_map:
            libur_map[pid] = set()
        libur_map[pid].add(day)

    # Susun baris per partner
    partners = Partner.objects.filter(is_active=True).order_by('name')
    rows = []
    grand_totals_by_day = {d: 0 for d in days_range}
    grand_total_pcs = 0

    for p in partners:
        p_sales = sales_map.get(p.id, {})
        p_libur = libur_map.get(p.id, set())

        day_values = []
        total_p_pcs = 0

        for d in days_range:
            sold = p_sales.get(d, 0)
            day_values.append(sold)
            total_p_pcs += sold
            grand_totals_by_day[d] += sold

        grand_total_pcs += total_p_pcs
        payout = total_p_pcs * 9000
        margin = total_p_pcs * 1000

        rows.append({
            'partner': p,
            'day_values': day_values,
            'total_pcs': total_p_pcs,
            'payout': payout,
            'margin': margin,
        })

    # Export to CSV jika diminta
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="Matriks_{selected_branch.slug}_{year}_{month:02d}.csv"'
        writer = csv.writer(response)
        
        # Header
        header = ['Nama Mitra', 'Rekening Bank', 'No Rekening'] + [f"Tgl {d}" for d in days_range] + ['Total Pcs', 'Bagi Hasil (Rp9k)', 'Margin (Rp1k)']
        writer.writerow(header)

        for r in rows:
            p = r['partner']
            writer.writerow([
                p.name, p.bank_name, p.bank_account_number,
                *r['day_values'],
                r['total_pcs'], r['payout'], r['margin']
            ])

        # Grand Total
        writer.writerow([
            'TOTAL KESELURUHAN', '', '',
            *[grand_totals_by_day[d] for d in days_range],
            grand_total_pcs, grand_total_pcs * 9000, grand_total_pcs * 1000
        ])
        return response

    # Prepare data for sales trend chart (ApexCharts)
    chart_categories = [f"Tgl {d}" for d in days_range]
    chart_series_pcs = [grand_totals_by_day[d] for d in days_range]
    chart_series_omzet = [grand_totals_by_day[d] * 10000 for d in days_range]

    best_day = None
    best_pcs = 0
    if grand_total_pcs > 0:
        best_day = max(days_range, key=lambda d: grand_totals_by_day[d])
        best_pcs = grand_totals_by_day[best_day]

    context = {
        'branches': branches,
        'selected_branch': selected_branch,
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'days_range': days_range,
        'rows': rows,
        'grand_totals_by_day': [grand_totals_by_day[d] for d in days_range],
        'grand_total_pcs': grand_total_pcs,
        'grand_payout': grand_total_pcs * 9000,
        'grand_margin': grand_total_pcs * 1000,
        'months_list': [(i, calendar.month_name[i]) for i in range(1, 13)],
        'years_list': [today.year - 1, today.year, today.year + 1],
        'chart_categories_json': json.dumps(chart_categories),
        'chart_series_pcs_json': json.dumps(chart_series_pcs),
        'chart_series_omzet_json': json.dumps(chart_series_omzet),
        'best_day': best_day,
        'best_pcs': best_pcs,
    }
    return render(request, 'reports/monthly_matrix.html', context)


@staff_member_required(login_url='admin:login')
def cashier_closure_view(request):
    """
    Laporan 2: Daily Cashier Closure (Resume Kas Kasir Harian).
    Rekonsiliasi uang fisik (uang besar, receh), penerimaan Gopay Merchant,
    potongan pengeluaran kasir (gaji, makan, operasional), serta selisih balance.
    """
    branches = Branch.objects.filter(is_active=True).order_by('name')
    selected_slug = request.GET.get('branch', 'ciomas')
    selected_branch = branches.filter(slug=selected_slug).first()
    if not selected_branch and branches.exists():
        selected_branch = branches.first()

    today = date.today()
    date_str = request.GET.get('date')
    if date_str:
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            target_date = today
    else:
        target_date = today

    # Ambil atau buat record cashflow untuk cabang dan tanggal ini
    cashflow, _ = DailyCashflow.objects.get_or_create(
        branch=selected_branch,
        date=target_date,
    )

    # Hitung total teoritis dari penjualan hari ini dengan optimasi ORM select_related
    today_stocks = (
        DailyStock.objects
        .filter(branch=selected_branch, date=target_date)
        .select_related('partner', 'product')
        .order_by('partner__name', 'product__name')
    )
    total_sold_pcs = sum(s.stock_sold for s in today_stocks)
    theoretical_revenue = total_sold_pcs * 10000

    if request.method == 'POST':
        try:
            # 1. Update Sisa Sore / Tutup Toko untuk seluruh konsinyasi hari ini
            for stock in today_stocks:
                sisa_key = f"stock_left_{stock.id}"
                if sisa_key in request.POST:
                    try:
                        sisa_val = int(request.POST.get(sisa_key) or 0)
                        stock.stock_left = max(0, min(stock.stock_in, sisa_val))
                        # Pastikan jika payment_status kosong/belum ada, default ke 'pending' (Belum Ditentukan)
                        if not stock.payment_status:
                            stock.payment_status = 'pending'
                        stock.save(update_fields=['stock_left', 'payment_status', 'updated_at'])
                    except (ValueError, TypeError):
                        pass

            # Re-fetch stocks to get updated sold count & calculations
            today_stocks = (
                DailyStock.objects
                .filter(branch=selected_branch, date=target_date)
                .select_related('partner', 'product')
                .order_by('partner__name', 'product__name')
            )
            total_sold_pcs = sum(s.stock_sold for s in today_stocks)
            theoretical_revenue = total_sold_pcs * 10000

            # 2. Rekonsiliasi Kasflow Fisik & QRIS
            cashflow.cash_uang_besar = int(request.POST.get('cash_uang_besar') or 0)
            cashflow.cash_uang_receh = int(request.POST.get('cash_uang_receh') or 0)
            cashflow.cash_setor = int(request.POST.get('cash_setor') or 0)
            cashflow.gopay_merchant = int(request.POST.get('gopay_merchant') or 0)
            cashflow.cash_terpakai_gaji = int(request.POST.get('cash_terpakai_gaji') or 0)
            cashflow.cash_terpakai_makan = int(request.POST.get('cash_terpakai_makan') or 0)
            cashflow.cash_terpakai_operasional = int(request.POST.get('cash_terpakai_operasional') or 0)
            cashflow.notes = request.POST.get('notes', '').strip()

            # Hitung selisih rekonsiliasi:
            # Penerimaan Kasir Riil (Uang Setor + Gopay + Pengeluaran Toko) - Omzet Penjualan Barang
            total_realized = (
                cashflow.cash_setor + 
                cashflow.gopay_merchant + 
                cashflow.total_operational_expenses
            )
            cashflow.selisih = total_realized - theoretical_revenue
            cashflow.save()

            messages.success(
                request,
                f"Tutup kasir & rekonsiliasi {selected_branch.name} tanggal {target_date.strftime('%d %B %Y')} berhasil disimpan! Sisa barang dan bukti transaksi langsung terdata otomatis."
            )
            return redirect(f"{request.path}?branch={selected_branch.slug}&date={target_date.isoformat()}")
        except ValueError:
            messages.error(request, "Format angka kas tidak valid.")

    total_partner_payout = sum(s.partner_payout for s in today_stocks)
    total_platform_margin = sum(s.platform_margin for s in today_stocks)
    total_stock_in = sum(s.stock_in for s in today_stocks)
    total_stock_left = sum(s.stock_left for s in today_stocks)

    context = {
        'branches': branches,
        'selected_branch': selected_branch,
        'target_date': target_date,
        'today': today,
        'cashflow': cashflow,
        'today_stocks': today_stocks,
        'total_sold_pcs': total_sold_pcs,
        'total_stock_in': total_stock_in,
        'total_stock_left': total_stock_left,
        'theoretical_revenue': theoretical_revenue,
        'total_partner_payout': total_partner_payout,
        'total_platform_margin': total_platform_margin,
    }
    return render(request, 'reports/cashier_closure.html', context)


@staff_member_required(login_url='admin:login')
def branch_comparison_view(request):
    """
    Laporan 3: Head-to-Head Branch Comparison (Ciomas vs Dramaga).
    Filter rentang waktu: 1W (1 Minggu), 2W (2 Minggu), 3W (3 Minggu), 1M (1 Bulan), 1Y (1 Tahun).
    Menampilkan grafik interaktif perbandingan Omzet, Volume Penjualan, dan Mitra Aktif.
    """
    return render(request, 'reports/branch_comparison.html')


def branch_comparison_api(request):
    """
    Endpoint JSON untuk data grafik komparasi Ciomas vs Dramaga.
    Menerima query parameter: ?range=1W|2W|3W|1M|1Y
    """
    range_param = request.GET.get('range', '1W').upper()
    today = date.today()

    if range_param == '1W':
        days = 7
    elif range_param == '2W':
        days = 14
    elif range_param == '3W':
        days = 21
    elif range_param == '1M':
        days = 30
    elif range_param == '1Y':
        days = 365
    else:
        days = 7

    start_date = today - timedelta(days=days - 1)

    # Generate dates list
    date_list = [start_date + timedelta(days=i) for i in range(days)]
    date_labels = [d.strftime('%d/%m') for d in date_list]

    branches = Branch.objects.filter(slug__in=['ciomas', 'dramaga']).order_by('slug')
    ciomas = branches.filter(slug='ciomas').first()
    dramaga = branches.filter(slug='dramaga').first()

    # Query stocks in range
    stocks_in_range = (
        DailyStock.objects
        .filter(date__gte=start_date, date__lte=today)
        .values('date', 'branch__slug')
        .annotate(
            total_sold=Sum('stock_in') - Sum('stock_left'), # simplified estimate
            total_in=Sum('stock_in'),
            active_partners=Count('partner', distinct=True)
        )
    )

    # Initialize daily time series
    ciomas_omzet = {d: 0 for d in date_list}
    dramaga_omzet = {d: 0 for d in date_list}
    ciomas_pcs = {d: 0 for d in date_list}
    dramaga_pcs = {d: 0 for d in date_list}

    # Query precise stock sold
    for st in DailyStock.objects.filter(date__gte=start_date, date__lte=today):
        d = st.date
        sold = st.stock_sold
        omzet = sold * 10000
        if st.branch_id == getattr(ciomas, 'id', None):
            ciomas_pcs[d] = ciomas_pcs.get(d, 0) + sold
            ciomas_omzet[d] = ciomas_omzet.get(d, 0) + omzet
        elif st.branch_id == getattr(dramaga, 'id', None):
            dramaga_pcs[d] = dramaga_pcs.get(d, 0) + sold
            dramaga_omzet[d] = dramaga_omzet.get(d, 0) + omzet

    # Format series data
    series_omzet = [
        {
            'name': 'Ciomas (Rp)',
            'data': [ciomas_omzet[d] for d in date_list]
        },
        {
            'name': 'Dramaga (Rp)',
            'data': [dramaga_omzet[d] for d in date_list]
        }
    ]

    series_pcs = [
        {
            'name': 'Ciomas (Pcs)',
            'data': [ciomas_pcs[d] for d in date_list]
        },
        {
            'name': 'Dramaga (Pcs)',
            'data': [dramaga_pcs[d] for d in date_list]
        }
    ]

    total_ciomas_omzet = sum(ciomas_omzet.values())
    total_dramaga_omzet = sum(dramaga_omzet.values())
    total_ciomas_pcs = sum(ciomas_pcs.values())
    total_dramaga_pcs = sum(dramaga_pcs.values())

    return JsonResponse({
        'status': 'success',
        'range': range_param,
        'date_labels': date_labels,
        'series_omzet': series_omzet,
        'series_pcs': series_pcs,
        'summary': {
            'ciomas': {
                'total_omzet': total_ciomas_omzet,
                'total_pcs': total_ciomas_pcs,
            },
            'dramaga': {
                'total_omzet': total_dramaga_omzet,
                'total_pcs': total_dramaga_pcs,
            },
            'winner': 'Ciomas' if total_ciomas_omzet >= total_dramaga_omzet else 'Dramaga'
        }
    })

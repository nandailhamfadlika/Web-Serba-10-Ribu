from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Sum, Count
from .models import DailyStock
from .forms import DailyStockIntakeForm
from apps.branches.models import Branch
from apps.partners.models import Partner
from apps.partners.forms import QuickPartnerForm
from apps.products.models import Product


@staff_member_required(login_url='admin:login')
def pos_intake_view(request):
    """
    Halaman Utama Fast In-Take POS Kasir Pagi (Subuh - 08:00 WIB).
    Mendukung input serah terima, upload bukti kamera foto fisik,
    dan modal tambah mitra baru on-the-fly.
    """
    branches = Branch.objects.filter(is_active=True).order_by('name')
    selected_slug = request.GET.get('branch', 'ciomas')
    selected_branch = branches.filter(slug=selected_slug).first()
    if not selected_branch and branches.exists():
        selected_branch = branches.first()

    today = date.today()

    if request.method == 'POST':
        form = DailyStockIntakeForm(request.POST, request.FILES, branch=selected_branch)
        if form.is_valid():
            partner = form.cleaned_data['partner']
            product = form.cleaned_data['product']
            stock_in = form.cleaned_data['stock_in']
            proof_photo = form.cleaned_data.get('proof_photo')
            new_prod_name = form.cleaned_data.get('new_product_name')
            new_prod_cat = form.cleaned_data.get('new_product_category')

            # Jika kasir menginput menu baru on-the-fly
            if not product and new_prod_name:
                product, _ = Product.objects.get_or_create(
                    name=new_prod_name.strip(),
                    partner=partner,
                    branch=selected_branch,
                    defaults={
                        'category': new_prod_cat or 'snack',
                        'price_customer': 10000,
                        'price_partner': 9000,
                        'is_active': True,
                    }
                )
            elif not product:
                messages.error(request, "Harap pilih menu yang ada atau isi nama menu baru.")
                return redirect(f"{request.path}?branch={selected_branch.slug}")

            # Update or create DailyStock record untuk hari ini
            daily_stock, created = DailyStock.objects.get_or_create(
                date=today,
                branch=selected_branch,
                partner=partner,
                product=product,
                defaults={
                    'stock_in': stock_in,
                    'stock_left': stock_in, # Di awal pagi, sisa = barang masuk
                    'proof_photo': proof_photo,
                }
            )

            if not created:
                # Jika sudah ada input sebelumnya hari ini, tambahkan kuantitas masuk
                daily_stock.stock_in += stock_in
                daily_stock.stock_left += stock_in
                if proof_photo:
                    daily_stock.proof_photo = proof_photo
                daily_stock.save()
                messages.success(
                    request,
                    f"Berhasil menambahkan {stock_in} pcs ke menu [{product.name}] ({partner.name}). Total masuk: {daily_stock.stock_in} pcs."
                )
            else:
                messages.success(
                    request,
                    f"In-Take sukses! {stock_in} pcs [{product.name}] ({partner.name}) berhasil dicatat."
                )

            return redirect(f"{request.path}?branch={selected_branch.slug}")
        else:
            messages.error(request, "Terjadi kesalahan pada data form in-take. Silakan periksa kembali.")
    else:
        form = DailyStockIntakeForm(branch=selected_branch)

    # Form modal tambah mitra baru
    quick_partner_form = QuickPartnerForm()

    # Rekap In-Take Hari Ini di Cabang Terpilih
    today_intakes = (
        DailyStock.objects
        .filter(branch=selected_branch, date=today)
        .select_related('partner', 'product')
        .order_by('-updated_at')
    )

    # Agregasi ringkasan pagi
    summary_stats = today_intakes.aggregate(
        total_porsi=Sum('stock_in'),
        total_mitra=Count('partner', distinct=True)
    )
    total_porsi = summary_stats['total_porsi'] or 0
    total_mitra = summary_stats['total_mitra'] or 0
    total_nominal_rp = total_porsi * 10000

    context = {
        'branches': branches,
        'selected_branch': selected_branch,
        'form': form,
        'quick_partner_form': quick_partner_form,
        'today_intakes': today_intakes,
        'total_porsi': total_porsi,
        'total_mitra': total_mitra,
        'total_nominal_rp': total_nominal_rp,
        'today': today,
    }
    return render(request, 'pos/intake.html', context)


def api_partner_products(request, partner_id):
    """
    API JSON untuk mengambil daftar menu produk yang terafiliasi dengan mitra tertentu.
    Digunakan oleh dropdown dinamis saat kasir memilih mitra.
    """
    branch_slug = request.GET.get('branch')
    products_qs = Product.objects.filter(partner_id=partner_id, is_active=True)
    
    if branch_slug:
        products_qs = products_qs.filter(branch__slug=branch_slug)

    products_data = [
        {'id': p.id, 'name': p.name, 'category': p.get_category_display()}
        for p in products_qs
    ]
    return JsonResponse({'status': 'success', 'products': products_data})

from datetime import date, timedelta
from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import redirect, get_object_or_404
from django.utils.html import format_html
from .models import DailyStock


class SmartDateRangeFilter(admin.SimpleListFilter):
    """
    Filter Tanggal Cerdas: Hari Ini, Kemarin, 3 Hari Terakhir, 7 Hari, Bulan Ini & Lalu.
    Memudahkan admin mengecek transaksi hari ini atau hari-hari sebelumnya dengan 1-klik.
    """
    title = 'Rentang Tanggal'
    parameter_name = 'date_range'

    def lookups(self, request, model_admin):
        return (
            ('today', '📅 Hari Ini (Today)'),
            ('yesterday', '⏮️ Kemarin (Yesterday)'),
            ('last_3_days', '📆 3 Hari Terakhir'),
            ('last_7_days', '🗓️ 7 Hari Terakhir'),
            ('this_month', '📊 Bulan Ini'),
            ('last_month', '📁 Bulan Lalu'),
        )

    def queryset(self, request, queryset):
        today = date.today()
        val = self.value()
        if val == 'today':
            return queryset.filter(date=today)
        elif val == 'yesterday':
            return queryset.filter(date=today - timedelta(days=1))
        elif val == 'last_3_days':
            return queryset.filter(date__gte=today - timedelta(days=3), date__lte=today)
        elif val == 'last_7_days':
            return queryset.filter(date__gte=today - timedelta(days=7), date__lte=today)
        elif val == 'this_month':
            return queryset.filter(date__year=today.year, date__month=today.month)
        elif val == 'last_month':
            first_day_this_month = today.replace(day=1)
            last_day_prev_month = first_day_this_month - timedelta(days=1)
            return queryset.filter(
                date__year=last_day_prev_month.year,
                date__month=last_day_prev_month.month
            )
        return queryset


@admin.register(DailyStock)
class DailyStockAdmin(admin.ModelAdmin):
    list_display = (
        'display_date_branch',
        'display_item',
        'display_stock_movement',
        'display_finances',
        'display_payment_status',
        'row_actions'
    )
    list_display_links = None
    list_filter = (SmartDateRangeFilter, 'branch', 'payment_status')
    search_fields = ('partner__name', 'product__name', 'branch__name')
    ordering = ('-date', 'branch', 'partner')
    list_per_page = 15
    actions = None  # Nonaktifkan checkbox & bulk action bar

    def get_queryset(self, request):
        # Optimasi ORM untuk mencegah N+1 Query pada relasi Foreign Key
        return super().get_queryset(request).select_related('branch', 'partner', 'product')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:stock_id>/set-status/<str:new_status>/',
                self.admin_site.admin_view(self.set_payment_status_view),
                name='inventory_dailystock_set_status'
            ),
        ]
        return custom_urls + urls

    def set_payment_status_view(self, request, stock_id, new_status):
        stock = get_object_or_404(DailyStock, pk=stock_id)
        valid_choices = dict(DailyStock.PAYMENT_STATUS_CHOICES)
        if new_status in valid_choices:
            stock.payment_status = new_status
            stock.save(update_fields=['payment_status', 'updated_at'])
            label = valid_choices[new_status]
            messages.success(
                request,
                f"Status pembayaran [{stock.product.name} - {stock.partner.name}] berhasil diubah ke '{label}'."
            )
        return redirect(request.META.get('HTTP_REFERER', reverse('admin:inventory_dailystock_changelist')))

    @admin.display(description='Tanggal & Cabang', ordering='date')
    def display_date_branch(self, obj):
        return format_html(
            '<div class="text-xs leading-tight py-0.5 whitespace-nowrap">'
            '  <div class="font-extrabold text-slate-900">📅 {}</div>'
            '  <div class="mt-1">'
            '    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-extrabold bg-red-50 text-brand-800 border border-red-200">'
            '      📍 {}'
            '    </span>'
            '  </div>'
            '</div>',
            obj.date.strftime('%d %b %Y'),
            obj.branch.name
        )

    @admin.display(description='Menu & Mitra UMKM', ordering='product__name')
    def display_item(self, obj):
        change_url = reverse('admin:inventory_dailystock_change', args=[obj.pk])
        return format_html(
            '<div class="py-0.5">'
            '  <a href="{}" class="font-black text-slate-900 hover:text-brand-700 text-xs sm:text-sm block transition-colors leading-snug">{}</a>'
            '  <div class="text-[11px] font-semibold text-slate-500 mt-0.5 flex items-center gap-1">'
            '    <span class="text-slate-400">Mitra:</span>'
            '    <span class="text-slate-800 font-bold">{}</span>'
            '  </div>'
            '</div>',
            change_url, obj.product.name, obj.partner.name
        )

    @admin.display(description='Pergerakan Stok (Pcs)')
    def display_stock_movement(self, obj):
        sold = obj.stock_sold
        return format_html(
            '<div class="text-xs leading-tight py-0.5 whitespace-nowrap">'
            '  <div class="text-[11px] font-medium text-slate-500">'
            '    In: <b class="text-slate-800">{}</b> • Sisa: <b class="text-slate-800">{}</b>'
            '  </div>'
            '  <div class="mt-1">'
            '    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-black bg-emerald-50 text-emerald-800 border border-emerald-200">'
            '      🔥 Terjual: {} pcs'
            '    </span>'
            '  </div>'
            '</div>',
            obj.stock_in, obj.stock_left, sold
        )

    @admin.display(description='Bagi Hasil & Margin')
    def display_finances(self, obj):
        payout_formatted = f"{obj.partner_payout:,}"
        margin_formatted = f"{obj.platform_margin:,}"
        return format_html(
            '<div class="text-xs leading-tight py-0.5 whitespace-nowrap">'
            '  <div class="font-bold text-slate-900">'
            '    Mitra: <span class="text-emerald-700 font-extrabold">Rp {}</span>'
            '  </div>'
            '  <div class="text-[10px] font-semibold text-slate-400 mt-0.5">'
            '    Margin: Rp {}'
            '  </div>'
            '</div>',
            payout_formatted, margin_formatted
        )

    @admin.display(description='Status Bagi Hasil', ordering='payment_status')
    def display_payment_status(self, obj):
        transfer_url = reverse('admin:inventory_dailystock_set_status', args=[obj.pk, 'transferred'])
        cash_url = reverse('admin:inventory_dailystock_set_status', args=[obj.pk, 'paid_cash'])
        pending_url = reverse('admin:inventory_dailystock_set_status', args=[obj.pk, 'pending'])

        if obj.payment_status == 'transferred':
            badge = '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-extrabold bg-blue-50 text-blue-800 border border-blue-200">💳 Transfer</span>'
            actions = format_html(
                '<div class="flex items-center gap-1 mt-1 text-[10px]">'
                '  <a href="{}" class="text-slate-500 hover:text-emerald-700 font-bold hover:underline">💵 Ubah Tunai</a>'
                '  <span class="text-slate-300">•</span>'
                '  <a href="{}" class="text-slate-400 hover:text-rose-600 hover:underline">Reset</a>'
                '</div>',
                cash_url, pending_url
            )
        elif obj.payment_status == 'paid_cash':
            badge = '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-extrabold bg-emerald-50 text-emerald-800 border border-emerald-200">💵 Tunai</span>'
            actions = format_html(
                '<div class="flex items-center gap-1 mt-1 text-[10px]">'
                '  <a href="{}" class="text-slate-500 hover:text-blue-700 font-bold hover:underline">💳 Ubah Transfer</a>'
                '  <span class="text-slate-300">•</span>'
                '  <a href="{}" class="text-slate-400 hover:text-rose-600 hover:underline">Reset</a>'
                '</div>',
                transfer_url, pending_url
            )
        else:
            badge = '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-extrabold bg-amber-50 text-amber-900 border border-amber-200">🟡 Belum Ditentukan</span>'
            actions = format_html(
                '<div class="flex items-center gap-1 mt-1 text-[10px]">'
                '  <a href="{}" class="px-1.5 py-0.5 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded border border-blue-200 font-bold transition-colors">💳 Transfer</a>'
                '  <a href="{}" class="px-1.5 py-0.5 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded border border-emerald-200 font-bold transition-colors">💵 Tunai</a>'
                '</div>',
                transfer_url, cash_url
            )

        return format_html('<div class="whitespace-nowrap">{}{}</div>', format_html(badge), actions)

    @admin.display(description='Aksi')
    def row_actions(self, obj):
        change_url = reverse('admin:inventory_dailystock_change', args=[obj.pk])
        delete_url = reverse('admin:inventory_dailystock_delete', args=[obj.pk])
        return format_html(
            '<div class="flex items-center gap-1.5 whitespace-nowrap">'
            '<a href="{}" class="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-brand-800 font-bold text-xs rounded-lg border border-amber-200 transition-colors">✏️ Edit</a>'
            '<a href="{}" data-delete-url="{}" data-object-name="{}" class="btn-delete-modal px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold text-xs rounded-lg border border-rose-200 transition-colors cursor-pointer">🗑️ Hapus</a>'
            '</div>',
            change_url, delete_url, delete_url, str(obj)
        )

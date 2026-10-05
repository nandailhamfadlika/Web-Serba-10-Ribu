from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import DailyCashflow
from apps.inventory.admin import SmartDateRangeFilter


@admin.register(DailyCashflow)
class DailyCashflowAdmin(admin.ModelAdmin):
    list_display = (
        'display_date_branch',
        'display_revenue',
        'display_expenses',
        'display_selisih',
        'display_notes',
        'row_actions'
    )
    list_display_links = None
    list_filter = (SmartDateRangeFilter, 'branch')
    search_fields = ('branch__name', 'notes')
    ordering = ('-date', 'branch')
    list_per_page = 15
    actions = None  # Nonaktifkan checkbox & bulk action bar

    def get_queryset(self, request):
        # Optimasi query ORM select_related untuk mencegah N+1
        return super().get_queryset(request).select_related('branch')

    @admin.display(description='Tanggal & Cabang', ordering='date')
    def display_date_branch(self, obj):
        return format_html(
            '<div class="text-xs leading-tight py-1">'
            '  <div class="font-extrabold text-slate-900 flex items-center gap-1.5">'
            '    <span>📅</span> {}'
            '  </div>'
            '  <div class="mt-1">'
            '    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-bold bg-red-50 text-brand-800 border border-red-200">'
            '      <span>📍</span> {}'
            '    </span>'
            '  </div>'
            '</div>',
            obj.date.strftime('%d %b %Y'),
            obj.branch.name
        )

    @admin.display(description='Penerimaan Kasir')
    def display_revenue(self, obj):
        setor_str = f"{obj.cash_setor:,}"
        gopay_str = f"{obj.gopay_merchant:,}"
        return format_html(
            '<div class="text-xs leading-tight py-1">'
            '  <div class="font-extrabold text-slate-800 flex items-center gap-1">'
            '    <span>💵</span> Setor Tunai: <span class="text-emerald-700">Rp {}</span>'
            '  </div>'
            '  <div class="text-[11px] font-semibold text-slate-500 mt-1 flex items-center gap-1">'
            '    <span>📱</span> GoPay/QRIS: Rp {}'
            '  </div>'
            '</div>',
            setor_str,
            gopay_str
        )

    @admin.display(description='Beban Operasional')
    def display_expenses(self, obj):
        total_exp_str = f"{obj.total_operational_expenses:,}"
        gaji_str = f"{obj.cash_terpakai_gaji:,}"
        makan_str = f"{obj.cash_terpakai_makan:,}"
        return format_html(
            '<div class="text-xs leading-tight py-1">'
            '  <div class="font-bold text-rose-700">'
            '    Total: Rp {}'
            '  </div>'
            '  <div class="text-[11px] text-slate-400 mt-0.5">'
            '    Gaji Rp{} • Makan Rp{}'
            '  </div>'
            '</div>',
            total_exp_str,
            gaji_str,
            makan_str
        )

    @admin.display(description='Hasil Rekonsiliasi (Selisih)', ordering='selisih')
    def display_selisih(self, obj):
        if obj.selisih == 0:
            return format_html(
                '<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">'
                '  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>Klop / Balance (Rp 0)'
                '</span>'
            )
        elif obj.selisih > 0:
            surplus_str = f"{obj.selisih:,}"
            return format_html(
                '<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-800 border border-blue-200">'
                '  <span>📈</span>Surplus +Rp {}'
                '</span>',
                surplus_str
            )
        else:
            kurang_str = f"{abs(obj.selisih):,}"
            return format_html(
                '<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-800 border border-rose-200">'
                '  <span>⚠️</span>Kurang -Rp {}'
                '</span>',
                kurang_str
            )

    @admin.display(description='Catatan Kasir')
    def display_notes(self, obj):
        if obj.notes:
            return format_html(
                '<span class="text-xs text-slate-600 line-clamp-1 italic max-w-xs" title="{}">"{}"</span>',
                obj.notes, obj.notes
            )
        return format_html('<span class="text-slate-300 font-mono text-xs">—</span>')

    @admin.display(description='Aksi')
    def row_actions(self, obj):
        change_url = reverse('admin:finances_dailycashflow_change', args=[obj.pk])
        delete_url = reverse('admin:finances_dailycashflow_delete', args=[obj.pk])
        return format_html(
            '<div class="flex items-center gap-1.5 whitespace-nowrap">'
            '<a href="{}" class="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-brand-800 font-bold text-xs rounded-lg border border-amber-200 transition-colors">✏️ Edit</a>'
            '<a href="{}" data-delete-url="{}" data-object-name="{}" class="btn-delete-modal px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold text-xs rounded-lg border border-rose-200 transition-colors cursor-pointer">🗑️ Hapus</a>'
            '</div>',
            change_url, delete_url, delete_url, str(obj)
        )

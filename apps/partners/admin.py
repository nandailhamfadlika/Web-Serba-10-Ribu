from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Partner, DailyAttendance

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = (
        'display_partner',
        'display_phone',
        'display_bank',
        'display_status',
        'row_actions'
    )
    list_display_links = None
    search_fields = ('name', 'phone_number', 'bank_account_name', 'bank_account_number')
    list_filter = ('is_active', 'bank_name')
    ordering = ('name',)
    list_per_page = 15
    actions = None  # Nonaktifkan checkbox & bulk action bar

    fieldsets = (
        ('👤 Identitas Mitra UMKM', {
            'fields': ('name', 'phone_number'),
            'description': 'Informasi identitas brand/nama mitra kuliner dan nomor kontak WhatsApp aktif.'
        }),
        ('💳 Informasi Rekening & E-Wallet Bagi Hasil', {
            'fields': ('bank_name', 'bank_account_name', 'bank_account_number'),
            'description': 'Data rekening bank atau e-wallet untuk pencairan bagi hasil penjualan (Rp9.000/pcs).'
        }),
        ('⚡ Status Kerjasama Mitra', {
            'fields': ('is_active',),
            'description': 'Centang untuk menandakan mitra aktif dan dapat menyuplai produk konsinyasi ke cabang.'
        }),
    )

    @admin.display(description='Nama Mitra UMKM', ordering='name')
    def display_partner(self, obj):
        initial = obj.name[0].upper() if obj.name else 'M'
        change_url = reverse('admin:partners_partner_change', args=[obj.pk])
        return format_html(
            '<div class="flex items-center gap-3 py-1">'
            '  <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-red-50 to-amber-50 border border-red-200/80 flex items-center justify-center font-black text-brand-800 text-sm shadow-2xs flex-shrink-0">'
            '    {}'
            '  </div>'
            '  <div class="min-w-0">'
            '    <a href="{}" class="font-black text-slate-900 hover:text-brand-700 text-sm leading-tight block transition-colors">{}</a>'
            '    <span class="inline-block text-[11px] font-semibold text-slate-400 mt-1">Mitra UMKM Konsinyasi</span>'
            '  </div>'
            '</div>',
            initial, change_url, obj.name
        )

    @admin.display(description='Kontak WhatsApp', ordering='phone_number')
    def display_phone(self, obj):
        if obj.phone_number:
            clean_num = obj.phone_number.replace('+', '').replace(' ', '').replace('-', '')
            return format_html(
                '<a href="https://wa.me/{}" target="_blank" class="inline-flex items-center gap-1.5 font-bold text-emerald-700 hover:text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 px-2.5 py-1 rounded-lg text-xs transition-colors">'
                '  <span>💬</span> {}'
                '</a>',
                clean_num, obj.phone_number
            )
        return format_html('<span class="text-slate-300 font-mono text-xs">— Belum Ada —</span>')

    @admin.display(description='Rekening Bagi Hasil')
    def display_bank(self, obj):
        if obj.bank_account_number:
            return format_html(
                '<div class="text-xs leading-tight">'
                '  <div class="font-extrabold text-slate-800 flex items-center gap-1"><span>💳</span> {}</div>'
                '  <div class="text-slate-500 font-mono mt-0.5">{}</div>'
                '  <div class="text-[11px] text-slate-400">a.n. {}</div>'
                '</div>',
                obj.bank_name or 'Bank/E-Wallet',
                obj.bank_account_number,
                obj.bank_account_name or '-'
            )
        return format_html('<span class="text-slate-300 font-mono text-xs">— Belum Diisi —</span>')

    @admin.display(description='Status Mitra', ordering='is_active')
    def display_status(self, obj):
        if obj.is_active:
            return format_html(
                '<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">'
                '  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>Aktif'
                '</span>'
            )
        return format_html(
            '<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-500 border border-slate-200">'
            '  Nonaktif'
            '</span>'
        )

    @admin.display(description='Aksi')
    def row_actions(self, obj):
        change_url = reverse('admin:partners_partner_change', args=[obj.pk])
        delete_url = reverse('admin:partners_partner_delete', args=[obj.pk])
        return format_html(
            '<div class="flex items-center gap-1.5 whitespace-nowrap">'
            '<a href="{}" class="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-brand-800 font-bold text-xs rounded-lg border border-amber-200 transition-colors">✏️ Edit</a>'
            '<a href="{}" data-delete-url="{}" data-object-name="{}" class="btn-delete-modal px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold text-xs rounded-lg border border-rose-200 transition-colors cursor-pointer">🗑️ Hapus</a>'
            '</div>',
            change_url, delete_url, delete_url, str(obj)
        )

@admin.register(DailyAttendance)
class DailyAttendanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'branch', 'partner', 'status', 'estimated_arrival_time', 'notes')
    list_filter = ('date', 'branch', 'status')
    search_fields = ('partner__name', 'notes')
    ordering = ('-date', 'branch', 'partner')
    list_per_page = 15

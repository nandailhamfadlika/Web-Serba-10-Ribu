from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'display_product',
        'display_partner',
        'display_branch',
        'display_status',
        'row_actions'
    )
    list_display_links = None  # Links are handled inside display_product
    list_filter = ('branch', 'category', 'is_active')
    search_fields = ('name', 'partner__name')
    ordering = ('branch', 'category', 'name')
    list_per_page = 15
    actions = None  # Nonaktifkan checkbox & bulk action bar

    fieldsets = (
        ('🍲 Informasi Menu Makanan', {
            'fields': ('name', 'category', 'photo'),
            'description': 'Lengkapi nama menu kuliner, kategori sajian, dan unggah foto produk jika ada.'
        }),
        ('🤝 Hubungkan Mitra & Cabang (Linked)', {
            'fields': ('partner', 'branch'),
            'description': 'Pilih mitra UMKM pembuat menu dan cabang gerai tempat menu ini dijual.'
        }),
        ('⚡ Status Menu', {
            'fields': ('is_active',),
            'description': 'Centang agar menu aktif dan dapat dipilih kasir saat serah terima drop barang.'
        }),
    )

    def save_model(self, request, obj, form, change):
        # Harga konsinyasi serba Rp10.000 dengan bagi hasil tetap Rp9.000 ke mitra UMKM
        if not obj.price_customer:
            obj.price_customer = 10000
        if not obj.price_partner:
            obj.price_partner = 9000
        super().save_model(request, obj, form, change)

    @admin.display(description='Menu Makanan', ordering='name')
    def display_product(self, obj):
        change_url = reverse('admin:products_product_change', args=[obj.pk])
        if obj.photo:
            thumb_html = format_html(
                '<img src="{}" alt="{}" class="w-12 h-12 object-cover rounded-xl border border-slate-200 shadow-xs flex-shrink-0">',
                obj.photo.url, obj.name
            )
        else:
            cat_icon = '🍱' if obj.category == 'makanan_berat' else ('🥐' if obj.category == 'snack' else '🧃')
            thumb_html = format_html(
                '<div class="w-12 h-12 rounded-xl bg-gradient-to-br from-red-50 to-amber-50/70 border border-red-100 flex items-center justify-center text-2xl shadow-xs flex-shrink-0">{}</div>',
                cat_icon
            )

        return format_html(
            '<div class="flex items-center gap-3 py-1">'
            '  {}'
            '  <div class="min-w-0">'
            '    <a href="{}" class="font-black text-slate-900 hover:text-brand-700 text-sm leading-tight block transition-colors">{}</a>'
            '    <span class="inline-block text-[11px] font-bold text-slate-400 mt-1">{}</span>'
            '  </div>'
            '</div>',
            thumb_html,
            change_url,
            obj.name,
            obj.get_category_display()
        )

    @admin.display(description='Mitra UMKM', ordering='partner__name')
    def display_partner(self, obj):
        return format_html(
            '<div class="flex items-center gap-1.5 font-bold text-slate-800 text-xs">'
            '  <span class="text-sm">👩‍🍳</span>'
            '  <span>{}</span>'
            '</div>',
            obj.partner.name
        )

    @admin.display(description='Cabang Gerai', ordering='branch__name')
    def display_branch(self, obj):
        return format_html(
            '<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 text-slate-700 border border-slate-200">'
            '  <span>📍</span> {}'
            '</span>',
            obj.branch.name
        )

    @admin.display(description='Status Menu', ordering='is_active')
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
        change_url = reverse('admin:products_product_change', args=[obj.pk])
        delete_url = reverse('admin:products_product_delete', args=[obj.pk])
        return format_html(
            '<div class="flex items-center gap-1.5 whitespace-nowrap">'
            '<a href="{}" class="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-brand-800 font-bold text-xs rounded-lg border border-amber-200 transition-colors">✏️ Edit</a>'
            '<a href="{}" data-delete-url="{}" data-object-name="{}" class="btn-delete-modal px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold text-xs rounded-lg border border-rose-200 transition-colors cursor-pointer">🗑️ Hapus</a>'
            '</div>',
            change_url, delete_url, delete_url, str(obj)
        )


from django.db import models

class Product(models.Model):
    """
    Menu Makanan Serba 10 Ribu.
    Harga jual serba Rp10.000 dengan porsi bagi hasil konsinyasi Rp9.000 ke mitra.
    """
    CATEGORY_CHOICES = [
        ('makanan_berat', 'Makanan Berat (Nasi/Mie/Olahan)'),
        ('snack', 'Snack / Kue Basah / Roti'),
        ('minuman', 'Minuman'),
        ('lainnya', 'Lainnya'),
    ]

    partner = models.ForeignKey(
        'partners.Partner',
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="Mitra UMKM"
    )
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="Cabang Gerai"
    )
    name = models.CharField(max_length=150, verbose_name="Nama Menu")
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='snack',
        verbose_name="Kategori Menu"
    )
    photo = models.ImageField(
        upload_to='products/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Foto Menu"
    )
    price_customer = models.PositiveIntegerField(
        default=10000,
        verbose_name="Harga Pelanggan (Rp)"
    )
    price_partner = models.PositiveIntegerField(
        default=9000,
        verbose_name="Bagi Hasil Mitra (Rp)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Menu Aktif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        verbose_name = 'Menu Produk'
        verbose_name_plural = 'Menu Produk'
        ordering = ['branch', 'category', 'name']
        indexes = [
            models.Index(fields=['branch', 'is_active']),
            models.Index(fields=['partner', 'is_active']),
        ]

    def __str__(self):
        return f"[{self.branch.name}] {self.name} ({self.partner.name})"

from django.db import models
from django.utils import timezone

class DailyStock(models.Model):
    """
    In-Take Pagi Kasir & Transaksi Harian Konsinyasi.
    Menyimpan kuantitas barang masuk subuh, sisa sore, foto bukti fisik (retensi H+7),
    serta komputasi bagi hasil mitra (Rp9.000) dan margin platform (Rp1.000).
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Belum Ditentukan (Pending)'),
        ('transferred', 'Ditransfer (Bank / E-Wallet)'),
        ('paid_cash', 'Dibayar Tunai (Cash)'),
    ]

    date = models.DateField(db_index=True, verbose_name="Tanggal Transaksi")
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.CASCADE,
        related_name='daily_stocks',
        verbose_name="Cabang"
    )
    partner = models.ForeignKey(
        'partners.Partner',
        on_delete=models.CASCADE,
        related_name='daily_stocks',
        verbose_name="Mitra UMKM"
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='daily_stocks',
        verbose_name="Menu Makanan"
    )
    stock_in = models.PositiveIntegerField(
        default=0,
        verbose_name="Barang Masuk Pagi (Pcs)"
    )
    stock_left = models.PositiveIntegerField(
        default=0,
        verbose_name="Sisa Sore / Tutup Toko (Pcs)"
    )
    proof_photo = models.ImageField(
        upload_to='proof_photos/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name="Foto Bukti Serah Terima Fisik (Retensi H+7)"
    )
    proof_uploaded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Waktu Upload Bukti"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name="Status Pembayaran Bagi Hasil"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_stocks'
        verbose_name = 'Stok & Transaksi Harian'
        verbose_name_plural = 'Stok & Transaksi Harian'
        ordering = ['-date', 'branch', 'partner', 'product']
        indexes = [
            models.Index(fields=['date', 'branch'], name='idx_dstk_date_branch'),
            models.Index(fields=['partner', 'date'], name='idx_dstk_partner_date'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['date', 'branch', 'product'],
                name='unique_stock_per_date_branch_product'
            )
        ]

    def __str__(self):
        return f"{self.date} | {self.branch.name} | {self.product.name} (Masuk: {self.stock_in}, Laku: {self.stock_sold})"

    @property
    def stock_sold(self) -> int:
        """Kuantitas terjual = barang masuk - sisa sore (min 0)."""
        return max(0, int(self.stock_in) - int(self.stock_left))

    @property
    def partner_payout(self) -> int:
        """Bagi hasil mitra = Rp9.000 x pcs terjual."""
        return self.stock_sold * 9000

    @property
    def platform_margin(self) -> int:
        """Margin keuntungan gerai = Rp1.000 x pcs terjual."""
        return self.stock_sold * 1000

    @property
    def gross_revenue(self) -> int:
        """Total omzet kotor = Rp10.000 x pcs terjual."""
        return self.stock_sold * 10000

    def save(self, *args, **kwargs):
        if self.proof_photo and not self.proof_uploaded_at:
            self.proof_uploaded_at = timezone.now()
        super().save(*args, **kwargs)

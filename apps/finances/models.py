from django.db import models

class DailyCashflow(models.Model):
    """
    Resume Kas Harian Kasir Toko & Rekonsiliasi Tutup Gerai.
    Mengadopsi format Excel rekonsiliasi kasir fisik, Gopay Merchant,
    serta potongan biaya operasional harian.
    """
    date = models.DateField(db_index=True, verbose_name="Tanggal Rekap")
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.CASCADE,
        related_name='cashflows',
        verbose_name="Cabang"
    )
    cash_setor = models.BigIntegerField(
        default=0,
        verbose_name="Uang Setor Tunai Kasir (Rp)"
    )
    cash_uang_besar = models.BigIntegerField(
        default=0,
        verbose_name="Uang Kertas Besar (Rp50k/Rp100k)"
    )
    cash_uang_receh = models.BigIntegerField(
        default=0,
        verbose_name="Uang Kertas Kecil & Logam (Rp)"
    )
    gopay_merchant = models.BigIntegerField(
        default=0,
        verbose_name="Penerimaan QRIS / GoPay Merchant (Rp)"
    )
    cash_terpakai_gaji = models.BigIntegerField(
        default=0,
        verbose_name="Pengeluaran Gaji Harian Kasir/Kru (Rp)"
    )
    cash_terpakai_makan = models.BigIntegerField(
        default=0,
        verbose_name="Pengeluaran Uang Makan Kru (Rp)"
    )
    cash_terpakai_operasional = models.BigIntegerField(
        default=0,
        verbose_name="Pengeluaran Operasional Toko (Plastik, Gas, Es Batu, dll.)"
    )
    selisih = models.BigIntegerField(
        default=0,
        verbose_name="Selisih Kas / Rekonsiliasi (Rp)"
    )
    notes = models.TextField(blank=True, verbose_name="Catatan Kasir")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_cashflows'
        verbose_name = 'Resume Kas Kasir'
        verbose_name_plural = 'Resume Kas Kasir'
        ordering = ['-date', 'branch']
        constraints = [
            models.UniqueConstraint(
                fields=['date', 'branch'],
                name='unique_cashflow_per_date_branch'
            )
        ]

    def __str__(self):
        return f"{self.date} | {self.branch.name} - Setor: Rp {self.cash_setor:,} (Selisih: Rp {self.selisih:,})"

    @property
    def total_cash_on_hand(self) -> int:
        """Total fisik uang tunai di kasir."""
        return self.cash_uang_besar + self.cash_uang_receh

    @property
    def total_operational_expenses(self) -> int:
        """Total pengeluaran operasional toko."""
        return self.cash_terpakai_gaji + self.cash_terpakai_makan + self.cash_terpakai_operasional

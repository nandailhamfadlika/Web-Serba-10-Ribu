from django.db import models

class Partner(models.Model):
    """
    Mitra UMKM Konsinyasi Serba 10 Ribu Group.
    Menyimpan data identitas, kontak WhatsApp, serta info rekening bank/e-wallet untuk bagi hasil.
    """
    name = models.CharField(max_length=150, unique=True, verbose_name="Nama Mitra")
    phone_number = models.CharField(max_length=25, blank=True, verbose_name="Nomor WhatsApp")
    bank_name = models.CharField(max_length=50, blank=True, verbose_name="Nama Bank / E-Wallet")
    bank_account_name = models.CharField(max_length=150, blank=True, verbose_name="Nama Pemilik Rekening")
    bank_account_number = models.CharField(max_length=60, blank=True, verbose_name="Nomor Rekening")
    is_active = models.BooleanField(default=True, verbose_name="Mitra Aktif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'partners'
        verbose_name = 'Mitra UMKM'
        verbose_name_plural = 'Mitra UMKM'
        ordering = ['name']

    def __str__(self):
        return self.name


class DailyAttendance(models.Model):
    """
    Absensi Rencana Drop Barang H-1 (Operator-Assisted via WhatsApp).
    Menentukan menu mana yang tampil di modul 'Intip Menu Besok'.
    """
    STATUS_CHOICES = [
        ('hadir', 'Hadir Besok'),
        ('libur', 'Libur / Tidak Antar'),
    ]

    date = models.DateField(db_index=True, verbose_name="Tanggal Rencana Drop (Besok)")
    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name="Mitra UMKM"
    )
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name="Cabang"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='hadir',
        verbose_name="Status Kehadiran"
    )
    estimated_arrival_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Perkiraan Waktu Tiba (Subuh - 08:00)"
    )
    notes = models.CharField(max_length=255, blank=True, verbose_name="Catatan Drop Barang")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'daily_attendances'
        verbose_name = 'Absensi H-1 Mitra'
        verbose_name_plural = 'Absensi H-1 Mitra'
        ordering = ['-date', 'branch', 'partner']
        constraints = [
            models.UniqueConstraint(
                fields=['date', 'partner', 'branch'],
                name='unique_partner_attendance_per_date_branch'
            )
        ]

    def __str__(self):
        return f"{self.date} | {self.branch.name} | {self.partner.name} - {self.get_status_display()}"

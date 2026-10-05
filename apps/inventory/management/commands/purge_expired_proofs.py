"""
Management Command: purge_expired_proofs.py
Kebijakan Retensi Media H+7 Serba 10 Ribu Group.

Menghapus file fisik bukti serah terima (proof_photo) yang usianya lebih dari 7 hari,
serta mengosongkan field database menjadi NULL untuk menghemat ruang disk storage.
Semua data riwayat angka kuantitas (stock_in, stock_left, terjual, rupiah) TETAP AMAN TERSIMPAN.
"""
import os
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.db import models, transaction
from apps.inventory.models import DailyStock


class Command(BaseCommand):
    help = (
        "Menghapus file fisik bukti foto serah terima (proof_photo) "
        "yang berumur lebih dari 7 hari (H+7) dan mengeset kolom DB ke NULL."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help="Batas umur hari file bukti sebelum dihapus (Default: 7 hari)."
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Simulasi audit: Menampilkan daftar file tanpa menghapus fisik ataupun mengubah database."
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help="Ukuran batch pemrosesan database untuk efisiensi memori (Default: 500)."
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        batch_size = options['batch_size']

        today = date.today()
        # Cutoff: record dengan tanggal sebelum (hari ini - X hari)
        cutoff_date = today - timedelta(days=days)

        mode_label = "[DRY-RUN SIMULASI]" if dry_run else "[LIVE PURGE]"
        self.stdout.write(self.style.NOTICE(f"\n======================================================="))
        self.stdout.write(self.style.NOTICE(f" {mode_label} Kebijakan Retensi Media H+{days}"))
        self.stdout.write(self.style.NOTICE(f" Tanggal Hari Ini: {today} | Batas Cutoff: <= {cutoff_date}"))
        self.stdout.write(self.style.NOTICE(f"=======================================================\n"))

        # Mengambil record kadaluarsa yang masih memiliki file foto bukti
        # Menggunakan .only() untuk optimasi query memori (django-perf-review)
        expired_stocks = (
            DailyStock.objects
            .filter(date__lte=cutoff_date)
            .exclude(models.Q(proof_photo='') | models.Q(proof_photo__isnull=True))
            .only('id', 'date', 'proof_photo')
            .order_by('date')
        )

        total_candidates = expired_stocks.count()
        if total_candidates == 0:
            self.stdout.write(self.style.SUCCESS(
                f"-> Tidak ada file bukti foto kadaluarsa (<= {cutoff_date}). Storage bersih!"
            ))
            return

        self.stdout.write(f"Ditemukan {total_candidates} catatan transaksi kadaluarsa yang memiliki bukti foto.")

        files_deleted = 0
        files_missing = 0
        bytes_freed = 0
        records_to_update = []

        for stock in expired_stocks.iterator(chunk_size=batch_size):
            photo_field = stock.proof_photo
            file_name = photo_field.name if photo_field else ""

            if not file_name:
                continue

            file_size = 0
            file_exists = False

            try:
                if default_storage.exists(file_name):
                    file_exists = True
                    try:
                        file_size = default_storage.size(file_name)
                    except Exception:
                        file_size = 0
            except Exception as e:
                self.stdout.write(self.style.WARNING(f" [!] Gagal memeriksa file {file_name}: {e}"))

            if dry_run:
                status_str = f"Akan dihapus ({file_size / 1024:.1f} KB)" if file_exists else "File fisik tidak ditemukan"
                self.stdout.write(f"  [SIMULASI] ID {stock.id} | Tgl {stock.date} | {file_name} -> {status_str}")
                if file_exists:
                    files_deleted += 1
                    bytes_freed += file_size
                else:
                    files_missing += 1
                records_to_update.append(stock)
            else:
                # Mode Eksekusi Nyata
                if file_exists:
                    try:
                        default_storage.delete(file_name)
                        files_deleted += 1
                        bytes_freed += file_size
                    except OSError as err:
                        self.stdout.write(self.style.ERROR(
                            f"  [ERROR] Gagal menghapus file fisik {file_name}: {err}"
                        ))
                        continue
                else:
                    files_missing += 1

                # Kosongkan relasi field foto di model
                stock.proof_photo = None
                records_to_update.append(stock)

                # Batch update per batch_size untuk efisiensi database
                if len(records_to_update) >= batch_size:
                    with transaction.atomic():
                        DailyStock.objects.bulk_update(records_to_update, ['proof_photo'])
                    records_to_update.clear()

        # Update sisa record yang tersisa
        if not dry_run and records_to_update:
            with transaction.atomic():
                DailyStock.objects.bulk_update(records_to_update, ['proof_photo'])

        # Laporan Ringkasan Eksekusi
        freed_kb = bytes_freed / 1024
        freed_mb = freed_kb / 1024

        self.stdout.write(self.style.SUCCESS(f"\n-------------------------------------------------------"))
        self.stdout.write(self.style.SUCCESS(f" REKAPITULASI RETENSI MEDIA H+{days}:"))
        self.stdout.write(f"  - Total Record Diproses      : {total_candidates}")
        self.stdout.write(f"  - File Fisik Dihapus         : {files_deleted} file")
        if files_missing > 0:
            self.stdout.write(self.style.WARNING(f"  - File Fisik Sudah Hilang    : {files_missing} file"))
        self.stdout.write(f"  - Ruang Storage Dibebaskan   : {freed_kb:.2f} KB ({freed_mb:.3f} MB)")
        if dry_run:
            self.stdout.write(self.style.NOTICE("  - Status Database            : TIDAK BERUBAH (Dry Run)"))
        else:
            self.stdout.write(self.style.SUCCESS("  - Status Database            : proof_photo diset ke NULL"))
            self.stdout.write(self.style.SUCCESS("  - Integritas Transaksi       : 100% UTUH (Angka kuantitas tersimpan)"))
        self.stdout.write(self.style.SUCCESS(f"-------------------------------------------------------\n"))

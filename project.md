# SPESIFIKASI KEBUTUHAN SISTEM (SRS) & DESAIN ARSITEKTUR
## Proyek: Platform Web-GIS Store Locator, Live Inventory, dan Manajemen Konsinyasi
## Mitra: Serba 10 Ribu Group (Cabang Ciomas & Cabang Dramaga)

---

## 1. PENDAHULUAN & DATA LOKASI GEOSPASIAL
Serba 10 Ribu Group adalah jaringan gerai konsinyasi offline kuliner sarapan lokal serba Rp10.000 dengan margin platform Rp1.000 dan bagi hasil mitra Rp9.000. Sistem ini berbasis Web-GIS yang mengarahkan pembeli langsung datang ke gerai fisik terdekat.

### Data Titik Cabang Fisik Resmi:
1. **Cabang Ciomas:**
   * Alamat: Jl. Raya Ciomas No. 320, Pagelaran, Kec. Ciomas, Kabupaten Bogor, Jawa Barat
   * Koordinat: Latitude `-6.60278`, Longitude `106.76442`
   * Google Maps URL: `https://maps.app.goo.gl/2FwwUpYJcVNjBRNd8`
2. **Cabang Dramaga:**
   * Alamat: Jl. Raya Dramaga (Komplek Ruko Margajaya / Koridor Kampus IPB Dramaga), Kec. Dramaga, Kabupaten Bogor, Jawa Barat
   * Koordinat: Latitude `-6.57467`, Longitude `106.74567`
   * Google Maps URL: `https://maps.app.goo.gl/U9r7WdR4peRTAcyD7`

---

## 2. ARSITEKTUR DATA & STRUKTUR TABEL (POSTGRESQL / POSTGIS)

### A. Tabel `Branch` (Cabang)
* `id` (PK, Integer/UUID)
* `name` (Varchar: "Serba 10 Ribu Ciomas", "Serba 10 Ribu Dramaga")
* `slug` (ciomas, dramaga)
* `address` (Text)
* `latitude` (Decimal: 9 digit, precision 6) -> Ciomas: -6.60278, Dramaga: -6.57467
* `longitude` (Decimal: 9 digit, precision 6) -> Ciomas: 106.76442, Dramaga: 106.74567
* `location` (PointField PostGIS: SRID 4326 untuk kalkulasi radius jarak)
* `gmaps_url` (URLField)
* `opening_hours` (Varchar: "06:00 - 10:00 WIB")
* `is_active` (Boolean: Default True)

### B. Tabel `Partner` (Mitra UMKM)
* `id` (PK)
* `name` (Varchar - Nama Mitra, misal: "Ani Brownies", "Fitri Bolen", dll.)
* `phone_number` (Varchar - WhatsApp)
* `bank_name` (Varchar - BCA, BRI, DANA, BSI, Cash)
* `bank_account_name` (Varchar - Pemilik Rekening)
* `bank_account_number` (Varchar - No Rekening)
* `default_payment_method` (Enum: Transfer, Cash)
* `is_active` (Boolean)
* `created_at` (Timestamp)

### C. Tabel `Product` (Menu Makanan)
* `id` (PK)
* `partner_id` (FK -> Partner)
* `branch_id` (FK -> Branch)
* `name` (Varchar - Nama Menu, misal: "Nasi Uduk Ayam", "Dimsum Mentai")
* `category` (Enum: Makanan Berat, Snack/Kue Basah, Minuman, Lainnya)
* `photo` (ImageField / URL)
* `price_customer` (Integer: Default 10000)
* `price_partner` (Integer: Default 9000)
* `is_active` (Boolean)

### D. Tabel `DailyAttendance` (Absensi Drop Barang H-1 Operator-Assisted)
* `id` (PK)
* `date` (Date - Tanggal Rencana Drop Besok)
* `partner_id` (FK -> Partner)
* `branch_id` (FK -> Branch)
* `status` (Enum: Hadir, Libur)
* `estimated_arrival_time` (Time - Subuh s.d. 08.00 WIB)
* `notes` (Text)

### E. Tabel `DailyStock` (In-Take Pagi Kasir & Transaksi)
* `id` (PK)
* `date` (Date)
* `branch_id` (FK -> Branch)
* `partner_id` (FK -> Partner)
* `product_id` (FK -> Product)
* `stock_in` (Integer - Barang Masuk Pagi)
* `stock_left` (Integer - Sisa Sore/Tutup Toko)
* `stock_sold` (Integer - Computed: stock_in - stock_left)
* `partner_payout` (BigInteger - Computed: stock_sold * 9000)
* `platform_margin` (BigInteger - Computed: stock_sold * 1000)
* `proof_photo` (ImageField, Nullable)
* `proof_uploaded_at` (Timestamp)
* `payment_status` (Enum: Pending, Transferred, Paid Cash)

### F. Tabel `DailyCashflow` (Resume Kas Kasir - Format Excel Mitra)
* `id` (PK)
* `date` (Date)
* `branch_id` (FK -> Branch)
* `cash_setor` (BigInteger)
* `cash_uang_besar` (BigInteger)
* `cash_uang_receh` (BigInteger)
* `gopay_merchant` (BigInteger)
* `cash_terpakai_gaji` (BigInteger)
* `cash_terpakai_makan` (BigInteger)
* `cash_terpakai_operasional` (BigInteger)
* `selisih` (BigInteger)

---

## 3. MODUL FITUR UTAMA

### Modul 1: Base Page Web-GIS Publik
* **Branch Switcher:** Toggle antara [Cabang Ciomas] dan [Cabang Dramaga].
* **Fitur "Cari Cabang Terdekat":** Mengambil geolocation browser pengguna dan mengkalkulasi jarak terpendek ke titik Ci (-6.60278, 106.76442) atau Dra (-6.57467, 106.74567).
* **Leaflet Map Interactive:** Marker kustom untuk kedua cabang, info popup jam buka, dan tombol rute navigasi Google Maps.
* **Live In-Store Inventory:** Menampilkan katalog barang yang masuk pagi hari (ready stock) per cabang.
* **Intip Menu Besok:** Menampilkan menu dari mitra yang absen `Hadir` pada tabel `DailyAttendance` untuk besok pagi.

### Modul 2: Fast In-Take POS (Kasir Pagi)
* Dropdown pencarian Mitra -> Pilih Menu -> Input Jumlah Qty Masuk -> Ambil Foto Bukti Serah Terima Fisik.
* Tombol Tambah Mitra Baru (Modal popup cepat untuk mitra baru tanpa keluar halaman kasir).

### Modul 3: Kebijakan Retensi Media Otomatis (Auto-Purge H+7)
* Django Management Command / Cron Job harian: Menghapus file fisik gambar `proof_photo` dari storage jika usianya `> 7 hari` dan mengubah field db menjadi `NULL`. Seluruh angka kuantitas transaksi tetap aman tersimpan.

### Modul 4: Dashboard & Executive Reporting
* **Matriks Summary Bulanan Mitra:** Mengadopsi struktur spreadsheet asli (31 kolom hari, baris nama mitra, angka pcs terjual, indikator 0 untuk libur).
* **Resume Kas Harian Kasir:** Mengadopsi tabel rekonsiliasi kas riil, Gopay, biaya operasional, dan selisih kas.
* **Branch Comparison (Ciomas vs Dramaga):** Grafik komparasi head-to-head (Omzet, Volume Penjualan, Mitra Aktif) dengan toggle rentang waktu (1 Minggu, 2 Minggu, 3 Minggu, 1 Bulan, 1 Tahun).
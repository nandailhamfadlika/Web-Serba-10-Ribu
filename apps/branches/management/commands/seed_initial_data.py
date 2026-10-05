"""
Management Command: seed_initial_data.py
Mengisi data resmi Cabang Ciomas & Dramaga, Mitra UMKM Riil dari Klien,
Menu Kuliner Awal, serta Sample Absensi H-1 dan Stok Harian.
"""
from django.core.management.base import BaseCommand
from datetime import date, timedelta
from apps.core.gis_compat import HAS_GDAL
from apps.branches.models import Branch
from apps.partners.models import Partner, DailyAttendance
from apps.products.models import Product
from apps.inventory.models import DailyStock

if HAS_GDAL:
    from django.contrib.gis.geos import Point
else:
    Point = None


class Command(BaseCommand):
    help = 'Seed data resmi Cabang Ciomas & Dramaga, Mitra UMKM Riil Serba 10 Ribu, dan Data Awal'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(">>> Memulai proses seeding data resmi Serba 10 Ribu Group..."))

        # =========================================================================
        # 1. SEED DUA CABANG RESMI BOGOR (SESUAI KOORDINAT PRESISI SRS)
        # =========================================================================
        branches_data = [
            {
                'name': 'Serba 10 Ribu Ciomas',
                'slug': 'ciomas',
                'address': 'Jl. Raya Ciomas No. 320, Pagelaran, Kec. Ciomas, Kabupaten Bogor, Jawa Barat',
                'latitude': -6.60278,
                'longitude': 106.76442,
                'gmaps_url': 'https://maps.app.goo.gl/2FwwUpYJcVNjBRNd8',
                'opening_hours': '06:00 - 10:00 WIB',
                'is_active': True,
            },
            {
                'name': 'Serba 10 Ribu Dramaga',
                'slug': 'dramaga',
                'address': 'Jl. Raya Dramaga (Komplek Ruko Margajaya / Koridor Kampus IPB Dramaga), Kec. Dramaga, Kabupaten Bogor, Jawa Barat',
                'latitude': -6.57467,
                'longitude': 106.74567,
                'gmaps_url': 'https://maps.app.goo.gl/U9r7WdR4peRTAcyD7',
                'opening_hours': '06:00 - 10:00 WIB',
                'is_active': True,
            }
        ]

        branches = {}
        for b_data in branches_data:
            lat = b_data['latitude']
            lng = b_data['longitude']
            defaults = {
                'address': b_data['address'],
                'latitude': lat,
                'longitude': lng,
                'gmaps_url': b_data['gmaps_url'],
                'opening_hours': b_data['opening_hours'],
                'is_active': b_data['is_active'],
            }
            if HAS_GDAL and Point:
                defaults['location'] = Point(lng, lat, srid=4326)

            branch, created = Branch.objects.update_or_create(
                slug=b_data['slug'],
                defaults={'name': b_data['name'], **defaults}
            )
            branches[b_data['slug']] = branch
            status = "Dibuat" if created else "Sudah Ada (Diperbarui)"
            self.stdout.write(f" [Cabang] {branch.name} -> {status}")

        # =========================================================================
        # 2. DAFTAR NAMA MITRA UMKM RESMI DARI USER
        # =========================================================================
        ciomas_partner_names = [
            "Abi zaki", "Afifah", "Aina", "Ani Brownies", "Bunda Tasya",
            "Bu Joko (Nur)", "Cindra", "Dena", "Devi", "Dian", "Dina",
            "Erti", "Fani", "Fitri Bolen", "Ghina", "Hani", "Helen",
            "Hessy", "Ika", "Intan", "Ita", "Lela", "Mama Aish",
            "Mama Cantika", "Mama Fitri", "Mama Luthfi", "Marsini",
            "Maryani", "Meliasari", "Mella", "Mika", "Nia", "Omah lopis",
            "Puji", "Putri", "Rayyan", "Saanan", "Sasan", "Sheilla",
            "Shofi", "Sinar Sari", "Sobari", "Sumba", "Ulil", "Vita",
            "Yeni Martin", "Zendy", "Intan Brule", "Bu iyam", "Beni",
            "Ria", "Ridwan", "Rama", "Fatimah", "Refa"
        ]

        dramaga_partner_names = [
            "Afifah", "Aina", "Bella", "Benni", "Bunda Tasya", "Dila",
            "Fani", "Fatimah", "Fitri", "Hani", "Ika", "Intan", "Inten",
            "Ita", "Kania", "Lia", "Mamika", "Marsya", "Maryani",
            "Momkai", "Muji", "Mutia", "Nia", "Nia Takoyaki", "Refa",
            "Ria", "Ridwan", "Sasan", "Septi", "Silvia", "Sinarsari",
            "Siti Homsa", "Syifa", "Tia", "Tika", "Vita", "Wieke",
            "Yeli", "Yulia", "Zendy"
        ]

        # Gabungkan semua nama unik mitra
        all_unique_partner_names = sorted(list(set(ciomas_partner_names + dramaga_partner_names)))
        self.stdout.write(f" [Mitra] Total Mitra Unik Teridentifikasi: {len(all_unique_partner_names)} Mitra")

        partners = {}
        for p_name in all_unique_partner_names:
            clean_name = p_name.strip()
            partner, _ = Partner.objects.update_or_create(
                name=clean_name,
                defaults={
                    'is_active': True,
                }
            )
            partners[clean_name] = partner

        self.stdout.write(self.style.SUCCESS(f" [Mitra] {len(partners)} Mitra berhasil disimpan ke database."))

        # =========================================================================
        # 3. CONTOH MENU PRODUK KULINER (FLEKSIBEL SESUAI PERMINTAAN USER)
        # =========================================================================
        sample_menu_matrix = [
            # Cabang Ciomas
            {"partner": "Ani Brownies", "branch": "ciomas", "name": "Fudgy Brownies Shiny Crust", "cat": "snack"},
            {"partner": "Fitri Bolen", "branch": "ciomas", "name": "Bolen Pisang Cokelat Lumer", "cat": "snack"},
            {"partner": "Abi zaki", "branch": "ciomas", "name": "Nasi Uduk Betawi Komplit", "cat": "makanan_berat"},
            {"partner": "Afifah", "branch": "ciomas", "name": "Dimsum Mentai Mozarella", "cat": "makanan_berat"},
            {"partner": "Aina", "branch": "ciomas", "name": "Kue Lupis Ketan Gula Merah", "cat": "snack"},
            {"partner": "Bunda Tasya", "branch": "ciomas", "name": "Kimbab Beef Teriyaki", "cat": "makanan_berat"},
            {"partner": "Mama Cantika", "branch": "ciomas", "name": "Nasi Kuning Telur Balado", "cat": "makanan_berat"},
            {"partner": "Sinar Sari", "branch": "ciomas", "name": "Risol Mayo Keju Lumer", "cat": "snack"},
            {"partner": "Vita", "branch": "ciomas", "name": "Chicken Wings BBQ Honey", "cat": "makanan_berat"},
            {"partner": "Zendy", "branch": "ciomas", "name": "Mochi Daifuku Cokelat Susu", "cat": "snack"},

            # Cabang Dramaga
            {"partner": "Bella", "branch": "dramaga", "name": "Nasi Tongkol Suwir Kemangi", "cat": "makanan_berat"},
            {"partner": "Dila", "branch": "dramaga", "name": "Nasi Bakar Cumi Pedas Gurih", "cat": "makanan_berat"},
            {"partner": "Fani", "branch": "dramaga", "name": "Bomboloni Nutella Lumer", "cat": "snack"},
            {"partner": "Fitri", "branch": "dramaga", "name": "Bolen Pisang Keju Premium", "cat": "snack"},
            {"partner": "Hani", "branch": "dramaga", "name": "Nasi Liwet Ayam Bakar Madu", "cat": "makanan_berat"},
            {"partner": "Ika", "branch": "dramaga", "name": "Nasi Chicken Katsu Curry", "cat": "makanan_berat"},
            {"partner": "Intan", "branch": "dramaga", "name": "Spaghetti Brulee Creamy", "cat": "makanan_berat"},
            {"partner": "Lia", "branch": "dramaga", "name": "Mini Pizza Sosis Mozarella", "cat": "snack"},
            {"partner": "Momkai", "branch": "dramaga", "name": "Nasi Paru Mercon Pedas Nampol", "cat": "makanan_berat"},
            {"partner": "Nia Takoyaki", "branch": "dramaga", "name": "Takoyaki Gurita Jumbo (Isi 4)", "cat": "snack"},
            {"partner": "Yulia", "branch": "dramaga", "name": "Pempek Palembang Asli Cuko Kental", "cat": "makanan_berat"},
        ]

        products = []
        for m in sample_menu_matrix:
            if m['partner'] in partners and m['branch'] in branches:
                prod, _ = Product.objects.update_or_create(
                    partner=partners[m['partner']],
                    branch=branches[m['branch']],
                    name=m['name'],
                    defaults={
                        'category': m['cat'],
                        'price_customer': 10000,
                        'price_partner': 9000,
                        'is_active': True,
                    }
                )
                products.append(prod)

        self.stdout.write(f" [Menu] {len(products)} Produk Menu Makanan berhasil disiapkan.")

        # =========================================================================
        # 4. SAMPLE DATA OPERASIONAL: STOK HARI INI & ABSENSI H-1
        # =========================================================================
        today = date.today()
        tomorrow = today + timedelta(days=1)

        # Stok Hari Ini (Tampil di Live In-Store Inventory Web-GIS)
        for prod in products:
            DailyStock.objects.update_or_create(
                date=today,
                branch=prod.branch,
                partner=prod.partner,
                product=prod,
                defaults={
                    'stock_in': 20,
                    'stock_left': 5,
                    'payment_status': 'pending',
                }
            )

        # Absensi Besok (Tampil di Intip Menu Besok H-1)
        for prod in products[:12]:
            DailyAttendance.objects.update_or_create(
                date=tomorrow,
                partner=prod.partner,
                branch=prod.branch,
                defaults={
                    'status': 'hadir',
                    'estimated_arrival_time': '05:30:00',
                    'notes': 'Siap antar subuh 20 porsi fresh',
                }
            )

        self.stdout.write(self.style.SUCCESS(">>> [SUKSES] Seeding data awal Serba 10 Ribu Group selesai 100%!"))

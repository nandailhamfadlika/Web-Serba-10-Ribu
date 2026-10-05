from django.db import models
from apps.core.gis_compat import HAS_GDAL, haversine_distance_km

if HAS_GDAL:
    from django.contrib.gis.db import models as gis_models
else:
    gis_models = None


class Branch(models.Model):
    """
    Physical Branch Hub for Serba 10 Ribu Group (Ciomas & Dramaga).
    Supports PostGIS spatial PointField when GDAL is present, with Decimal fallback coordinates.
    """
    name = models.CharField(max_length=120, verbose_name="Nama Cabang")
    slug = models.SlugField(max_length=60, unique=True, verbose_name="Slug Cabang")
    address = models.TextField(verbose_name="Alamat Lengkap")
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, verbose_name="Latitude"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, verbose_name="Longitude"
    )
    
    if HAS_GDAL and gis_models:
        location = gis_models.PointField(
            srid=4326, geography=True, spatial_index=True, null=True, blank=True,
            verbose_name="Titik Lokasi PostGIS"
        )
    
    gmaps_url = models.URLField(max_length=300, verbose_name="Google Maps URL")
    opening_hours = models.CharField(
        max_length=60, default="06:00 - 10:00 WIB", verbose_name="Jam Operasional"
    )
    is_active = models.BooleanField(default=True, verbose_name="Cabang Aktif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'branches'
        verbose_name = 'Cabang'
        verbose_name_plural = 'Cabang'
        ordering = ['name']

    def __str__(self):
        return self.name

    def distance_to(self, user_lat: float, user_lng: float) -> float:
        """
        Returns geodesic distance in kilometers from given user coordinates.
        """
        return haversine_distance_km(float(self.latitude), float(self.longitude), user_lat, user_lng)

    @property
    def logo_url(self) -> str:
        """
        Returns the brand logo path based on branch slug.
        """
        if self.slug and 'dramaga' in self.slug.lower():
            return '/media/Logo/serba10ribudramaga.jpeg'
        return '/media/Logo/Serba10ribuciomas.jpeg'

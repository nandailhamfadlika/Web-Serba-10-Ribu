"""
GIS Compatibility Helper for Serba 10 Ribu Group Web-GIS.
Gracefully handles both PostGIS/GDAL production environments and local environments
where C-libraries (GDAL/GEOS) might not be installed on Windows.
"""
import math

HAS_GDAL = False
try:
    from django.contrib.gis import gdal
    HAS_GDAL = bool(getattr(gdal, 'HAS_GDAL', False))
except Exception:
    HAS_GDAL = False

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees) using Haversine formula.
    Returns distance in kilometers.
    """
    # Convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371.0 # Radius of earth in kilometers
    return round(c * r, 2)

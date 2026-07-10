"""Hilfsfunktionen für Geometrie-Konvertierung.

PostGIS-Spalten für Gebiete/Cluster sind strikt als MULTIPOLYGON typisiert.
Von der Karte kommt beim Zeichnen aber ein einfaches Polygon - dieses muss
vor dem Speichern immer in ein MultiPolygon (mit einem Teilpolygon) gewandelt
werden, sonst lehnt PostGIS den Insert mit einem Geometrietyp-Fehler ab.
"""
from shapely.geometry import shape, MultiPolygon, Polygon
from geoalchemy2.shape import from_shape


def geojson_to_multipolygon_ewkb(geojson: dict, srid: int = 4326):
    """Wandelt ein GeoJSON Polygon oder MultiPolygon in ein für die DB
    passendes MultiPolygon-Geometrieobjekt (EWKB via GeoAlchemy2)."""
    geom = shape(geojson)
    if isinstance(geom, Polygon):
        geom = MultiPolygon([geom])
    elif not isinstance(geom, MultiPolygon):
        raise ValueError(f"Erwartet wurde Polygon oder MultiPolygon, erhalten: {geom.geom_type}")
    return from_shape(geom, srid=srid)

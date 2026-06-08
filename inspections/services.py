"""Services de géolocalisation et géofencing"""

from math import radians, cos, sin, asin, sqrt
from decimal import Decimal


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcule la distance en kilomètres entre deux points GPS
    en utilisant la formule de Haversine
    """
    # Convertir en radians
    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])

    # Formule de Haversine
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # Rayon de la Terre en km
    r = 6371

    return c * r


def is_within_geofence(point_lat, point_lon, center_lat, center_lon, radius_km=1.0):
    """
    Vérifie si un point GPS est dans une zone géofence circulaire

    Args:
        point_lat: Latitude du point
        point_lon: Longitude du point
        center_lat: Latitude du centre de la zone
        center_lon: Longitude du centre de la zone
        radius_km: Rayon de la zone en km (défaut: 1km)

    Returns:
        bool: True si le point est dans la zone
    """
    distance = haversine_distance(point_lat, point_lon, center_lat, center_lon)
    return distance <= radius_km


def find_nearest_zone(latitude, longitude):
    """
    Trouve la zone d'inspection la plus proche d'un point GPS

    Returns:
        InspectionZone ou None
    """
    from .models import InspectionZone

    zones = InspectionZone.objects.filter(is_active=True)
    nearest_zone = None
    min_distance = float('inf')

    for zone in zones:
        if zone.latitude and zone.longitude:
            distance = haversine_distance(
                latitude, longitude,
                zone.latitude, zone.longitude
            )
            if distance < min_distance:
                min_distance = distance
                nearest_zone = zone

    return nearest_zone, min_distance if nearest_zone else (None, None)


def get_nearby_enterprises(latitude, longitude, radius_km=5.0):
    """
    Récupère les entreprises dans un rayon donné

    Returns:
        QuerySet d'entreprises
    """
    from enterprises.models import Enterprise

    all_enterprises = Enterprise.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
        is_active=True
    )

    nearby = []
    for enterprise in all_enterprises:
        distance = haversine_distance(
            latitude, longitude,
            enterprise.latitude, enterprise.longitude
        )
        if distance <= radius_km:
            enterprise._distance = distance  # Ajouter la distance comme attribut
            nearby.append(enterprise)

    # Trier par distance
    nearby.sort(key=lambda e: e._distance)

    return nearby


def get_nearby_complaints(latitude, longitude, radius_km=5.0):
    """
    Récupère les plaintes dans un rayon donné

    Returns:
        Liste de plaintes avec distance
    """
    from complaints.models import Complaint

    all_complaints = Complaint.objects.filter(
        workplace_latitude__isnull=False,
        workplace_longitude__isnull=False
    )

    nearby = []
    for complaint in all_complaints:
        distance = haversine_distance(
            latitude, longitude,
            complaint.workplace_latitude, complaint.workplace_longitude
        )
        if distance <= radius_km:
            nearby.append({
                'complaint': complaint,
                'distance_km': round(distance, 2)
            })

    # Trier par distance
    nearby.sort(key=lambda x: x['distance_km'])

    return nearby


def validate_field_presence(inspector_lat, inspector_lon, workplace_lat, workplace_lon, max_distance_km=0.5):
    """
    Valide que l'inspecteur est bien sur le lieu de travail

    Args:
        max_distance_km: Distance maximale acceptable en km (défaut: 500m)

    Returns:
        dict avec is_valid et distance
    """
    distance = haversine_distance(
        inspector_lat, inspector_lon,
        workplace_lat, workplace_lon
    )

    is_valid = distance <= max_distance_km

    return {
        'is_valid': is_valid,
        'distance_km': round(distance, 3),
        'distance_meters': int(distance * 1000),
        'max_allowed_km': max_distance_km
    }


def generate_heatmap_data(complaint_type=None):
    """
    Génère les données pour une heatmap des plaintes

    Returns:
        Liste de points [lat, lon, intensity]
    """
    from complaints.models import Complaint

    complaints = Complaint.objects.filter(
        workplace_latitude__isnull=False,
        workplace_longitude__isnull=False
    )

    if complaint_type:
        complaints = complaints.filter(complaint_type=complaint_type)

    heatmap_data = []
    for complaint in complaints:
        heatmap_data.append([
            float(complaint.workplace_latitude),
            float(complaint.workplace_longitude),
            1  # Intensité (peut être ajustée selon priorité)
        ])

    return heatmap_data


def calculate_inspection_route(inspector_id):
    """
    Calcule un itinéraire optimal pour les inspections du jour

    Returns:
        Liste ordonnée d'inspections
    """
    from .models import InspectionRecord
    from django.utils import timezone
    from datetime import timedelta

    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    inspections = InspectionRecord.objects.filter(
        inspector_id=inspector_id,
        scheduled_date__gte=today,
        scheduled_date__lt=tomorrow,
        is_completed=False
    )

    # Simple algorithme: trier par proximité géographique
    # (Un algorithme TSP serait plus optimal mais plus complexe)

    if not inspections:
        return []

    route = []
    remaining = list(inspections)

    # Commencer par la première inspection
    current = remaining.pop(0)
    route.append(current)

    while remaining:
        # Trouver la plus proche
        nearest = None
        min_distance = float('inf')

        for inspection in remaining:
            if (current.enterprise.latitude and current.enterprise.longitude and
                inspection.enterprise.latitude and inspection.enterprise.longitude):
                distance = haversine_distance(
                    current.enterprise.latitude, current.enterprise.longitude,
                    inspection.enterprise.latitude, inspection.enterprise.longitude
                )
                if distance < min_distance:
                    min_distance = distance
                    nearest = inspection

        if nearest:
            route.append(nearest)
            remaining.remove(nearest)
            current = nearest
        else:
            # Si pas de coordonnées, ajouter à la fin
            route.extend(remaining)
            break

    return route

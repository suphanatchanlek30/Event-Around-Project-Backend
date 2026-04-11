import math

class LocationService:
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        # Haversine formula to calculate distance between two points on Earth
        R = 6371  # Earth's radius in kilometers
        
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine formula
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distance = R * c
        return distance

    def is_within_radius(self, distance_km: float, radius_km: float) -> bool:
        return distance_km <= radius_km

    def validate_coordinates(self, latitude: float, longitude: float) -> bool:
        return -90 <= latitude <= 90 and -180 <= longitude <= 180

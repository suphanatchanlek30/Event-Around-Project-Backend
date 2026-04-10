class LocationService:
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        raise NotImplementedError("calculate_distance is not implemented in skeleton phase.")

    def is_within_radius(self, user_lat: float, user_lon: float, event_lat: float, event_lon: float, radius_km: float) -> bool:
        raise NotImplementedError("is_within_radius is not implemented in skeleton phase.")

    def validate_coordinates(self, latitude: float, longitude: float) -> bool:
        raise NotImplementedError("validate_coordinates is not implemented in skeleton phase.")

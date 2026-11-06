from rules.base import CityRules
from rules.exceptions import RestrictedZoneError

class RomeRules(CityRules):
    def validate_movement(self, vehicle):
        lat, lon = vehicle.gps
        if self.is_restricted_zone(lat, lon):
            raise RestrictedZoneError("Restricted zone entered")

    def is_restricted_zone(self, lat, lon):
        return lat > 41.9  # example

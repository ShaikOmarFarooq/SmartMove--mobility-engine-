from rules.base import CityRules
from rules.exceptions import HelmetRequiredError

class MilanRules(CityRules):
    def on_unlock(self, vehicle, user):
        if not vehicle.helmet_present:
            raise HelmetRequiredError("Helmet not detected")

class CityRules:
    def on_unlock(self, vehicle, user):
        # Optional hook executed when vehicle is unlocked
        pass

    def on_end_rental(self, rental):
        # Optional hook executed when rental is ended
        pass

    def validate_movement(self, vehicle):
        # Optional hook executed to validate vehicle movement
        return True

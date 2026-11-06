class HelmetRequiredError(Exception):
    # Raised when helmet is not present for Milan rules
    pass

class RestrictedZoneError(Exception):
    # Raised when entering restricted zone in Rome
    pass
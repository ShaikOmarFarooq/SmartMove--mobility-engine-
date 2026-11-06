import time

class PricingEngine:
    PRICE_PER_MIN = 0.25

    @staticmethod
    def calculate(rental):
        duration_min = (rental.end_time - rental.start_time) / 60
        return round(duration_min * PricingEngine.PRICE_PER_MIN, 2)

from rules.base import CityRules

class LondonRules(CityRules):
    def on_end_rental(self, rental):
        rental.cost += 5.0  # congestion charge

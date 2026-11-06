import time

class Rental:
    def __init__(self, rental_id, user_id, vehicle_id):
        self.id = rental_id
        self.user_id = user_id
        self.vehicle_id = vehicle_id
        self.start_time = time.time()
        self.end_time = None
        self.cost = 0.0
        self.active = True

    def end(self):
        self.end_time = time.time()
        self.active = False

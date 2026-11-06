import json
import os
import tempfile

from domain.vehicle import Vehicle
from domain.user import User
from domain.enums import VehicleType, City, VehicleState

VEHICLES_FILE = "data/vehicles.json"
USERS_FILE = "data/users.json"


def _atomic_write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        encoding="utf-8",
        dir=os.path.dirname(path)
    ) as tmp:
        json.dump(data, tmp, indent=2)
        temp_name = tmp.name

    os.replace(temp_name, path)


def vehicles_exist():
    return os.path.exists(VEHICLES_FILE)


def users_exist():
    return os.path.exists(USERS_FILE)


def save_vehicles(vehicles):
    data = []
    for vehicle in vehicles.values():
        data.append({
            "id": vehicle.id,
            "type": vehicle.type.value,
            "city": vehicle.city.value,
            "state": vehicle.state.value,
            "gps": list(vehicle.gps),
            "battery": vehicle.battery,
            "temperature": vehicle.temperature,
            "helmet_present": getattr(vehicle, "helmet_present", True)
        })

    _atomic_write_json(VEHICLES_FILE, data)


def load_vehicles():
    with open(VEHICLES_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    vehicles = {}

    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue

            vehicle = Vehicle(
                vehicle_id=item["id"],
                vtype=VehicleType(item["type"]),
                city=City(item["city"])
            )
            vehicle.state = VehicleState(item.get("state", VehicleState.AVAILABLE.value))
            vehicle.gps = tuple(item.get("gps", [0.0, 0.0]))
            vehicle.battery = item.get("battery", 100)
            vehicle.temperature = item.get("temperature", 25)
            vehicle.helmet_present = item.get("helmet_present", True)

            vehicles[vehicle.id] = vehicle

        return vehicles

    raise ValueError("Unsupported vehicles.json format")


def save_users(users):
    data = []
    for user in users.values():
        data.append({
            "id": user.id,
            "name": user.name
        })

    _atomic_write_json(USERS_FILE, data)


def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    users = {}

    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue

            user = User(user_id=item["id"], name=item["name"])
            users[user.id] = user

        return users

    raise ValueError("Unsupported users.json format")
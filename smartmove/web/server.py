"""
SmartMove web frontend server.

A small, dependency-free HTTP server (Python standard library only) that
exposes the SmartMove controller as a JSON API and serves the single-page
frontend in web/static/index.html.

Run from the repository root (so the relative data/ paths resolve):

    python smartmove/web/server.py                # browse data, manual rentals
    python smartmove/web/server.py --simulate     # also run telemetry/rental simulation
    python smartmove/web/server.py --port 9000

Then open http://localhost:8000
"""
import argparse
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# Make `core`, `domain`, ... importable no matter where the script is started.
SMARTMOVE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SMARTMOVE_DIR not in sys.path:
    sys.path.insert(0, SMARTMOVE_DIR)

from core.controller import SmartMoveCentralController  # noqa: E402
from core.exceptions import SmartMoveError, IntegrityCheckError  # noqa: E402
from core.pricing import PricingEngine  # noqa: E402
from domain.enums import VehicleState  # noqa: E402
from simulation.simulation_engine import SimulationEngine  # noqa: E402
from rules.exceptions import HelmetRequiredError, RestrictedZoneError  # noqa: E402

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


class SmartMoveApp:
    """Holds the controller/simulation and implements the API operations."""

    def __init__(self):
        self.controller = SmartMoveCentralController()
        self.simulation = SimulationEngine(self.controller, telemetry_worker_count=4)
        self.simulation.bootstrap()
        self.simulation_running = False

    # ---------- serialisation helpers ----------
    @staticmethod
    def vehicle_dict(v):
        return {
            "id": v.id,
            "type": v.type.value,
            "city": v.city.value,
            "state": v.state.value,
            "gps": [round(v.gps[0], 5), round(v.gps[1], 5)],
            "battery": round(v.battery, 1),
            "temperature": round(v.temperature, 1),
            "helmet_present": bool(getattr(v, "helmet_present", True)),
        }

    def rental_dict(self, rental):
        now = time.time()
        end = rental.end_time or now
        minutes = (end - rental.start_time) / 60
        user = self.controller.users.get(rental.user_id)
        vehicle = self.controller.vehicles.get(rental.vehicle_id)
        return {
            "id": rental.id,
            "user_id": rental.user_id,
            "user_name": user.name if user else None,
            "vehicle_id": rental.vehicle_id,
            "city": vehicle.city.value if vehicle else None,
            "start_time": rental.start_time,
            "duration_seconds": round(end - rental.start_time),
            "running_cost": round(minutes * PricingEngine.PRICE_PER_MIN, 2),
            "active": rental.active,
            "cost": rental.cost,
        }

    # ---------- queries ----------
    def summary(self):
        vehicles = list(self.controller.vehicles.values())
        by_state, by_city, by_type = {}, {}, {}
        low_battery = 0
        battery_sum = 0.0
        for v in vehicles:
            by_state[v.state.value] = by_state.get(v.state.value, 0) + 1
            by_city[v.city.value] = by_city.get(v.city.value, 0) + 1
            by_type[v.type.value] = by_type.get(v.type.value, 0) + 1
            battery_sum += v.battery
            if v.battery < 15:
                low_battery += 1
        total = len(vehicles)
        return {
            "total_vehicles": total,
            "total_users": len(self.controller.users),
            "active_rentals": len(self.controller.active_rentals),
            "avg_battery": round(battery_sum / total, 1) if total else 0,
            "low_battery": low_battery,
            "by_state": by_state,
            "by_city": by_city,
            "by_type": by_type,
            "simulation_running": self.simulation_running,
        }

    def list_vehicles(self, q):
        city = q.get("city", [""])[0]
        state = q.get("state", [""])[0]
        vtype = q.get("type", [""])[0]
        search = q.get("q", [""])[0].lower()
        limit = min(int(q.get("limit", ["50"])[0]), 200)
        offset = max(int(q.get("offset", ["0"])[0]), 0)

        matches = []
        for v in self.controller.vehicles.values():
            if city and v.city.value != city:
                continue
            if state and v.state.value != state:
                continue
            if vtype and v.type.value != vtype:
                continue
            if search and search not in v.id.lower():
                continue
            matches.append(v)
        page = matches[offset:offset + limit]
        return {
            "total": len(matches),
            "offset": offset,
            "limit": limit,
            "items": [self.vehicle_dict(v) for v in page],
        }

    def get_vehicle(self, vehicle_id):
        v = self.controller.vehicles.get(vehicle_id)
        if not v:
            raise ApiError(404, "Vehicle not found")
        data = self.vehicle_dict(v)
        rental = self.controller.active_rentals.get(vehicle_id)
        data["active_rental"] = self.rental_dict(rental) if rental else None
        return data

    def list_users(self, q):
        search = q.get("q", [""])[0].lower()
        limit = min(int(q.get("limit", ["20"])[0]), 100)
        out = []
        for u in self.controller.users.values():
            if search and search not in u.name.lower() and search not in u.id.lower():
                continue
            out.append({"id": u.id, "name": u.name})
            if len(out) >= limit:
                break
        return {"items": out}

    def list_rentals(self):
        for _ in range(3):  # dict may change while simulation runs
            try:
                rentals = list(self.controller.active_rentals.values())
                break
            except RuntimeError:
                rentals = []
        items = [self.rental_dict(r) for r in rentals]
        items.sort(key=lambda r: r["start_time"], reverse=True)
        return {"items": items}

    def audit_tail(self, q):
        limit = min(int(q.get("limit", ["50"])[0]), 500)
        entity = q.get("entity", [""])[0]
        entries = self.controller.audit._read_entries()
        if entity:
            entries = [e for e in entries if entity in e["entity_id"]]
        total = len(entries)
        return {"total": total, "items": list(reversed(entries[-limit:]))}

    def audit_verify(self):
        try:
            self.controller.audit.verify_integrity()
            return {"ok": True, "message": "Audit log integrity verified."}
        except IntegrityCheckError as exc:
            return {"ok": False, "message": str(exc)}

    # ---------- commands ----------
    def start_rental(self, body):
        user_id, vehicle_id = body.get("user_id"), body.get("vehicle_id")
        user = self.controller.users.get(user_id)
        vehicle = self.controller.vehicles.get(vehicle_id)
        if not user:
            raise ApiError(404, "User not found")
        if not vehicle:
            raise ApiError(404, "Vehicle not found")
        rental = self.controller.start_rental(user, vehicle)
        return self.rental_dict(rental)

    def end_rental(self, body):
        vehicle = self.controller.vehicles.get(body.get("vehicle_id"))
        if not vehicle:
            raise ApiError(404, "Vehicle not found")
        rental = self.controller.end_rental(vehicle)
        return self.rental_dict(rental)

    def set_simulation(self, running):
        if running and not self.simulation_running:
            self.simulation.start()
            self.simulation_running = True
        elif not running and self.simulation_running:
            self.simulation.stop()
            self.simulation_running = False
        return {"simulation_running": self.simulation_running}


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # keep the console quiet
            pass

        def _send_json(self, status, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _send_index(self):
            with open(os.path.join(STATIC_DIR, "index.html"), "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _handle(self, method):
            parsed = urlparse(self.path)
            path, q = parsed.path.rstrip("/") or "/", parse_qs(parsed.query)
            try:
                if method == "GET":
                    if path == "/":
                        return self._send_index()
                    if path == "/api/summary":
                        return self._send_json(200, app.summary())
                    if path == "/api/vehicles":
                        return self._send_json(200, app.list_vehicles(q))
                    if path.startswith("/api/vehicles/"):
                        return self._send_json(200, app.get_vehicle(path.split("/", 3)[3]))
                    if path == "/api/users":
                        return self._send_json(200, app.list_users(q))
                    if path == "/api/rentals":
                        return self._send_json(200, app.list_rentals())
                    if path == "/api/audit":
                        return self._send_json(200, app.audit_tail(q))
                    if path == "/api/audit/verify":
                        return self._send_json(200, app.audit_verify())
                else:
                    length = int(self.headers.get("Content-Length") or 0)
                    raw = self.rfile.read(length) if length else b"{}"
                    body = json.loads(raw or b"{}")
                    if path == "/api/rentals/start":
                        return self._send_json(201, app.start_rental(body))
                    if path == "/api/rentals/end":
                        return self._send_json(200, app.end_rental(body))
                    if path == "/api/simulation":
                        return self._send_json(200, app.set_simulation(bool(body.get("running"))))
                raise ApiError(404, "Not found")
            except ApiError as exc:
                self._send_json(exc.status, {"error": exc.message})
            except (SmartMoveError, HelmetRequiredError, RestrictedZoneError) as exc:
                self._send_json(409, {"error": str(exc)})
            except (ValueError, json.JSONDecodeError):
                self._send_json(400, {"error": "Bad request"})
            except Exception as exc:  # pragma: no cover
                self._send_json(500, {"error": f"Server error: {exc}"})

        def do_GET(self):
            self._handle("GET")

        def do_POST(self):
            self._handle("POST")

    return Handler


def main():
    parser = argparse.ArgumentParser(description="SmartMove web frontend")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--simulate", action="store_true",
                        help="start telemetry and rental simulation immediately")
    args = parser.parse_args()

    app = SmartMoveApp()
    if args.simulate:
        app.set_simulation(True)

    server = ThreadingHTTPServer((args.host, args.port), make_handler(app))
    print(f"SmartMove frontend running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        app.set_simulation(False)
        server.server_close()


if __name__ == "__main__":
    main()

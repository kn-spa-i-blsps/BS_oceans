#!/usr/bin/env python3
import math
import os
import sys
import time

try:
    from pymavlink import mavutil
except ImportError:
    print("pymavlink not available. Install it in your environment to use ArduSub control.")
    sys.exit(1)


FLEET_SIZE = int(os.getenv("BS_FLEET_SIZE", "1"))
VEHICLE_PREFIX = os.getenv("BS_VEHICLE_PREFIX", "bluerov")
WAYPOINT_FILE = os.getenv("BS_WP_FILE", "")
DEPTH_TARGET = float(os.getenv("BS_DEPTH_TARGET", "1.0"))
WAYPOINT_RADIUS = float(os.getenv("BS_WP_RADIUS", "1.0"))
UPDATE_HZ = float(os.getenv("BS_CTRL_HZ", "2.0"))

# Comma-separated list of endpoints; default assumes first ArduSub SITL
ENDPOINTS = os.getenv("BS_MAVLINK_ENDPOINTS", "")
MAVLINK_BASE = int(os.getenv("BS_MAVLINK_BASE", "14550"))


def load_waypoints(path):
    shared = []
    per_vehicle = {}
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) in (2, 3):
                x = float(parts[0])
                y = float(parts[1])
                z = float(parts[2]) if len(parts) == 3 else None
                shared.append((x, y, z))
            elif len(parts) in (3, 4):
                name = parts[0]
                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3]) if len(parts) == 4 else None
                per_vehicle.setdefault(name, []).append((x, y, z))
    return shared, per_vehicle


def enu_to_ned(x, y, z):
    # ENU: x east, y north, z up
    # NED: x north, y east, z down
    return y, x, -z


def set_guided_mode(conn):
    conn.set_mode("GUIDED")


def arm(conn):
    conn.arducopter_arm()
    conn.motors_armed_wait()


def send_position_target(conn, x_ned, y_ned, z_ned):
    conn.mav.set_position_target_local_ned_send(
        int(time.time() * 1000),
        conn.target_system,
        conn.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        0b0000111111111000,  # position only
        x_ned,
        y_ned,
        z_ned,
        0, 0, 0,
        0, 0, 0,
        0, 0,
    )


def wait_heartbeat(conn):
    conn.wait_heartbeat(timeout=10)


def connect_endpoint(endpoint):
    conn = mavutil.mavlink_connection(endpoint, autoreconnect=True)
    wait_heartbeat(conn)
    set_guided_mode(conn)
    arm(conn)
    return conn


def main():
    if not WAYPOINT_FILE:
        print("BS_WP_FILE is required for ArduSub control.")
        return 1

    shared_wps, per_vehicle_wps = load_waypoints(WAYPOINT_FILE)
    if not shared_wps and not per_vehicle_wps:
        print("No waypoints found in file.")
        return 1

    endpoints = [e.strip() for e in ENDPOINTS.split(",") if e.strip()]
    if len(endpoints) < FLEET_SIZE:
        endpoints = [
            f"udp:127.0.0.1:{MAVLINK_BASE + i * 10}" for i in range(FLEET_SIZE)
        ]

    vehicles = []
    for i in range(FLEET_SIZE):
        name = f"{VEHICLE_PREFIX}{i + 1}"
        wps = per_vehicle_wps.get(name) or shared_wps
        conn = connect_endpoint(endpoints[i])
        vehicles.append({"name": name, "conn": conn, "wps": wps, "idx": 0})

    period = 1.0 / UPDATE_HZ
    while True:
        for v in vehicles:
            wp = v["wps"][v["idx"]]
            x, y = wp[0], wp[1]
            z = wp[2] if len(wp) >= 3 and wp[2] is not None else DEPTH_TARGET
            x_ned, y_ned, z_ned = enu_to_ned(x, y, z)
            send_position_target(v["conn"], x_ned, y_ned, z_ned)

            # Check distance using last known position if available
            msg = v["conn"].recv_match(type="LOCAL_POSITION_NED", blocking=False)
            if msg:
                dx = msg.x - x_ned
                dy = msg.y - y_ned
                dz = msg.z - z_ned
                if math.sqrt(dx * dx + dy * dy + dz * dz) < WAYPOINT_RADIUS:
                    v["idx"] = (v["idx"] + 1) % len(v["wps"])
        time.sleep(period)


if __name__ == "__main__":
    raise SystemExit(main())

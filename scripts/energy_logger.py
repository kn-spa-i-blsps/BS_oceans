#!/usr/bin/env python3
import csv
import math
import os
import signal
import sys
import time

from gz_pose_stream import PoseStream

WORLD_NAME = os.getenv("BS_WORLD_NAME", "buoyant_tethys")
FLEET_SIZE = int(os.getenv("BS_FLEET_SIZE", "3"))
VEHICLE_PREFIX = os.getenv("BS_VEHICLE_PREFIX", "bluerov")
OUTPUT_CSV = os.getenv("BS_ENERGY_CSV", "")
EXPERIMENT_ID = os.getenv("BS_EXPERIMENT_ID", "")

DRAG_RHO = float(os.getenv("BS_DRAG_RHO", "1000.0"))
DRAG_CD = float(os.getenv("BS_DRAG_CD", "0.8"))
DRAG_AREA = float(os.getenv("BS_DRAG_AREA", "0.1"))
PROP_EFF = float(os.getenv("BS_PROP_EFF", "0.6"))
HOTEL_W = float(os.getenv("BS_HOTEL_W", "15.0"))

POSE_TOPIC = f"/world/{WORLD_NAME}/pose/info"


def main():
    pose_stream = PoseStream(POSE_TOPIC)
    pose_stream.start()

    running = True

    def _stop(*_args):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    last_pose = {}
    last_time = {}
    energy = {f"{VEHICLE_PREFIX}{i + 1}": 0.0 for i in range(FLEET_SIZE)}

    while running:
        now = time.time()
        poses = pose_stream.get_all()
        for name in list(energy.keys()):
            pose = poses.get(name)
            if not pose:
                continue
            if name in last_pose:
                dt = now - last_time[name]
                if dt > 0:
                    dx = pose["x"] - last_pose[name]["x"]
                    dy = pose["y"] - last_pose[name]["y"]
                    dz = pose["z"] - last_pose[name]["z"]
                    v = math.sqrt(dx * dx + dy * dy + dz * dz) / dt
                    drag_force = 0.5 * DRAG_RHO * DRAG_CD * DRAG_AREA * v * v
                    power = drag_force * v / max(PROP_EFF, 1e-3) + HOTEL_W
                    energy[name] += power * dt
            last_pose[name] = pose
            last_time[name] = now
        time.sleep(0.5)

    pose_stream.stop()

    output_csv = OUTPUT_CSV
    if not output_csv:
        ts = time.strftime("%Y%m%d_%H%M%S")
        output_csv = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "data",
                "experiments",
                f"energy_{ts}.csv",
            )
        )

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["experiment_id", "vehicle", "energy"])
        for name, value in energy.items():
            writer.writerow([EXPERIMENT_ID, name, f"{value:.6f}"])


if __name__ == "__main__":
    sys.exit(main())

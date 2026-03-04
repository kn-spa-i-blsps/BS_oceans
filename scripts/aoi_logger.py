#!/usr/bin/env python3
import csv
import math
import os
import random
import signal
import sys
import time

from gz_pose_stream import PoseStream


WORLD_NAME = os.getenv("BS_WORLD_NAME", "buoyant_tethys")
FLEET_SIZE = int(os.getenv("BS_FLEET_SIZE", "3"))
RMSE = float(os.getenv("BS_LOC_RMSE", "1.0"))
STRATEGY = os.getenv("BS_STRATEGY", "lawnmower")
SEED = int(os.getenv("BS_SEED", "42")) + 202
VEHICLE_PREFIX = os.getenv("BS_VEHICLE_PREFIX", "bluerov")

AREA_MIN_X = float(os.getenv("BS_AREA_MIN_X", "0.0"))
AREA_MAX_X = float(os.getenv("BS_AREA_MAX_X", "20.0"))
AREA_MIN_Y = float(os.getenv("BS_AREA_MIN_Y", "0.0"))
AREA_MAX_Y = float(os.getenv("BS_AREA_MAX_Y", "20.0"))
CELL_SIZE = float(os.getenv("BS_CELL_SIZE", "1.0"))

POSE_TOPIC = f"/world/{WORLD_NAME}/pose/info"
OUTPUT_CSV = os.getenv("BS_OUTPUT_CSV", "")
EXPERIMENT_ID = os.getenv("BS_EXPERIMENT_ID", "")


def _p95(values):
    if not values:
        return 0.0
    values = sorted(values)
    idx = int(math.ceil(0.95 * len(values))) - 1
    idx = max(0, min(idx, len(values) - 1))
    return values[idx]


def main():
    random.seed(SEED)
    sigma = RMSE / math.sqrt(3.0)

    nx = int(math.ceil((AREA_MAX_X - AREA_MIN_X) / CELL_SIZE))
    ny = int(math.ceil((AREA_MAX_Y - AREA_MIN_Y) / CELL_SIZE))
    last_visit = [[None for _ in range(ny)] for _ in range(nx)]
    ivt_samples = []

    pose_stream = PoseStream(POSE_TOPIC)
    pose_stream.start()
    start_time = time.time()

    running = True

    def _stop(*_args):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    while running:
        now = time.time()
        poses = pose_stream.get_all()
        for i in range(FLEET_SIZE):
            name = f"{VEHICLE_PREFIX}{i + 1}"
            pose = poses.get(name)
            if not pose:
                continue
            x = pose["x"] + random.gauss(0.0, sigma)
            y = pose["y"] + random.gauss(0.0, sigma)
            ix = int((x - AREA_MIN_X) / CELL_SIZE)
            iy = int((y - AREA_MIN_Y) / CELL_SIZE)
            if 0 <= ix < nx and 0 <= iy < ny:
                last = last_visit[ix][iy]
                if last is not None:
                    ivt_samples.append(now - last)
                last_visit[ix][iy] = now
        time.sleep(0.5)

    end_time = time.time()
    duration = end_time - start_time
    aoi_values = []
    for ix in range(nx):
        for iy in range(ny):
            last = last_visit[ix][iy]
            if last is None:
                aoi = duration
            else:
                aoi = end_time - last
            aoi_values.append(aoi)

    mean_aoi = sum(aoi_values) / len(aoi_values) if aoi_values else 0.0
    max_aoi = max(aoi_values) if aoi_values else 0.0
    p95_aoi = _p95(aoi_values)

    mean_ivt = sum(ivt_samples) / len(ivt_samples) if ivt_samples else 0.0
    max_ivt = max(ivt_samples) if ivt_samples else 0.0

    output_csv = OUTPUT_CSV
    if not output_csv:
        ts = time.strftime("%Y%m%d_%H%M%S")
        output_csv = os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            "experiments",
            f"aoi_{ts}.csv",
        )
        output_csv = os.path.abspath(output_csv)

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "experiment_id",
                "mean_aoi",
                "max_aoi",
                "p95_aoi",
                "mean_ivt",
                "max_ivt",
                "mission_duration",
                "fleet_size",
                "localization_rmse",
                "trajectory_strategy",
            ]
        )
        writer.writerow(
            [
                EXPERIMENT_ID,
                f"{mean_aoi:.6f}",
                f"{max_aoi:.6f}",
                f"{p95_aoi:.6f}",
                f"{mean_ivt:.6f}",
                f"{max_ivt:.6f}",
                f"{duration:.6f}",
                FLEET_SIZE,
                f"{RMSE:.3f}",
                STRATEGY,
            ]
        )

    pose_stream.stop()


if __name__ == "__main__":
    sys.exit(main())

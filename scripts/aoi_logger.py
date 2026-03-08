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


def _gini(array):
    """ Counts Gini Coefficient (How fair is na algorithm for every cell)
        for array with (0 = Ideal Equality, 1 = Maximum Inequality)"""
    if not array:
        return 0.0
    array = sorted(array)
    n = len(array)
    total = sum(array)
    if total == 0:
        return 0.0

    coef_ = 2.0 / n
    const_ = (n + 1.0) / n
    weighted_sum = sum([(i + 1) * yi for i, yi in enumerate(array)])
    return (coef_ * weighted_sum) / total - const_


def main():
    random.seed(SEED)
    sigma = RMSE / math.sqrt(3.0)

    # Counting number of cells
    nx = int(math.ceil((AREA_MAX_X - AREA_MIN_X) / CELL_SIZE))
    ny = int(math.ceil((AREA_MAX_Y - AREA_MIN_Y) / CELL_SIZE))

    last_visit = [[None for _ in range(ny)] for _ in range(nx)]
    last_ivt = [[None for _ in range(ny)] for _ in range(nx)]
    ivt_samples = []
    grid_history = {}

    # For Gini Coefficient and TTC
    visit_counts = [[0 for _ in range(ny)] for _ in range(nx)]
    unvisited_cells = nx * ny
    ttc = None

    pose_stream = PoseStream(POSE_TOPIC)
    pose_stream.start()
    start_time = time.time()

    running = True

    def _stop(*_args):
        nonlocal running
        running = False

    # Saving state from all cells
    def _take_snapshot(current_time):
        elapsed_time = current_time - start_time
        current_aoi_grid = []
        current_ivt_grid = []

        for ix in range(nx):
            aoi_row = []
            ivt_row = []
            for iy in range(ny):
                last = last_visit[ix][iy]
                if last is None:
                    aoi = elapsed_time
                else:
                    aoi = current_time - last

                aoi_row.append(aoi)
                ivt_row.append(last_ivt[ix][iy])

            current_aoi_grid.append(aoi_row)
            current_ivt_grid.append(ivt_row)

        grid_history[elapsed_time] = {
            "aoi": current_aoi_grid,
            "ivt": current_ivt_grid
        }

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    # Main loop for AoI
    while running:
        now = time.time()
        poses = pose_stream.get_all()
        for i in range(FLEET_SIZE):
            name = f"{VEHICLE_PREFIX}{i + 1}"
            pose = poses.get(name)
            if not pose:
                continue
            # Getting poses and converting then for cell number oon the grid
            x = pose["x"] + random.gauss(0.0, sigma)
            y = pose["y"] + random.gauss(0.0, sigma)
            ix = int((x - AREA_MIN_X) / CELL_SIZE)
            iy = int((y - AREA_MIN_Y) / CELL_SIZE)
            # Adding data
            if 0 <= ix < nx and 0 <= iy < ny:
                last = last_visit[ix][iy]

                if last is None:
                    unvisited_cells -= 1
                    visit_counts[ix][iy] += 1
                    # Checking if we covered last cell
                    if unvisited_cells == 0 and ttc is None:
                        ttc = now - start_time
                else:
                    ivt = now - last
                    # We have to be careful with long duration in one cell,
                    # to not mess the Gini Coefficient
                    # TODO (maybe to consider only counting when entering new cell)
                    if ivt > 3.0:
                        ivt_samples.append(ivt)
                        last_ivt[ix][iy] = ivt
                        visit_counts[ix][iy] += 1
                last_visit[ix][iy] = now
        time.sleep(0.5)
        # TODO check the best frequence for snaphots
        _take_snapshot(now)

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

    final_ttc = ttc if ttc is not None else duration

    flat_visits = []
    for ix in range(nx):
        for iy in range(ny):
            flat_visits.append(visit_counts[ix][iy])
    gini_index = _gini(flat_visits)

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
                "ttc",
                "gini_index",
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
                f"{final_ttc:.6f}",
                f"{gini_index:.6f}",
                f"{duration:.6f}",
                FLEET_SIZE,
                f"{RMSE:.3f}",
                STRATEGY,
            ]
        )

        history_csv = output_csv.replace(".csv", "_history.csv")

        # Writing whole history of an experiment to CSV file for further analysis
        with open(history_csv, "w", newline="") as f_hist:
            hist_writer = csv.writer(f_hist)
            hist_writer.writerow(["time_sec", "cell_x", "cell_y", "aoi", "last_ivt"])

            for t, grids in grid_history.items():
                aoi_grid = grids["aoi"]
                ivt_grid = grids["ivt"]

                for ix in range(nx):
                    for iy in range(ny):
                        val_aoi = aoi_grid[ix][iy]
                        val_ivt = ivt_grid[ix][iy]

                        # TODO is it good for analysis to have blanks
                        str_ivt = f"{val_ivt:.4f}" if val_ivt is not None else ""

                        hist_writer.writerow([
                            f"{t:.1f}",
                            ix,
                            iy,
                            f"{val_aoi:.4f}",
                            str_ivt
                        ])

    pose_stream.stop()


if __name__ == "__main__":
    sys.exit(main())

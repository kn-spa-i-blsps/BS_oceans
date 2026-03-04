#!/usr/bin/env python3
import os
import signal
import subprocess
import sys
import time

WORLD_NAME = os.getenv("BS_WORLD_NAME", "buoyant_tethys")
FLEET_SIZE = int(os.getenv("BS_FLEET_SIZE", "3"))
VEHICLE_PREFIX = os.getenv("BS_VEHICLE_PREFIX", "bluerov")

CURRENT_X = float(os.getenv("BS_CURRENT_X", "0.0"))
CURRENT_Y = float(os.getenv("BS_CURRENT_Y", "0.0"))
CURRENT_Z = float(os.getenv("BS_CURRENT_Z", "0.0"))
CURRENT_K = float(os.getenv("BS_CURRENT_K", "25.0"))


def publish_wrench(entity_name, fx, fy, fz):
    payload = (
        f"entity: {{name: '{entity_name}', type: MODEL}}, "
        f"wrench: {{force: {{x: {fx:.6f}, y: {fy:.6f}, z: {fz:.6f}}}}}"
    )
    subprocess.run(
        [
            "gz",
            "topic",
            "-t",
            f"/world/{WORLD_NAME}/wrench/persistent",
            "-m",
            "gz.msgs.EntityWrench",
            "-p",
            payload,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def clear_wrench(entity_name):
    payload = f"name: '{entity_name}', type: MODEL"
    subprocess.run(
        [
            "gz",
            "topic",
            "-t",
            f"/world/{WORLD_NAME}/wrench/clear",
            "-m",
            "gz.msgs.Entity",
            "-p",
            payload,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def main():
    fx = CURRENT_K * CURRENT_X
    fy = CURRENT_K * CURRENT_Y
    fz = CURRENT_K * CURRENT_Z

    for i in range(FLEET_SIZE):
        name = f"{VEHICLE_PREFIX}{i + 1}"
        publish_wrench(name, fx, fy, fz)

    running = True

    def _stop(*_args):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    while running:
        time.sleep(1.0)

    for i in range(FLEET_SIZE):
        name = f"{VEHICLE_PREFIX}{i + 1}"
        clear_wrench(name)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
import math
import os
import random
import signal
import subprocess
import sys
import time

from gz_pose_stream import PoseStream


WORLD_NAME = os.getenv("BS_WORLD_NAME", "buoyant_tethys")
FLEET_SIZE = int(os.getenv("BS_FLEET_SIZE", "3"))
RMSE = float(os.getenv("BS_LOC_RMSE", "1.0"))
SEED = int(os.getenv("BS_SEED", "42")) + 101
UPDATE_HZ = float(os.getenv("BS_LOC_HZ", "2.0"))
VEHICLE_PREFIX = os.getenv("BS_VEHICLE_PREFIX", "bluerov")

POSE_TOPIC = f"/world/{WORLD_NAME}/pose/info"
EST_TOPIC_PREFIX = os.getenv("BS_EST_POSE_PREFIX", "/blue_spark/pose_estimate")


def publish_pose(topic, pose):
    payload = (
        "position { x: %.6f y: %.6f z: %.6f } "
        "orientation { x: %.6f y: %.6f z: %.6f w: %.6f }"
        % (
            pose["x"],
            pose["y"],
            pose["z"],
            pose["qx"],
            pose["qy"],
            pose["qz"],
            pose["qw"],
        )
    )
    subprocess.run(
        ["gz", "topic", "-t", topic, "-m", "gz.msgs.Pose", "-p", payload],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def main():
    random.seed(SEED)
    sigma = RMSE / math.sqrt(3.0)
    pose_stream = PoseStream(POSE_TOPIC)
    pose_stream.start()

    running = True

    def _stop(*_args):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    period = 1.0 / UPDATE_HZ
    while running:
        poses = pose_stream.get_all()
        for i in range(FLEET_SIZE):
            name = f"{VEHICLE_PREFIX}{i + 1}"
            pose = poses.get(name)
            if not pose:
                continue
            noisy = dict(pose)
            noisy["x"] += random.gauss(0.0, sigma)
            noisy["y"] += random.gauss(0.0, sigma)
            noisy["z"] += random.gauss(0.0, sigma)
            topic = f"{EST_TOPIC_PREFIX}/{name}"
            publish_pose(topic, noisy)
        time.sleep(period)

    pose_stream.stop()


if __name__ == "__main__":
    sys.exit(main())

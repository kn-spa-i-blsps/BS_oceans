#!/usr/bin/env python3
import subprocess
import threading
import time


def _parse_pose_message(lines):
    poses = {}
    in_pose = False
    block = None
    current = {}

    def _commit_pose():
        name = current.get("name")
        if name and all(k in current for k in ("x", "y", "z", "qx", "qy", "qz", "qw")):
            poses[name] = {
                "x": current["x"],
                "y": current["y"],
                "z": current["z"],
                "qx": current["qx"],
                "qy": current["qy"],
                "qz": current["qz"],
                "qw": current["qw"],
            }

    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("pose {"):
            in_pose = True
            block = None
            current = {}
            continue
        if not in_pose:
            continue
        if s.startswith("name:"):
            current["name"] = s.split(":", 1)[1].strip().strip('"')
            continue
        if s.startswith("position {"):
            block = "position"
            continue
        if s.startswith("orientation {"):
            block = "orientation"
            continue
        if s == "}":
            if block is not None:
                block = None
            else:
                _commit_pose()
                in_pose = False
            continue
        if block == "position":
            if s.startswith("x:"):
                current["x"] = float(s.split(":", 1)[1])
            elif s.startswith("y:"):
                current["y"] = float(s.split(":", 1)[1])
            elif s.startswith("z:"):
                current["z"] = float(s.split(":", 1)[1])
            continue
        if block == "orientation":
            if s.startswith("x:"):
                current["qx"] = float(s.split(":", 1)[1])
            elif s.startswith("y:"):
                current["qy"] = float(s.split(":", 1)[1])
            elif s.startswith("z:"):
                current["qz"] = float(s.split(":", 1)[1])
            elif s.startswith("w:"):
                current["qw"] = float(s.split(":", 1)[1])
            continue

    return poses


class PoseStream:
    def __init__(self, topic):
        self.topic = topic
        self._poses = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._proc = None

    def start(self):
        if self._thread:
            return
        self._proc = subprocess.Popen(
            ["gz", "topic", "-e", "-t", self.topic],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._proc:
            self._proc.terminate()
        if self._thread:
            self._thread.join(timeout=1)

    def _reader_loop(self):
        buffer = []
        last_flush = time.time()
        while not self._stop.is_set() and self._proc and self._proc.stdout:
            line = self._proc.stdout.readline()
            if not line:
                time.sleep(0.05)
                continue
            if line.strip() == "":
                if buffer:
                    poses = _parse_pose_message(buffer)
                    if poses:
                        with self._lock:
                            self._poses.update(poses)
                    buffer = []
                    last_flush = time.time()
                continue
            buffer.append(line)
            if time.time() - last_flush > 0.5 and buffer:
                poses = _parse_pose_message(buffer)
                if poses:
                    with self._lock:
                        self._poses.update(poses)
                buffer = []
                last_flush = time.time()

    def get(self, name):
        with self._lock:
            return self._poses.get(name)

    def get_all(self):
        with self._lock:
            return dict(self._poses)


__all__ = ["PoseStream"]

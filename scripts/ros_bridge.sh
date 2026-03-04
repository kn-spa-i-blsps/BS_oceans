#!/usr/bin/env bash
set -euo pipefail

ROS_DISTRO="${BS_ROS_DISTRO:-jazzy}"
FLEET_SIZE="${BS_FLEET_SIZE:-3}"
VEHICLE_PREFIX="${BS_VEHICLE_PREFIX:-bluerov}"

if [[ -f "/opt/ros/$ROS_DISTRO/setup.bash" ]]; then
  # shellcheck disable=SC1090
  set +u
  source "/opt/ros/$ROS_DISTRO/setup.bash"
  set -u
else
  echo "ROS 2 setup not found at /opt/ros/$ROS_DISTRO" >&2
  exit 1
fi

args=()
for i in $(seq 1 "$FLEET_SIZE"); do
  name="${VEHICLE_PREFIX}${i}"
  args+=("/model/${name}/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry")
  for thr in 1 2 3 4 5 6; do
    args+=("/model/${name}/joint/thruster${thr}_joint/cmd_thrust@std_msgs/msg/Float64[gz.msgs.Double")
  done
done

ros2 run ros_gz_bridge parameter_bridge "${args[@]}"

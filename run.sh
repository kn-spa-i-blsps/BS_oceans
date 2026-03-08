#!/usr/bin/env bash

# set environment configuration variables automatically
set -a 
source ./config.env
set +a

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export GZ_SIM_RESOURCE_PATH="$PROJECT_ROOT/models:$PROJECT_ROOT/worlds"
WORLD_PATH="${BS_WORLD_PATH:-$PROJECT_ROOT/worlds/swarm.sdf}"
if [[ -n "${BS_ARDUPILOT_PLUGIN_PATH:-}" ]]; then
  export GZ_SIM_SYSTEM_PLUGIN_PATH="$BS_ARDUPILOT_PLUGIN_PATH:${GZ_SIM_SYSTEM_PLUGIN_PATH:-}"
fi

cleanup() {
  kill "$gz_pid" "$wp_pid" "$loc_pid" "$aoi_pid" "$cur_pid" "$eng_pid" "${sitl_pid:-}" "${ros_pid:-}" 2>/dev/null || true
  wait "$gz_pid" "$wp_pid" "$loc_pid" "$aoi_pid" "$cur_pid" "$eng_pid" "${sitl_pid:-}" "${ros_pid:-}" 2>/dev/null || true
}
trap cleanup INT TERM

gz sim -v4 "$WORLD_PATH" &
gz_pid=$!

"$PROJECT_ROOT/scripts/ardusub_sitl.sh" &
sitl_pid=$!

"$PROJECT_ROOT/scripts/ros_bridge.sh" &
ros_pid=$!

python3 "$PROJECT_ROOT/scripts/localization_noise.py" &
loc_pid=$!
python3 "$PROJECT_ROOT/scripts/aoi_logger.py" &
aoi_pid=$!
python3 "$PROJECT_ROOT/scripts/current_field.py" &
cur_pid=$!
python3 "$PROJECT_ROOT/scripts/energy_logger.py" &
eng_pid=$!
python3 "$PROJECT_ROOT/scripts/ardusub_waypoint_runner.py" &
wp_pid=$!

wait -n "$gz_pid" "$wp_pid" "$loc_pid" "$aoi_pid" "$cur_pid" "$eng_pid"
cleanup

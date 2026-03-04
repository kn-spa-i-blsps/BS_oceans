#!/usr/bin/env bash
set -euo pipefail

ARDUPILOT_HOME="${BS_ARDUPILOT_HOME:-$HOME/BlueSpark-software/ardupilot}"
FRAME="${BS_ARDU_FRAME:-gazebo-bluerov2}"
MODEL="${BS_ARDU_MODEL:-JSON}"
FLEET_SIZE="${BS_FLEET_SIZE:-3}"
PARAM_FILE="${BS_ARDU_PARAMS:-$ARDUPILOT_HOME/Tools/Frame_params/Sub/bluerov2-4_0_0.params}"

if [[ ! -d "$ARDUPILOT_HOME" ]]; then
  echo "ArduPilot repo not found at $ARDUPILOT_HOME" >&2
  exit 1
fi

cd "$ARDUPILOT_HOME"

pids=()
for i in $(seq 0 $((FLEET_SIZE - 1))); do
  ./Tools/autotest/sim_vehicle.py \
    -v ArduSub \
    -f "$FRAME" \
    --model "$MODEL" \
    --add-param-file="$PARAM_FILE" \
    --instance "$i" \
    &
  pids+=("$!")
done

wait "${pids[@]}"

# Blue Spark Oceans - Docker for running container

Blue Spark Oceans is a physics-informed multi-AUV simulation environment for persistent subsea monitoring. It uses Gazebo Harmonic (gz-sim8), ArduSub SITL, and ROS 2 bridging for control and logging. The system produces AoI / IVT metrics and energy estimates to support fleet-size, localization, and trajectory studies.

## Project Layout

- `worlds/swarm.sdf` — main world (BlueROV swarm + pipeline + currents)
- `models/bluerov2/` — local BlueROV model
- `scripts/` — control, localization noise, AoI logging, energy model, experiments
- `data/experiments/` — output CSVs
- `config.env` — default runtime configuration
- `waypoints/mission.txt` — per-vehicle waypoint lists

## Requirements


## Quick Start

1) After cloning the repository you should run:
   `chmod +x start_docker.sh`

2) After that type in:
   `./start_docker.sh` 

3)Once your in the container please remember about one thing:
  ```
  mkdir /workspace/ardupilot/Tools/Frame_params/Sub
  mv /workspace/bluerov2-4_0_0.params /workspace/ardupilot/Frame_params/Sub
  ```
4) These paths should already be specified:
  ```
  BS_ARDUPILOT_PLUGIN_PATH=/path/to/ardupilot_gazebo/build
  BS_ARDUPILOT_HOME=/path/to/ardupilot
  ```

5) Start the simulation:
  
  ```
  cd /workspace/BS_Oceans
  set -a
  source ./config.env
  set +a
  ./run.sh
  ```

## Multi-Vehicle ArduSub

`run.sh` starts one ArduSub SITL instance per vehicle (`BS_FLEET_SIZE`).

Default MAVLink endpoints are auto-generated.

## Notes

- This setup is ArduSub-only; direct thrust controllers are removed.
- For multi-vehicle ArduSub, use separate MAVLink endpoints via `BS_MAVLINK_ENDPOINTS`.
- ROS bridge is started automatically by `run.sh`.

# Blue Spark Oceans

Blue Spark Oceans is a physics-informed multi-AUV simulation environment for persistent subsea monitoring. It uses Gazebo Harmonic (gz-sim8), ArduSub SITL, and ROS 2 bridging for control and logging. The system produces AoI / IVT metrics and energy estimates to support fleet-size, localization, and trajectory studies.

## Project Layout

- `worlds/swarm.sdf` — main world (BlueROV swarm + pipeline + currents)
- `models/bluerov2/` — local BlueROV model
- `scripts/` — control, localization noise, AoI logging, energy model, experiments
- `data/experiments/` — output CSVs
- `config.env` — default runtime configuration
- `waypoints/mission.txt` — per-vehicle waypoint lists

## Requirements

- Gazebo Harmonic (gz-sim8)
- ArduPilot SITL (ArduSub) built locally
- ArduPilot Gazebo plugin (`libArduPilotPlugin.so`)
- ROS 2 Jazzy + `ros_gz_bridge`
- Python 3 + `pymavlink`

## Quick Start

1) Configure environment variables (edit `config.env`):

```
BS_ARDUPILOT_PLUGIN_PATH=/path/to/ardupilot_gazebo/build
BS_ARDUPILOT_HOME=/path/to/ardupilot
```

2) Start the simulation:

```
cd /home/janmikolajczyk/projects/blue_spark_oceans
set -a
source ./config.env
set +a
./run.sh
```

## Multi-Vehicle ArduSub

`run.sh` starts one ArduSub SITL instance per vehicle (`BS_FLEET_SIZE`).

Default MAVLink endpoints are auto-generated:

```
udp:127.0.0.1:14550
udp:127.0.0.1:14560
udp:127.0.0.1:14570
...
```

You can override with:

```
BS_MAVLINK_ENDPOINTS=udp:127.0.0.1:14550,udp:127.0.0.1:14560,udp:127.0.0.1:14570
```

If you need ArduSub consoles or map windows:

```
BS_ARDU_CONSOLE=1
BS_ARDU_MAP=1
```

## Waypoints

Waypoints are stored in `waypoints/mission.txt` and are required for ArduSub control.

Format:
- Per-vehicle lines only:

```
bluerov1 2 2 1.5
bluerov1 8 2 1.5
bluerov1 8 8 1.5
bluerov1 2 8 1.5

bluerov2 5 5 2.0
bluerov2 12 5 2.0
```

Each line is `vehicle x y z` in meters (ENU, z is depth).

## Experiments

Run a sweep across fleet size, localization RMSE, and trajectory strategies:

```
python3 scripts/experiment_runner.py
```

Parameters (from `config.env` or exported env):
- Fleet sizes: `BS_FLEET_SIZES=3,4,5,6`
- RMSE range: `BS_LOC_RMSE_MIN`, `BS_LOC_RMSE_MAX`, `BS_LOC_RMSE_STEP`
- Strategies: `BS_STRATEGIES=lawnmower,stochastic,voronoi`
- Duration: `BS_DURATION=300`

Outputs:
- AoI/IVT CSV: `data/experiments/<exp_id>.csv`
- Energy CSV: `data/experiments/<exp_id>_energy.csv`

## Currents (Uniform)

Set current in `config.env`:

```
BS_CURRENT_X=0.2
BS_CURRENT_Y=0.0
BS_CURRENT_Z=0.0
BS_CURRENT_K=25.0
```

## Energy Model

Drag-based energy estimate:

```
BS_DRAG_RHO=1000.0
BS_DRAG_CD=0.8
BS_DRAG_AREA=0.1
BS_PROP_EFF=0.6
BS_HOTEL_W=15.0
```

## Notes

- This setup is ArduSub-only; direct thrust controllers are removed.
- For multi-vehicle ArduSub, use separate MAVLink endpoints via `BS_MAVLINK_ENDPOINTS`.
- ROS bridge is started automatically by `run.sh`.

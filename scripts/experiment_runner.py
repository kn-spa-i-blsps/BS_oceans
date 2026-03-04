#!/usr/bin/env python3
import math
import os
import signal
import subprocess
import sys
import time


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORLD_BASE = os.path.join(PROJECT_ROOT, "worlds", "swarm.sdf")
GENERATED_DIR = os.path.join(PROJECT_ROOT, "worlds", "generated")


def _parse_list(value, cast=float):
    return [cast(v.strip()) for v in value.split(",") if v.strip()]


def _parse_range(min_val, max_val, step):
    values = []
    v = min_val
    while v <= max_val + 1e-9:
        values.append(v)
        v += step
    return values


def _load_base_world():
    with open(WORLD_BASE, "r", encoding="utf-8") as f:
        return f.read()


def _generate_includes(count, spacing=12.0):
    cols = int(math.ceil(math.sqrt(count)))
    rows = int(math.ceil(count / cols))
    start_x = 0.0
    start_y = 0.0
    blocks = []
    for i in range(count):
        row = i // cols
        col = i % cols
        x = start_x + col * spacing
        y = start_y + row * spacing
        name = f"bluerov{i + 1}"
        port = 9002 + i * 10
        block = f"""
    <!-- ================= AUV #{i + 1} ================= -->
    <include>
      <name>{name}</name>
      <pose>{x:.2f} {y:.2f} 1 0 0 1.57</pose>
      <uri>model://bluerov2</uri>

      <plugin filename="gz-sim-thruster-system" name="gz::sim::systems::Thruster">
        <namespace>{name}</namespace>
        <joint_name>thruster1_joint</joint_name>
        <thrust_coefficient>0.004422</thrust_coefficient>
        <fluid_density>1000</fluid_density>
        <propeller_diameter>0.1</propeller_diameter>
      </plugin>
      <plugin filename="gz-sim-thruster-system" name="gz::sim::systems::Thruster">
        <namespace>{name}</namespace>
        <joint_name>thruster2_joint</joint_name>
        <thrust_coefficient>0.004422</thrust_coefficient>
        <fluid_density>1000</fluid_density>
        <propeller_diameter>0.1</propeller_diameter>
      </plugin>
      <plugin filename="gz-sim-thruster-system" name="gz::sim::systems::Thruster">
        <namespace>{name}</namespace>
        <joint_name>thruster3_joint</joint_name>
        <thrust_coefficient>0.004422</thrust_coefficient>
        <fluid_density>1000</fluid_density>
        <propeller_diameter>0.1</propeller_diameter>
      </plugin>
      <plugin filename="gz-sim-thruster-system" name="gz::sim::systems::Thruster">
        <namespace>{name}</namespace>
        <joint_name>thruster4_joint</joint_name>
        <thrust_coefficient>0.004422</thrust_coefficient>
        <fluid_density>1000</fluid_density>
        <propeller_diameter>0.1</propeller_diameter>
      </plugin>
      <plugin filename="gz-sim-thruster-system" name="gz::sim::systems::Thruster">
        <namespace>{name}</namespace>
        <joint_name>thruster5_joint</joint_name>
        <thrust_coefficient>0.004422</thrust_coefficient>
        <fluid_density>1000</fluid_density>
        <propeller_diameter>0.1</propeller_diameter>
      </plugin>
      <plugin filename="gz-sim-thruster-system" name="gz::sim::systems::Thruster">
        <namespace>{name}</namespace>
        <joint_name>thruster6_joint</joint_name>
        <thrust_coefficient>0.004422</thrust_coefficient>
        <fluid_density>1000</fluid_density>
        <propeller_diameter>0.1</propeller_diameter>
      </plugin>

      <plugin name="ArduPilotPlugin" filename="libArduPilotPlugin.so">
        <fdm_addr>127.0.0.1</fdm_addr>
        <fdm_port_in>{port}</fdm_port_in>
        <connectionTimeoutMaxCount>5</connectionTimeoutMaxCount>
        <lock_step>1</lock_step>

        <modelXYZToAirplaneXForwardZDown>0 0 0 3.142 0 0</modelXYZToAirplaneXForwardZDown>
        <gazeboXYZToNED>0 0 0 3.142 0 1.571</gazeboXYZToNED>

        <imuName>imu_sensor</imuName>

        <control channel="0">
          <jointName>thruster1_joint</jointName>
          <servo_min>1100</servo_min>
          <servo_max>1900</servo_max>
          <type>COMMAND</type>
          <cmd_topic>/model/{name}/joint/thruster1_joint/cmd_thrust</cmd_topic>
          <offset>-0.5</offset>
          <multiplier>100</multiplier>
        </control>
        <control channel="1">
          <jointName>thruster2_joint</jointName>
          <servo_min>1100</servo_min>
          <servo_max>1900</servo_max>
          <type>COMMAND</type>
          <cmd_topic>/model/{name}/joint/thruster2_joint/cmd_thrust</cmd_topic>
          <offset>-0.5</offset>
          <multiplier>100</multiplier>
        </control>
        <control channel="2">
          <jointName>thruster3_joint</jointName>
          <servo_min>1100</servo_min>
          <servo_max>1900</servo_max>
          <type>COMMAND</type>
          <cmd_topic>/model/{name}/joint/thruster3_joint/cmd_thrust</cmd_topic>
          <offset>-0.5</offset>
          <multiplier>100</multiplier>
        </control>
        <control channel="3">
          <jointName>thruster4_joint</jointName>
          <servo_min>1100</servo_min>
          <servo_max>1900</servo_max>
          <type>COMMAND</type>
          <cmd_topic>/model/{name}/joint/thruster4_joint/cmd_thrust</cmd_topic>
          <offset>-0.5</offset>
          <multiplier>100</multiplier>
        </control>
        <control channel="4">
          <jointName>thruster5_joint</jointName>
          <servo_min>1100</servo_min>
          <servo_max>1900</servo_max>
          <type>COMMAND</type>
          <cmd_topic>/model/{name}/joint/thruster5_joint/cmd_thrust</cmd_topic>
          <offset>-0.5</offset>
          <multiplier>100</multiplier>
        </control>
        <control channel="5">
          <jointName>thruster6_joint</jointName>
          <servo_min>1100</servo_min>
          <servo_max>1900</servo_max>
          <type>COMMAND</type>
          <cmd_topic>/model/{name}/joint/thruster6_joint/cmd_thrust</cmd_topic>
          <offset>-0.5</offset>
          <multiplier>100</multiplier>
        </control>
      </plugin>
    </include>
"""
        blocks.append(block.rstrip())
    return "\n".join(blocks) + "\n"


def generate_world(count):
    os.makedirs(GENERATED_DIR, exist_ok=True)
    text = _load_base_world()
    first = text.find("<include>")
    last = text.rfind("</include>")
    if first == -1 or last == -1:
        raise RuntimeError("Base world has no include blocks")
    prefix = text[:first]
    suffix = text[last + len("</include>") :]
    includes = _generate_includes(count)
    out = prefix + includes + suffix
    path = os.path.join(GENERATED_DIR, f"swarm_{count}.sdf")
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    return path


def run_experiment(fleet_size, rmse, strategy, duration, seed):
    world_path = generate_world(fleet_size)
    ts = time.strftime("%Y%m%d_%H%M%S")
    exp_id = f"fs{fleet_size}_rmse{rmse:g}_{strategy}_{ts}"
    out_csv = os.path.join(PROJECT_ROOT, "data", "experiments", f"{exp_id}.csv")
    energy_csv = os.path.join(PROJECT_ROOT, "data", "experiments", f"{exp_id}_energy.csv")

    env = os.environ.copy()
    env.update(
        {
            "BS_FLEET_SIZE": str(fleet_size),
            "BS_LOC_RMSE": str(rmse),
            "BS_STRATEGY": strategy,
            "BS_SEED": str(seed),
            "BS_WORLD_PATH": world_path,
            "BS_OUTPUT_CSV": out_csv,
            "BS_ENERGY_CSV": energy_csv,
            "BS_EXPERIMENT_ID": exp_id,
            "BS_VEHICLE_PREFIX": "bluerov",
        }
    )

    proc = subprocess.Popen(
        [os.path.join(PROJECT_ROOT, "run.sh")],
        cwd=PROJECT_ROOT,
        env=env,
    )
    try:
        time.sleep(duration)
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.terminate()
    return out_csv


def main():
    fleet_sizes = _parse_list(os.getenv("BS_FLEET_SIZES", "3,4,5,6"), int)
    if os.getenv("BS_LOC_RMSE_MIN") and os.getenv("BS_LOC_RMSE_MAX") and os.getenv("BS_LOC_RMSE_STEP"):
        rmse_min = float(os.getenv("BS_LOC_RMSE_MIN"))
        rmse_max = float(os.getenv("BS_LOC_RMSE_MAX"))
        rmse_step = float(os.getenv("BS_LOC_RMSE_STEP"))
        rmses = _parse_range(rmse_min, rmse_max, rmse_step)
    else:
        rmses = _parse_list(os.getenv("BS_LOC_RMSES", "0.5,1.0,2.0,3.0"), float)
    strategies = _parse_list(os.getenv("BS_STRATEGIES", "lawnmower,stochastic,voronoi"), str)
    duration = float(os.getenv("BS_DURATION", "300"))
    seed = int(os.getenv("BS_SEED", "42"))

    for fleet in fleet_sizes:
        for rmse in rmses:
            for strat in strategies:
                print(f"Running {fleet} AUVs, RMSE {rmse}, {strat}")
                out = run_experiment(fleet, rmse, strat, duration, seed)
                print(f"Saved: {out}")


if __name__ == "__main__":
    sys.exit(main())

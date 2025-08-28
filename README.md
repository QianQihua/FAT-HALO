# FAT Tool Scripts Repository

## Repository Purpose
This repository stores FAT testing tools and related automation scripts, including core modules for ultrasonic sensor parameter configuration and data collection.

## Script Functionality

### Data Collection Module
- `record_lidar_ultrasonic_camera.sh`  
LIDAR–ultrasonic–camera data collection script that records the following ROS topics in real time:
  - `/camera/compressed_output/compressed` (camera compressed stream)
  - `/move_base/global_costmap/local_costmap` (navigation costmap)
  - `/scan` (LIDAR scan data)
  - `/ultrasonic_list` (ultrasonic sensor array data)
  - `/rosout_agg` (ROS system logs)

### KS236 Ultrasonic Parameter Configuration Module
- `ks236_energy_get.py`: Read energy parameters in real time
- `ks236_energy_set.py`: Configure energy parameters online
- `ks236_p_get.py`: Read FOV (P-value) parameters in real time
- `ks236_p_set.py`: Configure FOV (P-value) parameters online
- `ultrasonic_set.bash`: One-click script to deploy default parameter configuration

## Deployment Guide

### Environment Preparation
1. In your browser, visit https://smart.kabam.ai/login, log in with your account, select the Halo with the corresponding ID, and enter the Terminal.
2. Create a shared directory and prepare to clone the repository:
```bash
sudo mkdir -p ~/FAT_TOOLS/ultrasonic
cd ~/FAT_TOOLS/ultrasonic/
```
#### Clone the repository
```bash
sudo git clone https://github.com/QianQihua/FAT-HALO.git
```
After cloning, you should see at least four Python scripts and two bash scripts.
#### Or connect your personal computer to the Halo Wi‑Fi and scp the scripts above to Halo one by one

### Script Initialization
3. Set up a virtual environment and install dependencies:
```bash
cd /home/ubuntu/FAT_TOOLS/ultrasonic/
python3 -m venv ultrasonic_env
sudo apt update && pip install pyserial

```
4. Use the scripts to tune the KS236 ultrasonic energy and P-value online to eliminate false ultrasonic detections.
Note: Before each use, make sure to run the following, otherwise the scripts will not work:
```bash
cd /home/ubuntu/FAT_TOOLS/ultrasonic/
source ultrasonic_env/bin/activate

```
For subsequent online tuning of the ultrasonic sensors, refer to `UltrasonicSensors_SOP(CN)v1.3.pdf` or `UltrasonicSensors_SOP(EN)v1.3.pdf` in this repository. For basic script usage, see Part 1; for the principles and methods of ultrasonic probe noise tuning, see Part 2.

5. Use the one-click script to configure ultrasonic parameters (optional, for quickly restoring ultrasonic parameters and state):
```bash
cd /home/ubuntu/FAT_TOOLS/ultrasonic/
source ultrasonic_set.bash
```

6. Deploy the data collection script (optional, for recording and analyzing ultrasonic data):
```bash
docker cp record_lidar_ultrasonic_camera.sh ultrasonic_sensors:/home/catkin_ws
# Verify transfer: Successfully copied 13.3kB...

docker exec -it ultrasonic_sensors bash
source /opt/ros/noetic/setup.bash
bash record_lidar_ultrasonic_camera.sh
```

## Related Documents
- `UltrasonicSensors_SOP(CN)v1.3.pdf`: Chinese SOP
- `UltrasonicSensors_SOP(EN)v1.3.pdf`: English SOP
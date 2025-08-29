# FAT Tool Scripts Repository

## Repository Purpose
This repository stores FAT testing tools and related automation scripts, including core modules for ultrasonic sensor parameter configuration and data collection.

## Script Functionality

### Data Collection Module
- `record_lidar_ultrasonic_camera.sh`  
LIDAR–ultrasonic–camera data collection script that records the following ROS topics in real time:
  - `/camera/compressed_output/compressed` (camera compressed data stream)
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
Visit https://smart.kabam.ai/login, enter your account and password, select the Halo with the corresponding ID, and enter the Terminal.
Create a shared directory, note to modify the shared directory and its subfolder permissions:
```bash
sudo mkdir -p ~/FAT_TOOLS/ultrasonic
sudo chown -R ubuntu:ubuntu ~/FAT_TOOLS/
cd ~/FAT_TOOLS/ultrasonic/
```

### Transfer Scripts
Copy the scripts from FAT_HALO.zip in your PC to /home/ubuntu/FAT_TOOLS/ultrasonic/ (using any method like scp)

### Set Up Virtual Environment and Install Dependencies
```bash
cd /home/ubuntu/FAT_TOOLS/ultrasonic/FAT_HALO
sudo python3 -m venv ultrasonic_env
source ultrasonic_env/bin/activate
```

### Use Scripts to Tune KS236 Ultrasonic Energy and P-value Online to Eliminate Non-existent Noise Detected by Ultrasonic Sensors
Note: Before each use, be sure to run the following two commands; otherwise the scripts will not work.
```bash
cd /home/ubuntu/FAT_TOOLS/ultrasonic/FAT_HALO/
source ultrasonic_env/bin/activate
```
If you get "No module named 'pyserial'", then run:
```bash
pip install pyserial
```
For subsequent online tuning of the ultrasonic sensors, refer to `UltrasonicSensors_SOP(CN)v1.3.pdf` or `UltrasonicSensors_SOP(EN)v1.3.pdf` in this repository. For basic script usage, see Part 1; for the principles and methods of ultrasonic probe noise tuning, see Part 2.

Use the one-click script to configure ultrasonic parameters (optional, for quickly restoring ultrasonic parameters and state):
```bash
cd /home/ubuntu/FAT_TOOLS/ultrasonic/FAT_HALO/
source ultrasonic_set.bash
```
Note: If you encounter the following errors when running `ultrasonic_set.bash`:
```bash
(ultrasonic_env) ubuntu@Halo82:~/FAT_TOOLS/ultrasonic/FAT_HALO$ bash ultrasonic_set.bash
': not a valid identifier 8: export: `PATH
ultrasonic_set.bash: line 9: $'\r': command not found
ultrasonic_set.bash: line 17: $'\r': command not found
ultrasonic_set.bash: line 18: $'\r': command not found
ultrasonic_set.bash: line 20: syntax error near unexpected token `$'{\r''
'ltrasonic_set.bash: line 20: `validate_path() {

```
You can run:
```bash
sed -i 's/\r$//' ultrasonic_set.bash
chmod +x ultrasonic_set.bash

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

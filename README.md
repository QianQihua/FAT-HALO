# FAT Tools Repository

## Repository Purpose
This repository contains FAT testing tools and automation scripts for ultrasonic sensor configuration and data acquisition systems.

## Script Functionality

### Data Collection Module
- `record_lidar_ultrasonic_camera.sh`  
Multi-sensor data collection script recording following ROS topics:
  - `/camera/compressed_output/compressed` (Camera stream)
  - `/move_base/global_costmap/local_costmap` (Navigation costmap)
  - `/scan` (LIDAR point cloud)
  - `/ultrasonic_list` (Ultrasonic array data)
  - `/rosout_agg` (ROS system logs)

### KS236 Ultrasonic Configuration Module
- `ks236_energy_get.py`: Real-time energy parameter monitoring
- `ks236_energy_set.py`: Online energy parameter configuration
- `ks236_p_get.py`: FOV (P-value) parameter monitoring
- `ks236_p_set.py`: FOV (P-value) parameter configuration
- `ultrasonic_set.bash`: One-click deployment script for default parameters

## Deployment Guide

### Environment Setup
1. Login to Halo Terminal
2. Clone repository:
```bash
sudo git clone http://192.168.161.40:3000/Erich/Script-repo.git
cd Script-repo
```
3. Switch branch:
```bash
sudo git checkout FAT_Tools
sudo git branch  # Verify branch status (*FAT_Tools)
```

### File Deployment
4. Create shared directory:
```bash
sudo mkdir -p ~/FAT_TOOLS/ultrasonic/
```
5. Copy scripts:
```bash
# Copy Python scripts
sudo cp *.py ~/FAT_TOOLS/ultrasonic/

# Copy deployment script
sudo cp ultrasonic_set.bash ~/FAT_TOOLS/ultrasonic/
```

### Script Initialization
6. Configure ultrasonic scripts:
```bash
cd /home/ubuntu/FAT_TOOLS/ultrasonic/
python3 -m venv ultrasonic_env
sudo apt update && pip install pyserial
source ultrasonic_set.bash
```

7. Deploy data collection script:
```bash
docker cp record_lidar_ultrasonic_camera.sh ultrasonic_sensors:/home/catkin_ws
# Verify transfer: Successfully copied 13.3kB...

docker exec -it ultrasonic_sensors bash
source /opt/ros/noetic/setup.bash
bash record_lidar_ultrasonic_camera.sh
```

## Documentation
- `UltrasonicSensors_SOP(CN)v1.2.docx`: Chinese SOP
- `UltrasonicSensors_SOP(EN)v1.2.docx`: English SOP
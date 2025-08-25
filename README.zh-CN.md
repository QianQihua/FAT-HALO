# FAT工具脚本仓库

## 仓库用途
本仓库用于存储FAT测试工具及相关自动化脚本，包含超声波传感器参数配置、数据采集等核心功能模块。

## 脚本功能说明

### 数据采集模块
- `record_lidar_ultrasonic_camera.sh`  
激光雷达-超声波-相机数据采集脚本，实时记录以下ROS话题：
  - `/camera/compressed_output/compressed`（相机压缩数据流）
  - `/move_base/global_costmap/local_costmap`（导航代价地图）
  - `/scan`（激光雷达扫描数据）
  - `/ultrasonic_list`（超声波传感器阵列数据）
  - `/rosout_agg`（ROS系统日志）

### KS236超声波参数配置模块
- `ks236_energy_get.py`：实时读取能量参数
- `ks236_energy_set.py`：在线配置能量参数
- `ks236_p_get.py`：实时读取FOV（P值）参数
- `ks236_p_set.py`：在线配置FOV（P值）参数
- `ultrasonic_set.bash`：一键部署默认参数配置脚本

## 部署指南

### 环境准备
1. 登录Halo终端
2. 克隆仓库：
```bash
sudo git clone http://192.168.161.40:3000/Erich/Script-repo.git
cd Script-repo
```
3. 切换分支：
```bash
sudo git checkout FAT_Tools
sudo git branch  # 验证分支状态（*FAT_Tools）
```

### 文件部署
4. 创建公共目录：
```bash
sudo mkdir -p ~/FAT_TOOLS/ultrasonic/
```
5. 复制脚本文件：
```bash
# 复制Python脚本
sudo cp *.py ~/FAT_TOOLS/ultrasonic/

# 复制部署脚本
sudo cp ultrasonic_set.bash ~/FAT_TOOLS/ultrasonic/
```

### 脚本初始化
6. 配置超声波参数脚本：
```bash
cd /home/ubuntu/FAT_TOOLS/ultrasonic/
python3 -m venv ultrasonic_env
sudo apt update && pip install pyserial
source ultrasonic_set.bash
```

7. 部署数据采集脚本：
```bash
docker cp record_lidar_ultrasonic_camera.sh ultrasonic_sensors:/home/catkin_ws
# 验证传输成功：Successfully copied 13.3kB...

docker exec -it ultrasonic_sensors bash
source /opt/ros/noetic/setup.bash
bash record_lidar_ultrasonic_camera.sh
```

## 相关文档
- `UltrasonicSensors_SOP(CN)v1.2.docx`：中文版操作规范
- `UltrasonicSensors_SOP(EN)v1.2.docx`：英文版操作规范
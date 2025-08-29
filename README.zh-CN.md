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
浏览器输入https://smart.kabam.ai/login，输入你的账号密码，选择对应编号的Halo,并进入终端Terminal
创建公共目录，注意修改公共目录及其子文件夹权限：
```bash
sudo mkdir -p ~/FAT_TOOLS/ultrasonic
sudo chown -R ubuntu:ubuntu ~/FAT_TOOLS/
cd ~/FAT_TOOLS/ultrasonic/
```
### 传输脚本
把FAT_HALO.zip里的脚本copy进/home/ubuntu/FAT_TOOLS/ultrasonic/(任何类似scp的方法)


### 搭建虚拟环境并安装依赖
```bash
cd /home/ubuntu/FAT_TOOLS/ultrasonic/FAT_HALO
sudo python3 -m venv ultrasonic_env
source ultrasonic_env/bin/activate
```

### 使用脚本在线调试超声波KS236的能量和P值以消除超声波探测到的不存在的噪点
注意：每次使用脚本以前请务必执行下属两条语句，否则无法使用。
```bash
cd /home/ubuntu/FAT_TOOLS/ultrasonic/FAT_HALO/
source ultrasonic_env/bin/activate
```
如果提示No module named 'pyserial'，则执行：
```bash
pip install pyserial
```
后续的对超声波的在线调试参考仓库中的`UltrasonicSensors_SOP(CN)v1.3.pdf`或者`UltrasonicSensors_SOP(EN)v1.3.pdf`。其中脚本的基本使用参考第一部分，超声波探头噪点调试的原理和方法参考第二部分

使用脚本一键配置超声波参数(可选，用于快速还原超声波的参数和状态)：
```bash
cd /home/ubuntu/FAT_TOOLS/ultrasonic/FAT_HALO/
source ultrasonic_set.bash
```
注意：如执行ultrasonic_set.bash遇到以下报错:
```bash
(ultrasonic_env) ubuntu@Halo82:~/FAT_TOOLS/ultrasonic/FAT_HALO$ bash ultrasonic_set.bash
': not a valid identifier 8: export: `PATH
ultrasonic_set.bash: line 9: $'\r': command not found
ultrasonic_set.bash: line 17: $'\r': command not found
ultrasonic_set.bash: line 18: $'\r': command not found
ultrasonic_set.bash: line 20: syntax error near unexpected token `$'{\r''
'ltrasonic_set.bash: line 20: `validate_path() {

```
可输入:
```bash
sed -i 's/\r$//' ultrasonic_set.bash
chmod +x ultrasonic_set.bash

```

6. 部署数据采集脚本（可选，用于记录和分析超声波数据）：
```bash
docker cp record_lidar_ultrasonic_camera.sh ultrasonic_sensors:/home/catkin_ws
# 验证传输成功：Successfully copied 13.3kB...

docker exec -it ultrasonic_sensors bash
source /opt/ros/noetic/setup.bash
bash record_lidar_ultrasonic_camera.sh
```

## 附属相关文档
- `UltrasonicSensors_SOP(CN)v1.3.pdf`：中文版操作规范
- `UltrasonicSensors_SOP(EN)v1.3.pdf`：英文版操作规范

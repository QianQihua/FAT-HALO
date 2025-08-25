#!/bin/bash


# 强制设置bash严格模式
set -euo pipefail
source /opt/ros/noetic/setup.bash
command -v rosbag >/dev/null || { echo "未找到rosbag命令"; exit 1; }

export BAG_DIR="/home/catkin_ws/bags"
declare -g MONITOR_PID=0
DATE_SUFFIX=$(date +%y%m%d)
BAG_SUBDIR="${BAG_DIR}/bags_${DATE_SUFFIX}"
TIMESTAMP=$(date +%H%M%S)
DURATION=180
TOPICS="/scan /ultrasonic_list /move_base/global_costmap/local_costmap /camera/compressed_output/compressed /rosout_agg"
mkdir -p "$BAG_SUBDIR" || { echo "Creating directory failed."; exit 1; }
chmod -R 750 "$BAG_SUBDIR"
KEEP_FILES=20
SPLIT_SIZE=2048
BUFFER_SIZE=32768
CHUNK_SIZE=2048
LOG_FILE="${BAG_DIR}/recording_${DATE_SUFFIX}_${TIMESTAMP}.log"
exec 2> >(tee -a "$LOG_FILE") 2>&1
echo "==== Recording Start at $(date +%H%M%S) ===="

# 修复1: 使用专用函数清理旧文件（仅针对当前日期子目录）
# 在clean_old_bags()函数中增加调试输出
clean_old_bags() {
    echo "[CLEAN] 删除超过3分钟的bag文件（目录: $BAG_SUBDIR）"
    echo "[CLEAN] 删除修改时间早于 $(date -d '3 minutes ago' +'%H:%M:%S') 的文件:"
    # 排除当前录制文件（通配符匹配）
    local exclude_pattern="lidar_costmap_ultrasonic_data_${TIMESTAMP}_*"
    find "$BAG_SUBDIR" -type f -name '*.bag' -mmin +3 ! -name "$exclude_pattern" -print
    # 打印待删除文件列表
    local files_to_delete=$(find "$BAG_SUBDIR" -type f -name '*.bag' -mmin +3 -print)
    if [ -n "$files_to_delete" ]; then
        echo "待删除文件:"
        printf '  - %s\n' "$files_to_delete"
        find "$BAG_SUBDIR" -type f -name '*.bag' -mmin +3 -delete
    else
        echo "无符合删除条件的文件"
    fi
}


# 修复2: 避免信号递归
# 修复进程组变量
RECORD_PGID=0
MONITOR_PGID=0

# 修改后的关闭函数
shutdown_sequence() {
    echo "捕获终止信号，开始清理流程..."
    trap - INT TERM EXIT

    # 1. 终止监控进程
    [ $MONITOR_PID -ne 0 ] && kill $MONITOR_PID 2>/dev/null

    # 2. 安全终止录制进程组（新增等待逻辑）
    if [ $PID -ne 0 ]; then
        echo "等待录制进程退出（最长5秒）..."
        kill -TERM $PID 2>/dev/null
        # 等待进程退出，避免强制终止
        local wait_count=0
        while kill -0 $PID 2>/dev/null && [ $wait_count -lt 10 ]; do
            sleep 0.5
            ((wait_count++))
        done
        # 超时后强制终止
        if kill -0 $PID 2>/dev/null; then
            echo "进程未退出，强制终止"
            kill -9 $PID
            [ $RECORD_PGID -ne 0 ] && kill -9 -- -$RECORD_PGID 2>/dev/null
        fi
    fi

    # 3. 清理旧文件（顺序调整到进程终止后）
    clean_old_bags

    # 4. 通配符匹配所有分割文件（修复校验逻辑）
    sleep 1
    for bag in "${BAG_SUBDIR}/lidar_costmap_ultrasonic_data_${TIMESTAMP}"_*.bag; do
        [ -f "$bag" ] || continue
        echo "校验文件: $bag"
        validate_bag_file "$bag"
    done
    # 额外检查可能存在的 .active 文件
    find "$BAG_SUBDIR" -name "lidar_costmap_ultrasonic_data_${TIMESTAMP}_*.active" | while read active_file; do
        validate_bag_file "${active_file%.active}"  # 去除后缀后校验
    done

    # 5. 数据同步
    echo "数据同步..."
    sync
    exit 0
}

# 新增校验函数
validate_bag_file() {
    local file="$1"
    # 若存在同名的 .active 文件，优先修复
    if [ -f "${file}.active" ]; then
        echo "检测到未完成文件: ${file}.active，尝试修复..."
        rosbag reindex "${file}.active" &>> "$LOG_FILE"
        rosbag fix "${file}.active" "${file}.fixed" &>> "$LOG_FILE" && mv "${file}.fixed" "$file"
        rm -f "${file}.active"
    fi
    # 常规校验
    if timeout 10 rosbag info "$file" &>> "$LOG_FILE"; then
        echo "文件验证通过" >&2
    else
        echo "文件损坏，尝试修复..."
        rosbag fix "$file" "${file}.fixed" &>> "$LOG_FILE" && mv "${file}.fixed" "$file"
    fi
}


trap shutdown_sequence INT TERM EXIT

# 启动前清理
clean_old_bags
find "$BAG_DIR" -name "*.active" -delete
find "$BAG_DIR" -name "*.recover" -exec rosbag reindex {} \; 2>/dev/null || true

# 主进程录制（保持不变）
rosbag record -O $BAG_SUBDIR/lidar_costmap_ultrasonic_data_${TIMESTAMP} \
    --duration=$DURATION \
    --split --size=$SPLIT_SIZE \
    --max-splits=$KEEP_FILES \
    --lz4 \
    -b $BUFFER_SIZE \
    --chunksize=$CHUNK_SIZE \
    --tcpnodelay \
    $TOPICS &
PID=$!
sleep 2
#PGID=$(ps -o pgid= $PID | grep -o '[0-9]\+')  # 精确获取PGID
RECORD_PGID=$(ps -o pgid= $PID | tr -d ' ')

# 启动监控进程（修改输出）
(
while sleep 10; do
    echo "==== 系统状态更新 ===="
    free -m | awk '/Mem/{printf "内存使用率:%.1f%% ", $3/$2 * 100}'
    df -h "${BAG_DIR}" | awk 'NR==2{printf "磁盘使用率:%s\n", $5}'
done
) >> "$LOG_FILE" 2>&1 &
MONITOR_PID=$!
MONITOR_PGID=$(ps -o pgid= $MONITOR_PID | tr -d ' ')

#主进程等待
wait $PID
validate_bag_file "${BAG_SUBDIR}/lidar_costmap_ultrasonic_data_${TIMESTAMP}.bag"

#深度文件校验
if rosbag check "${BAG_SUBDIR}/lidar_costmap_ultrasonic_data_${TIMESTAMP}.bag" &>>$LOG_FILE; then
        echo "深度校验通过"
else
        echo "检测到损坏，尝试修复..."
        rosbag fix "${BAG_FILE}" "${BAG_FILE}.fixed"  #生成修复后的副本
        mv "${BAG_FILE}.fixed" "${BAG_FILE}"
fi

#最终校验
if rosbag info "${BAG_SUBDIR}/lidar_costmap_ultrasonic_data_${TIMESTAMP}.bag" &>/dev/null; then
        echo "录制文件验证通过"
else
        echo "警告： 生成的bag文件可能损坏！ " >&2
        exit 1
fi

exit 0
root@Halo82:/home/catkin_ws# vim record_lidar_ultrasonic_camera.sh
root@Halo82:/home/catkin_ws# vim record_lidar_ultrasonic_camera.sh
root@Halo82:/home/catkin_ws# cat record_lidar_ultrasonic_camera.sh
#!/bin/bash
# 省略头部注释和配置（保持不变）...

# 强制设置bash严格模式
set -euo pipefail
source /opt/ros/noetic/setup.bash
command -v rosbag >/dev/null || { echo "未找到rosbag命令"; exit 1; }

export BAG_DIR="/home/catkin_ws/bags"
declare -g MONITOR_PID=0
DATE_SUFFIX=$(date +%y%m%d)
BAG_SUBDIR="${BAG_DIR}/bags_${DATE_SUFFIX}"
TIMESTAMP=$(date +%H%M%S)
DURATION=180
TOPICS="/scan /ultrasonic_list /move_base/global_costmap/local_costmap /camera/compressed_output/compressed /rosout_agg"
mkdir -p "$BAG_SUBDIR" || { echo "Creating directory failed."; exit 1; }
chmod -R 750 "$BAG_SUBDIR"
KEEP_FILES=20
SPLIT_SIZE=2048
BUFFER_SIZE=32768
CHUNK_SIZE=2048
LOG_FILE="${BAG_DIR}/recording_${DATE_SUFFIX}_${TIMESTAMP}.log"
exec 2> >(tee -a "$LOG_FILE") 2>&1
echo "==== Recording Start at $(date +%H%M%S) ===="

# 修复1: 使用专用函数清理旧文件（仅针对当前日期子目录）
# 在clean_old_bags()函数中增加调试输出
clean_old_bags() {
    echo "[CLEAN] 删除超过120分钟的bag文件（目录: $BAG_SUBDIR）"
    echo "[CLEAN] 删除修改时间早于 $(date -d '120 minutes ago' +'%H:%M:%S') 的文件:"
    # 排除当前录制文件（通配符匹配）
    local exclude_pattern="lidar_costmap_ultrasonic_data_${TIMESTAMP}_*"
    find "$BAG_SUBDIR" -type f -name '*.bag' -mmin +120 ! -name "$exclude_pattern" -print
    # 打印待删除文件列表
    local files_to_delete=$(find "$BAG_SUBDIR" -type f -name '*.bag' -mmin +120 -print)
    if [ -n "$files_to_delete" ]; then
        echo "待删除文件:"
        printf '  - %s\n' "$files_to_delete"
        find "$BAG_SUBDIR" -type f -name '*.bag' -mmin +120 -delete
    else
        echo "无符合删除条件的文件"
    fi
}


# 修复2: 避免信号递归
# 修复进程组变量
RECORD_PGID=0
MONITOR_PGID=0

# 修改后的关闭函数
shutdown_sequence() {
    echo "捕获终止信号，开始清理流程..."
    trap - INT TERM EXIT

    # 1. 终止监控进程
    [ $MONITOR_PID -ne 0 ] && kill $MONITOR_PID 2>/dev/null

    # 2. 安全终止录制进程组（新增等待逻辑）
    if [ $PID -ne 0 ]; then
        echo "等待录制进程退出（最长5秒）..."
        kill -TERM $PID 2>/dev/null
        # 等待进程退出，避免强制终止
        local wait_count=0
        while kill -0 $PID 2>/dev/null && [ $wait_count -lt 10 ]; do
            sleep 0.5
            ((wait_count++))
        done
        # 超时后强制终止
        if kill -0 $PID 2>/dev/null; then
            echo "进程未退出，强制终止"
            kill -9 $PID
            [ $RECORD_PGID -ne 0 ] && kill -9 -- -$RECORD_PGID 2>/dev/null
        fi
    fi

    # 3. 清理旧文件（顺序调整到进程终止后）
    clean_old_bags

    # 4. 通配符匹配所有分割文件（修复校验逻辑）
    sleep 1
    for bag in "${BAG_SUBDIR}/lidar_costmap_ultrasonic_data_${TIMESTAMP}"_*.bag; do
        [ -f "$bag" ] || continue
        echo "校验文件: $bag"
        validate_bag_file "$bag"
    done
    # 额外检查可能存在的 .active 文件
    find "$BAG_SUBDIR" -name "lidar_costmap_ultrasonic_data_${TIMESTAMP}_*.active" | while read active_file; do
        validate_bag_file "${active_file%.active}"  # 去除后缀后校验
    done

    # 5. 数据同步
    echo "数据同步..."
    sync
    exit 0
}

# 新增校验函数
validate_bag_file() {
    local file="$1"
    # 若存在同名的 .active 文件，优先修复
    if [ -f "${file}.active" ]; then
        echo "检测到未完成文件: ${file}.active，尝试修复..."
        rosbag reindex "${file}.active" &>> "$LOG_FILE"
        rosbag fix "${file}.active" "${file}.fixed" &>> "$LOG_FILE" && mv "${file}.fixed" "$file"
        rm -f "${file}.active"
    fi
    # 常规校验
    if timeout 10 rosbag info "$file" &>> "$LOG_FILE"; then
        echo "文件验证通过" >&2
    else
        echo "文件损坏，尝试修复..."
        rosbag fix "$file" "${file}.fixed" &>> "$LOG_FILE" && mv "${file}.fixed" "$file"
    fi
}


trap shutdown_sequence INT TERM EXIT

# 启动前清理
clean_old_bags
find "$BAG_DIR" -name "*.active" -delete
find "$BAG_DIR" -name "*.recover" -exec rosbag reindex {} \; 2>/dev/null || true

# 主进程录制（保持不变）
rosbag record -O $BAG_SUBDIR/lidar_costmap_ultrasonic_data_${TIMESTAMP} \
    --duration=$DURATION \
    --split --size=$SPLIT_SIZE \
    --max-splits=$KEEP_FILES \
    --lz4 \
    -b $BUFFER_SIZE \
    --chunksize=$CHUNK_SIZE \
    --tcpnodelay \
    $TOPICS &
PID=$!
sleep 2
#PGID=$(ps -o pgid= $PID | grep -o '[0-9]\+')  # 精确获取PGID
RECORD_PGID=$(ps -o pgid= $PID | tr -d ' ')

# 启动监控进程（修改输出）
(
while sleep 10; do
    echo "==== 系统状态更新 ===="
    free -m | awk '/Mem/{printf "内存使用率:%.1f%% ", $3/$2 * 100}'
    df -h "${BAG_DIR}" | awk 'NR==2{printf "磁盘使用率:%s\n", $5}'
done
) >> "$LOG_FILE" 2>&1 &
MONITOR_PID=$!
MONITOR_PGID=$(ps -o pgid= $MONITOR_PID | tr -d ' ')

#主进程等待
wait $PID
validate_bag_file "${BAG_SUBDIR}/lidar_costmap_ultrasonic_data_${TIMESTAMP}.bag"

#深度文件校验
if rosbag check "${BAG_SUBDIR}/lidar_costmap_ultrasonic_data_${TIMESTAMP}.bag" &>>$LOG_FILE; then
        echo "深度校验通过"
else
        echo "检测到损坏，尝试修复..."
        rosbag fix "${BAG_FILE}" "${BAG_FILE}.fixed"  #生成修复后的副本
        mv "${BAG_FILE}.fixed" "${BAG_FILE}"
fi

#最终校验
if rosbag info "${BAG_SUBDIR}/lidar_costmap_ultrasonic_data_${TIMESTAMP}.bag" &>/dev/null; then
        echo "录制文件验证通过"
else
        echo "警告： 生成的bag文件可能损坏！ " >&2
        exit 1
fi

exit 0

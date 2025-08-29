#!/bin/bash
# Program:
#	This script will configure the energy-time-threshold values that determine the maximum detection distance and the FOV parameter P that affects the detection range for ultrasonic probes #1 to #9.
# History:
# 2025/7/1	Erich	First release
# 2025/8/7	Erich	Second release
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
BASE_DIR="$SCRIPT_DIR"
VENV_PATH="$BASE_DIR/ultrasonic_env/bin/activate"
ENERGY_SET_PATH="$BASE_DIR/ks236_energy_set.py"
P_SET_PATH="$BASE_DIR/ks236_p_set.py"
ENERGY_GET_PATH="$BASE_DIR/ks236_energy_get.py"
P_GET_PATH="$BASE_DIR/ks236_p_get.py"


# --------------------[验证路径存在]---------------------
validate_path() {
    if [ ! -e "$1" ]; then
        echo -e "Error: Path does not exist - $1" >&2
        exit 1
    fi
}

validate_path "$VENV_PATH"
validate_path "$ENERGY_SET_PATH"
validate_path "$P_SET_PATH"



# --------------------[Step 1] Stop ultrasonic_sensors-------------------------
echo -e "\n[Step 1] Stop ultarsonic_sensors...\n"
docker stop ultrasonic_sensors || {
	echo -e "Error:Failed to stop ultrasonic_sensors container" >&2
	docker start ultrasonic_sensors
	exit 1
}

# --------------------[Step 2] Activate Python Environment---------------------
echo -e "\n[Step 2] Activating Python Environment...\n"
source "$VENV_PATH" || {
		echo -e "Error: Failed to activate virtual environment,exiting..."
		docker start ultrasonic_sensors
		exit 1
	}

# --------------------[Step 3] Configure energy-time-threshold----------------
echo -e "\n[Step 3] Configuring energy-time-threshold...\n"
python "$ENERGY_SET_PATH" \
	--probe 1 --range 2.5 --energy 3 --time 2 --threshold 2 --device /dev/ttyUS --permanent || { 
	echo -e "\nError:Failed to set energy-time-threshold for probe 1" >&2
	deactivate
	docker start ultrasonic_sensors
	exit 1
}
python "$ENERGY_SET_PATH" \
	--probe 2 --range 2.5 --energy 3 --time 2 --threshold 2 --device /dev/ttyUS --permanent || {
        echo -e "\nError:Failed to set energy-time-threshold for probe 2" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
}
python "$ENERGY_SET_PATH" \
	--probe 3 --range 2.5 --energy 3 --time 2 --threshold 2 --device /dev/ttyUS --permanent || {
        echo -e "\nError:Failed to set energy-time-threshold for probe 3" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
}
python "$ENERGY_SET_PATH" \
	--probe 4 --range 2.5 --energy 3 --time 2 --threshold 2 --device /dev/ttyUS --permanent || {
        echo -e "\nError:Failed to set energy-time-threshold for probe 4" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
}
python "$ENERGY_SET_PATH" \
	--probe 5 --range 2.5 --energy 3 --time 2 --threshold 2 --device /dev/ttyUS --permanent || {
        echo -e "\nError:Failed to set energy-time-threshold for probe 5" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
}
python "$ENERGY_SET_PATH" \
	--probe 6 --range 2.5 --energy 3 --time 2 --threshold 2 --device /dev/ttyUS --permanent || {
        echo -e "\nError:Failed to set energy-time-threshold for probe 6" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
}
python "$ENERGY_SET_PATH" \
	--probe 7 --range 2.5 --energy 3 --time 2 --threshold 2 --device /dev/ttyUS --permanent || {
        echo -e "\nError:Failed to set energy-time-threshold for probe 7" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
}
python "$ENERGY_SET_PATH" \
	--probe 8 --range 2.5 --energy 3 --time 2 --threshold 2 --device /dev/ttyUS --permanent || {
        echo -e "\nError:Failed to set energy-time-threshold for probe 8" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
}
python "$ENERGY_SET_PATH" \
	--probe 9 --range 2.5 --energy 3 --time 2 --threshold 2 --device /dev/ttyUS --permanent || {
        echo -e "\nError:Failed to set energy-time-threshold for probe 9" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
}

# --------------------[Step 4] Verify energy-time-threshold-------------------
echo -e "\n[Step 4] Verifying energy-time-threshold setting...\n"
python "$ENERGY_GET_PATH" || {
	echo -e "Error: Energy verification failed" >&2
	deactivate
	docker start ultrasonic_sensors
	exit 1
}
echo -e "Congratulation!Engergy has been set successfully!\n"

# --------------------[Step 5] Configure FOV parameters-----------------------
echo -e "\n[Step 5] Configuring FOV parameters...\n"
python "$P_SET_PATH" \
	--probe 1 --preset default --permanent || {
        echo -e "Error: Failed to set FOV parameters for probe 1" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
    }
python "$P_SET_PATH" \
	--probe 2 --preset default --permanent || {
        echo -e "Error: Failed to set FOV parameters for probe 2" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
    }
python "$P_SET_PATH" \
	--probe 3 --preset default --permanent || {
        echo -e "Error: Failed to set FOV parameters for probe 3" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
    }
python "$P_SET_PATH" \
	--probe 4 --preset default --permanent || {
        echo -e "Error: Failed to set FOV parameters for probe 4" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
    }
python "$P_SET_PATH" \
	--probe 5 --preset default --permanent || {
        echo -e "Error: Failed to set FOV parameters for probe 5" >&2
        deactivate
	docker start ultrasonic_sensors
	exit 1
    }
python "$P_SET_PATH" \
	--probe 6 --preset default --permanent || {
        echo -e "Error: Failed to set FOV parameters for probe 6" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
    }
python "$P_SET_PATH" \
	--probe 7 --preset default --permanent || {
        echo -e "Error: Failed to set FOV parameters for probe 7" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
    }
python "$P_SET_PATH" \
	--probe 8 --preset default --permanent || {
        echo -e "Error: Failed to set FOV parameters for probe 8" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
    }
python "$P_SET_PATH" \
	--probe 9 --preset default --permanent || {
        echo -e "Error: Failed to set FOV parameters for probe 9" >&2
	deactivate
	docker start ultrasonic_sensors
        exit 1
    }

# --------------------[Step 6] Verify FOV parameters-------------------------
echo -e "\n[Step 6] Verifying FOV parameters setting...\n"
python /home/ubuntu/lab/erich/ultrasonic/ks236_p_get.py || {
	echo -e "Error: FOV parameters verification failed" >&2
	deactivate
	docker start ultrasonic_sensors
	exit 1
}
echo -e "\nCongratulations!P has been set successfully!\n"

# --------------------[Step 7] Cleanup environment----------------------------
echo -e "\n[Step 7] Cleaning up environment...\n"
deactivate || {
    echo "Warning: Failed to deactivate virtual environment" >&2
}

# --------------------[Step 8] Restart ultrasonic_sensors---------------------
echo -e "\n[Step 8] Restarting ultrasonic_sensors..."
docker start ultrasonic_sensors || {
	echo "Error: Failed to start docker container"
	exit 1
}
echo -e "\nUltrasonic_sensors have been set!"

echo -e "\n[Success] Ultrasonic sensors configuration completed!"
exit 0

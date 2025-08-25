#!/usr/bin/env python3
"""
KS236 Ultrasonic Probe Energy Parameter Setter
==============================================

This script sets energy parameters for KS236 ultrasonic probes via RS485 communication.
Based on the RS485 energy control protocol documentation.

Features:
- Set energy parameters for probes 1-9
- Support for all three ranges (2.5m, 1.5m, 6.5m)
- Temporary or permanent setting modes
- Automatic verification after setting
- Command line interface with validation

Usage:
    python ks236_energy_set.py --probe 1 --range 2.5 --energy 2
    python ks236_energy_set.py --probe 5 --range 1.5 --energy 3 --permanent
    python ks236_energy_set.py --probe 3 --range 6.5 --energy 4 --time 5 --threshold 1

Author: Generated for Halo82 ultrasonic system
Date: 2025-06-30
"""

import serial
import time
import argparse
import sys
from typing import Optional, Dict, Any

class KS236EnergySetter:
    """KS236 ultrasonic probe energy parameter setter"""
    
    # Protocol constants
    ADDR_CODE = 0xE8
    CMD_CODE = 0x99
    
    # Probe parameter mappings
    PROBE_TEMP_PARAMS = {  # Temporary modification (0xB1-0xBC)
        1: 0xB1, 2: 0xB2, 3: 0xB3, 4: 0xB4, 5: 0xB5,
        6: 0xB6, 7: 0xB7, 8: 0xB8, 9: 0xB9, 10: 0xBA,
        11: 0xBB, 12: 0xBC
    }
    
    PROBE_PERM_PARAMS = {  # Permanent modification (0x71-0x7C)
        1: 0x71, 2: 0x72, 3: 0x73, 4: 0x74, 5: 0x75,
        6: 0x76, 7: 0x77, 8: 0x78, 9: 0x79, 10: 0x7A,
        11: 0x7B, 12: 0x7C
    }
    
    PROBE_QUERY_PARAMS = {  # Query parameters (0xD1-0xDC)
        1: 0xD1, 2: 0xD2, 3: 0xD3, 4: 0xD4, 5: 0xD5,
        6: 0xD6, 7: 0xD7, 8: 0xD8, 9: 0xD9, 10: 0xDA,
        11: 0xDB, 12: 0xDC
    }
    
    # Range mappings
    RANGE_NAMES = {
        2.5: '2.5m',
        1.5: '1.5m', 
        6.5: '6.5m'
    }
    
    # Default values
    DEFAULT_VALUES = {
        'energy1': 3, 'time1': 2, 'threshold1': 2,  # 2.5m range
        'energy2': 1, 'time2': 0, 'threshold2': 2,  # 1.5m range
        'energy3': 5, 'time3': 6, 'threshold3': 2   # 6.5m range
    }
    
    FIXED_PARAMS = (0x2C, 0x40)
    
    def __init__(self, device_path: str = '/dev/ttyUS', baudrate: int = 115200, timeout: int = 3):
        """
        Initialize the KS236 energy setter
        
        Args:
            device_path: Serial device path
            baudrate: Communication baudrate
            timeout: Read timeout in seconds
        """
        self.device_path = device_path
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_port = None
        
    def calculate_bcc(self, data: bytes) -> int:
        """Calculate BCC checksum (XOR of all bytes)"""
        bcc = 0
        for byte in data:
            bcc ^= byte
        return bcc
    
    def connect(self) -> bool:
        """Establish serial connection"""
        try:
            self.serial_port = serial.Serial(
                port=self.device_path,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                write_timeout=1
            )
            print(f"✓ Connected to {self.device_path} at {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            print(f"✗ Failed to connect to {self.device_path}: {e}")
            return False
    
    def disconnect(self):
        """Close serial connection"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            print("✓ Serial connection closed")
    
    def read_probe_params(self, probe_num: int) -> Optional[Dict[str, int]]:
        """
        Read current probe parameters
        
        Args:
            probe_num: Probe number (1-12)
            
        Returns:
            Dictionary with current parameters or None if failed
        """
        if probe_num not in self.PROBE_QUERY_PARAMS:
            print(f"✗ Invalid probe number: {probe_num}")
            return None
        
        # Create query command
        param = self.PROBE_QUERY_PARAMS[probe_num]
        bcc = self.ADDR_CODE ^ self.CMD_CODE ^ param
        command = bytes([self.ADDR_CODE, self.CMD_CODE, param, bcc])
        
        try:
            # Send query
            self.serial_port.reset_input_buffer()
            self.serial_port.write(command)
            self.serial_port.flush()
            
            time.sleep(0.2)
            
            # Read response
            response = self.serial_port.read(15)
            
            if len(response) == 15:
                # Validate response
                if response[0] == self.ADDR_CODE and response[1] == self.CMD_CODE:
                    return {
                        'energy1': response[3], 'time1': response[4], 'threshold1': response[5],
                        'energy2': response[6], 'time2': response[7], 'threshold2': response[8],
                        'energy3': response[9], 'time3': response[10], 'threshold3': response[11]
                    }
            
            print(f"✗ Invalid response from probe {probe_num}")
            return None
            
        except Exception as e:
            print(f"✗ Error reading probe {probe_num}: {e}")
            return None
    
    def set_probe_params(self, probe_num: int, energy1: int, time1: int, threshold1: int,
                        energy2: int, time2: int, threshold2: int,
                        energy3: int, time3: int, threshold3: int,
                        permanent: bool = False, max_retries: int = 3) -> bool:
        """
        Set probe energy parameters
        
        Args:
            probe_num: Probe number (1-12)
            energy1-threshold3: Parameters for three ranges
            permanent: True for permanent modification, False for temporary
            max_retries: Maximum retry attempts
            
        Returns:
            True if setting successful
        """
        if probe_num not in self.PROBE_TEMP_PARAMS:
            print(f"✗ Invalid probe number: {probe_num}")
            return False
        
        # Validate parameter ranges
        if not (0 <= energy1 <= 7 and 0 <= energy2 <= 7 and 0 <= energy3 <= 7):
            print("✗ Energy values must be in range 0-7")
            return False
        if not (0 <= time1 <= 7 and 0 <= time2 <= 7 and 0 <= time3 <= 7):
            print("✗ Time values must be in range 0-7")
            return False
        if not (0 <= threshold1 <= 3 and 0 <= threshold2 <= 3 and 0 <= threshold3 <= 3):
            print("✗ Threshold values must be in range 0-3")
            return False
        
        # Select probe parameter code
        probe_params = self.PROBE_PERM_PARAMS if permanent else self.PROBE_TEMP_PARAMS
        param1 = probe_params[probe_num]
        
        # Create command
        command = bytes([
            self.ADDR_CODE, self.CMD_CODE, param1,
            energy1, time1, threshold1,
            energy2, time2, threshold2,
            energy3, time3, threshold3,
            self.FIXED_PARAMS[0], self.FIXED_PARAMS[1]
        ])
        
        # Calculate BCC
        bcc = self.calculate_bcc(command)
        full_command = command + bytes([bcc])
        
        print(f"Setting probe {probe_num} ({'permanent' if permanent else 'temporary'}):")
        print(f"  Command: {' '.join(f'{b:02X}' for b in full_command)}")
        print(f"  2.5m range: E{energy1}/T{time1}/Th{threshold1}")
        print(f"  1.5m range: E{energy2}/T{time2}/Th{threshold2}")
        print(f"  6.5m range: E{energy3}/T{time3}/Th{threshold3}")
        
        # Send command with retries
        for attempt in range(max_retries):
            try:
                self.serial_port.reset_input_buffer()
                bytes_sent = self.serial_port.write(full_command)
                self.serial_port.flush()
                
                if bytes_sent != len(full_command):
                    print(f"Warning: Only sent {bytes_sent}/{len(full_command)} bytes")
                    continue
                
                time.sleep(0.5)
                
                # Read response (expect 5 bytes)
                response = self.serial_port.read(5)
                
                if len(response) >= 5:
                    if response[0] == self.ADDR_CODE and response[1] == self.CMD_CODE:
                        status = response[3]
                        if status == 0x00:
                            print("✓ Setting successful")
                            return True
                        elif status == 0x02:
                            print("✗ Parameter error")
                            return False
                        elif status == 0xFF:
                            print("✗ Setting failed")
                            return False
                        else:
                            print(f"✗ Unknown status: 0x{status:02X}")
                    else:
                        print("✗ Invalid response format")
                else:
                    print(f"✗ Invalid response length: {len(response)} bytes")
                
                if attempt < max_retries - 1:
                    print(f"Retrying... (attempt {attempt + 2}/{max_retries})")
                    time.sleep(0.3)
                    
            except Exception as e:
                print(f"Error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.3)
        
        print(f"✗ Failed to set probe {probe_num} after {max_retries} attempts")
        return False
    
    def set_range_energy(self, probe_num: int, range_m: float, energy: int, 
                        time_val: Optional[int] = None, threshold: Optional[int] = None,
                        permanent: bool = False, verify: bool = True) -> bool:
        """
        Set energy for specific range of a probe
        
        Args:
            probe_num: Probe number (1-12)
            range_m: Range in meters (2.5, 1.5, or 6.5)
            energy: Energy value (0-7)
            time_val: Time value (0-7), None to keep current
            threshold: Threshold value (0-3), None to keep current
            permanent: True for permanent modification
            verify: True to verify setting after change
            
        Returns:
            True if setting successful
        """
        if range_m not in self.RANGE_NAMES:
            print(f"✗ Invalid range: {range_m}. Must be 2.5, 1.5, or 6.5")
            return False
        
        # Read current parameters
        print(f"Reading current parameters for probe {probe_num}...")
        current = self.read_probe_params(probe_num)
        if not current:
            print(f"✗ Failed to read current parameters for probe {probe_num}")
            return False
        
        print(f"Current parameters:")
        print(f"  2.5m range: E{current['energy1']}/T{current['time1']}/Th{current['threshold1']}")
        print(f"  1.5m range: E{current['energy2']}/T{current['time2']}/Th{current['threshold2']}")
        print(f"  6.5m range: E{current['energy3']}/T{current['time3']}/Th{current['threshold3']}")
        
        # Prepare new parameters
        new_params = current.copy()
        
        if range_m == 2.5:
            new_params['energy1'] = energy
            if time_val is not None:
                new_params['time1'] = time_val
            if threshold is not None:
                new_params['threshold1'] = threshold
        elif range_m == 1.5:
            new_params['energy2'] = energy
            if time_val is not None:
                new_params['time2'] = time_val
            if threshold is not None:
                new_params['threshold2'] = threshold
        elif range_m == 6.5:
            new_params['energy3'] = energy
            if time_val is not None:
                new_params['time3'] = time_val
            if threshold is not None:
                new_params['threshold3'] = threshold
        
        print(f"\nSetting {self.RANGE_NAMES[range_m]} range energy to {energy}...")
        
        # Set parameters
        success = self.set_probe_params(
            probe_num,
            new_params['energy1'], new_params['time1'], new_params['threshold1'],
            new_params['energy2'], new_params['time2'], new_params['threshold2'],
            new_params['energy3'], new_params['time3'], new_params['threshold3'],
            permanent=permanent
        )
        
        if success and verify:
            print(f"\nVerifying changes...")
            time.sleep(0.5)
            
            updated = self.read_probe_params(probe_num)
            if updated:
                print(f"Updated parameters:")
                print(f"  2.5m range: E{updated['energy1']}/T{updated['time1']}/Th{updated['threshold1']}")
                print(f"  1.5m range: E{updated['energy2']}/T{updated['time2']}/Th{updated['threshold2']}")
                print(f"  6.5m range: E{updated['energy3']}/T{updated['time3']}/Th{updated['threshold3']}")
                
                # Check if change was applied
                if range_m == 2.5 and updated['energy1'] == energy:
                    print(f"🎉 Successfully set 2.5m energy to {energy}")
                    return True
                elif range_m == 1.5 and updated['energy2'] == energy:
                    print(f"🎉 Successfully set 1.5m energy to {energy}")
                    return True
                elif range_m == 6.5 and updated['energy3'] == energy:
                    print(f"🎉 Successfully set 6.5m energy to {energy}")
                    return True
                else:
                    print(f"⚠️ Setting command succeeded but energy value not updated")
                    return False
            else:
                print(f"⚠️ Setting succeeded but verification failed")
                return success
        
        return success


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Set energy parameters for KS236 ultrasonic probes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set probe 1, 2.5m range energy to 2
  python ks236_energy_set.py --probe 1 --range 2.5 --energy 2
  
  # Set probe 5, 1.5m range energy to 3 with custom time and threshold
  python ks236_energy_set.py --probe 5 --range 1.5 --energy 3 --time 1 --threshold 1
  
  # Set probe 3, 6.5m range energy to 4 permanently
  python ks236_energy_set.py --probe 3 --range 6.5 --energy 4 --permanent
  
  # Set with custom device
  python ks236_energy_set.py --probe 2 --range 2.5 --energy 1 --device /dev/ttyUSB0
        """
    )
    
    parser.add_argument(
        '--probe', '-p',
        type=int,
        required=True,
        choices=range(1, 13),
        help='Probe number (1-12)'
    )
    
    parser.add_argument(
        '--range', '-r',
        type=float,
        required=True,
        choices=[2.5, 1.5, 6.5],
        help='Range in meters (2.5, 1.5, or 6.5)'
    )
    
    parser.add_argument(
        '--energy', '-e',
        type=int,
        required=True,
        choices=range(0, 8),
        help='Energy value (0-7, higher = longer range)'
    )
    
    parser.add_argument(
        '--time', '-t',
        type=int,
        choices=range(0, 8),
        help='Time value (0-7, higher = larger blind zone)'
    )
    
    parser.add_argument(
        '--threshold', '-th',
        type=int,
        choices=range(0, 4),
        help='Threshold value (0-3, lower = longer range)'
    )
    
    parser.add_argument(
        '--permanent',
        action='store_true',
        help='Make permanent changes (default: temporary)'
    )
    
    parser.add_argument(
        '--device', '-d',
        default='/dev/ttyUS',
        help='Serial device path (default: /dev/ttyUS)'
    )
    
    parser.add_argument(
        '--baudrate', '-b',
        type=int,
        default=115200,
        help='Baudrate (default: 115200)'
    )
    
    parser.add_argument(
        '--no-verify',
        action='store_true',
        help='Skip verification after setting'
    )
    
    args = parser.parse_args()
    
    # Create setter instance
    setter = KS236EnergySetter(
        device_path=args.device,
        baudrate=args.baudrate
    )
    
    try:
        if not setter.connect():
            sys.exit(1)
        
        print(f"\n{'='*60}")
        print(f"Setting KS236 Probe {args.probe} - {args.range}m Range Energy")
        print(f"{'='*60}")
        
        success = setter.set_range_energy(
            probe_num=args.probe,
            range_m=args.range,
            energy=args.energy,
            time_val=args.time,
            threshold=args.threshold,
            permanent=args.permanent,
            verify=not args.no_verify
        )
        
        setter.disconnect()
        
        if success:
            print(f"\n🎉 Operation completed successfully!")
            sys.exit(0)
        else:
            print(f"\n❌ Operation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Operation cancelled by user")
        setter.disconnect()
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        setter.disconnect()
        sys.exit(1)


if __name__ == "__main__":
    main() 
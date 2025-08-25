#!/usr/bin/env python3
"""
KS236 Ultrasonic Probe P-Value Parameter Setter
==============================================

This script sets P-value parameters for KS236 ultrasonic probes via RS485 communication.
Based on the RS485 P-control protocol documentation (rs485_p_control_v0.2.md).

P values (P1-P17) are core configuration parameters that control probe phase and beam angle:
- P1-P12: Main phase parameters controlling beam angle for different distance ranges
- P13-P17: Auxiliary parameters (recommended to keep at default values)

Features:
- Set P values for probes 1-9
- Support for individual P values or complete profiles
- Temporary or permanent setting modes
- Preset beam angle configurations
- Automatic verification after setting
- Command line interface with validation

Usage:
    python ks236_p_set.py --probe 1 --preset narrow    # Apply narrow beam preset
    python ks236_p_set.py --probe 5 --p1 15 --p2 15    # Set specific P values
    python ks236_p_set.py --probe 3 --profile custom.json --permanent  # Load from file

Author: Generated for Halo82 ultrasonic system
Date: 2025-06-30
"""

import serial
import time
import argparse
import sys
import json
from typing import Optional, Dict, List, Any, Union

class KS236PValueSetter:
    """KS236 ultrasonic probe P-value parameter setter"""
    
    # Protocol constants
    ADDR_CODE = 0xE8
    CMD_CODE = 0x99
    
    # Probe parameter mappings for setting
    PROBE_TEMP_PARAMS = {  # Temporary setting (0xC1-0xC9)
        1: 0xC1, 2: 0xC2, 3: 0xC3, 4: 0xC4, 5: 0xC5,
        6: 0xC6, 7: 0xC7, 8: 0xC8, 9: 0xC9
    }
    
    PROBE_PERM_PARAMS = {  # Permanent setting (0x81-0x89)
        1: 0x81, 2: 0x82, 3: 0x83, 4: 0x84, 5: 0x85,
        6: 0x86, 7: 0x87, 8: 0x88, 9: 0x89
    }
    
    PROBE_QUERY_PARAMS = {  # Query parameters (0xE1-0xE9)
        1: 0xE1, 2: 0xE2, 3: 0xE3, 4: 0xE4, 5: 0xE5,
        6: 0xE6, 7: 0xE7, 8: 0xE8, 9: 0xE9
    }
    
    # P-value descriptions and ranges
    P_DESCRIPTIONS = {
        'P1': '22.5 ~ 42.5 cm',
        'P2': '42.5 ~ 59.5 cm', 
        'P3': '59.5 ~ 76.5 cm',
        'P4': '76.5 ~ 110 cm',
        'P5': '110 ~ 144 cm',
        'P6': '144 ~ 178 cm',
        'P7': '178 ~ 212 cm',
        'P8': '212 ~ 246 cm',
        'P9': '246 ~ 280 cm',
        'P10': '280 ~ 348 cm',
        'P11': '348 ~ 416 cm',
        'P12': '416 cm+',
        'P13': 'Auxiliary param 13',
        'P14': 'Auxiliary param 14',
        'P15': 'Auxiliary param 15',
        'P16': 'Auxiliary param 16',
        'P17': 'Auxiliary param 17'
    }
    
    # Default values for all P parameters
    DEFAULT_VALUES = {
        'P1': 19, 'P2': 19, 'P3': 19, 'P4': 31, 'P5': 31, 'P6': 31,
        'P7': 31, 'P8': 31, 'P9': 31, 'P10': 31, 'P11': 31, 'P12': 31,
        'P13': 0, 'P14': 3, 'P15': 1, 'P16': 0, 'P17': 1
    }
    
    # Preset beam angle configurations (based on protocol documentation)
    BEAM_PRESETS = {
        'narrow': {
            'name': 'Narrow Beam (50°x16°)',
            'description': 'Maximum range, narrow field of view',
            'values': [31, 31, 31, 30, 26, 21, 16, 16, 13, 0, 0, 0, 0, 3, 1, 0, 1]
        },
        'medium': {
            'name': 'Medium Beam (90°x44°)',
            'description': 'Balanced range and coverage',
            'values': [24, 24, 23, 21, 18, 13, 10, 10, 6, 0, 0, 0, 0, 3, 1, 0, 1]
        },
        'wide': {
            'name': 'Wide Beam (100°x50°)',
            'description': 'Good coverage, moderate range',
            'values': [15, 15, 15, 15, 10, 10, 5, 5, 0, 0, 0, 0, 0, 3, 1, 0, 1]
        },
        'ultra_wide': {
            'name': 'Ultra Wide Beam (135°x64°)',
            'description': 'Maximum coverage, shorter range',
            'values': [10, 10, 7, 7, 6, 3, 2, 0, 0, 0, 0, 0, 0, 3, 1, 0, 1]
        },
        'default': {
            'name': 'Default Configuration',
            'description': 'Factory default P values',
            'values': [19, 19, 19, 31, 31, 31, 31, 31, 31, 31, 31, 31, 0, 3, 1, 0, 1]
        }
    }
    
    def __init__(self, device_path: str = '/dev/ttyUS', baudrate: int = 115200, timeout: int = 3):
        """
        Initialize the KS236 P-value setter
        
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
    
    def read_probe_p_values(self, probe_num: int) -> Optional[List[int]]:
        """
        Read current P values from probe
        
        Args:
            probe_num: Probe number (1-9)
            
        Returns:
            List of 17 P values or None if failed
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
            
            # Read response (21 bytes expected)
            response = self.serial_port.read(21)
            
            if len(response) == 21:
                # Validate response
                if response[0] == self.ADDR_CODE and response[1] == self.CMD_CODE:
                    # Validate BCC
                    expected_bcc = self.calculate_bcc(response[:-1])
                    if response[20] == expected_bcc:
                        return list(response[3:20])  # P1-P17 values
            
            print(f"✗ Invalid response from probe {probe_num}")
            return None
            
        except Exception as e:
            print(f"✗ Error reading probe {probe_num}: {e}")
            return None
    
    def set_probe_p_values(self, probe_num: int, p_values: List[int],
                          permanent: bool = False, max_retries: int = 3) -> bool:
        """
        Set probe P values
        
        Args:
            probe_num: Probe number (1-9)
            p_values: List of 17 P values (P1-P17)
            permanent: True for permanent modification, False for temporary
            max_retries: Maximum retry attempts
            
        Returns:
            True if setting successful
        """
        if probe_num not in self.PROBE_TEMP_PARAMS:
            print(f"✗ Invalid probe number: {probe_num}")
            return False
        
        if len(p_values) != 17:
            print(f"✗ Must provide exactly 17 P values, got {len(p_values)}")
            return False
        
        # Validate P value ranges
        for i, p_val in enumerate(p_values):
            if not (0 <= p_val <= 31):
                print(f"✗ P{i+1} value {p_val} out of range (0-31)")
                return False
        
        # Select probe parameter code
        probe_params = self.PROBE_PERM_PARAMS if permanent else self.PROBE_TEMP_PARAMS
        param1 = probe_params[probe_num]
        
        # Create command
        command = bytes([self.ADDR_CODE, self.CMD_CODE, param1] + p_values)
        
        # Calculate BCC
        bcc = self.calculate_bcc(command)
        full_command = command + bytes([bcc])
        
        print(f"Setting probe {probe_num} ({'permanent' if permanent else 'temporary'}):")
        print(f"  Command: {' '.join(f'{b:02X}' for b in full_command)}")
        print(f"  Main phase (P1-P12): {p_values[:12]}")
        print(f"  Auxiliary (P13-P17): {p_values[12:]}")
        
        # Send command with retries
        for attempt in range(max_retries):
            try:
                self.serial_port.reset_input_buffer()
                bytes_sent = self.serial_port.write(full_command)
                self.serial_port.flush()
                
                if bytes_sent != len(full_command):
                    print(f"Warning: Only sent {bytes_sent}/{len(full_command)} bytes")
                    continue
                
                time.sleep(0.5)  # Wait for processing (especially for permanent writes)
                
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
    
    def set_individual_p_values(self, probe_num: int, p_updates: Dict[str, int],
                               permanent: bool = False, verify: bool = True) -> bool:
        """
        Set specific P values while keeping others unchanged
        
        Args:
            probe_num: Probe number (1-9)
            p_updates: Dictionary like {'P1': 15, 'P3': 20}
            permanent: True for permanent modification
            verify: True to verify setting after change
            
        Returns:
            True if setting successful
        """
        # Read current P values
        print(f"Reading current P values for probe {probe_num}...")
        current_values = self.read_probe_p_values(probe_num)
        if not current_values:
            print(f"✗ Failed to read current P values for probe {probe_num}")
            return False
        
        print(f"Current P values: {current_values}")
        
        # Apply updates
        new_values = current_values.copy()
        for p_name, p_value in p_updates.items():
            if p_name not in self.P_DESCRIPTIONS:
                print(f"✗ Invalid P parameter: {p_name}")
                return False
            
            p_index = int(p_name[1:]) - 1  # P1 -> index 0
            if not (0 <= p_index <= 16):
                print(f"✗ Invalid P parameter index: {p_name}")
                return False
            
            if not (0 <= p_value <= 31):
                print(f"✗ P value {p_value} out of range (0-31) for {p_name}")
                return False
            
            old_value = new_values[p_index]
            new_values[p_index] = p_value
            print(f"  {p_name}: {old_value} → {p_value} ({self.P_DESCRIPTIONS[p_name]})")
        
        # Set new values
        success = self.set_probe_p_values(probe_num, new_values, permanent=permanent)
        
        if success and verify:
            print(f"\nVerifying changes...")
            time.sleep(0.5)
            
            updated_values = self.read_probe_p_values(probe_num)
            if updated_values:
                print(f"Updated P values: {updated_values}")
                
                # Check if changes were applied
                all_correct = True
                for p_name, expected_value in p_updates.items():
                    p_index = int(p_name[1:]) - 1
                    actual_value = updated_values[p_index]
                    if actual_value != expected_value:
                        print(f"⚠️ {p_name}: Expected {expected_value}, got {actual_value}")
                        all_correct = False
                
                if all_correct:
                    print(f"🎉 Successfully updated P values")
                    return True
                else:
                    print(f"⚠️ Some P values not updated correctly")
                    return False
            else:
                print(f"⚠️ Setting succeeded but verification failed")
                return success
        
        return success
    
    def apply_preset(self, probe_num: int, preset_name: str,
                    permanent: bool = False, verify: bool = True) -> bool:
        """
        Apply a preset beam angle configuration
        
        Args:
            probe_num: Probe number (1-9)
            preset_name: Name of preset configuration
            permanent: True for permanent modification
            verify: True to verify setting after change
            
        Returns:
            True if setting successful
        """
        if preset_name not in self.BEAM_PRESETS:
            print(f"✗ Unknown preset: {preset_name}")
            print(f"Available presets: {list(self.BEAM_PRESETS.keys())}")
            return False
        
        preset = self.BEAM_PRESETS[preset_name]
        print(f"Applying preset '{preset['name']}' to probe {probe_num}")
        print(f"Description: {preset['description']}")
        
        success = self.set_probe_p_values(probe_num, preset['values'], permanent=permanent)
        
        if success and verify:
            print(f"\nVerifying preset application...")
            time.sleep(0.5)
            
            updated_values = self.read_probe_p_values(probe_num)
            if updated_values:
                if updated_values == preset['values']:
                    print(f"🎉 Successfully applied preset '{preset['name']}'")
                    return True
                else:
                    print(f"⚠️ Preset values not applied correctly")
                    return False
            else:
                print(f"⚠️ Preset application succeeded but verification failed")
                return success
        
        return success
    
    def load_profile_from_file(self, file_path: str) -> Optional[List[int]]:
        """
        Load P value profile from JSON file
        
        Args:
            file_path: Path to JSON file containing P values
            
        Returns:
            List of 17 P values or None if failed
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if 'p_values' in data and len(data['p_values']) == 17:
                p_values = data['p_values']
                # Validate ranges
                for i, p_val in enumerate(p_values):
                    if not (0 <= p_val <= 31):
                        print(f"✗ Invalid P{i+1} value {p_val} in file (must be 0-31)")
                        return None
                return p_values
            else:
                print(f"✗ File must contain 'p_values' array with 17 values")
                return None
                
        except Exception as e:
            print(f"✗ Error loading profile from {file_path}: {e}")
            return None
    
    def save_profile_to_file(self, p_values: List[int], file_path: str, 
                           name: str = "", description: str = "") -> bool:
        """
        Save P value profile to JSON file
        
        Args:
            p_values: List of 17 P values
            file_path: Output file path
            name: Profile name
            description: Profile description
            
        Returns:
            True if successful
        """
        try:
            profile = {
                'name': name,
                'description': description,
                'p_values': p_values,
                'created': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(file_path, 'w') as f:
                json.dump(profile, f, indent=2)
            
            print(f"✓ Profile saved to {file_path}")
            return True
            
        except Exception as e:
            print(f"✗ Error saving profile to {file_path}: {e}")
            return False
    
    def list_presets(self):
        """Display available beam angle presets"""
        print("Available Beam Angle Presets:")
        print("=" * 50)
        
        for preset_name, preset_data in self.BEAM_PRESETS.items():
            print(f"{preset_name:12}: {preset_data['name']}")
            print(f"{'':12}  {preset_data['description']}")
            print(f"{'':12}  P1-P12: {preset_data['values'][:12]}")
            print()

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Set P-value parameters for KS236 ultrasonic probes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply narrow beam preset to probe 1
  python ks236_p_set.py --probe 1 --preset narrow
  
  # Set specific P values for probe 5
  python ks236_p_set.py --probe 5 --p1 15 --p2 15 --p3 12
  
  # Apply custom profile permanently
  python ks236_p_set.py --probe 3 --profile custom.json --permanent
  
  # Set single P value temporarily
  python ks236_p_set.py --probe 2 --p4 25
  
  # List available presets
  python ks236_p_set.py --list-presets
        """
    )
    
    parser.add_argument(
        '--probe', '-p',
        type=int,
        choices=range(1, 10),
        help='Probe number (1-9)'
    )
    
    parser.add_argument(
        '--preset',
        choices=list(KS236PValueSetter.BEAM_PRESETS.keys()),
        help='Apply beam angle preset'
    )
    
    parser.add_argument(
        '--profile',
        help='Load P values from JSON profile file'
    )
    
    # Individual P value arguments
    for i in range(1, 18):
        parser.add_argument(
            f'--p{i}',
            type=int,
            metavar=f'0-31',
            help=f'Set P{i} value (0-31)'
        )
    
    parser.add_argument(
        '--permanent',
        action='store_true',
        help='Make changes permanent (stored in EEPROM)'
    )
    
    parser.add_argument(
        '--no-verify',
        action='store_true',
        help='Skip verification after setting'
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
        help='Serial baudrate (default: 115200)'
    )
    
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        default=3,
        help='Read timeout in seconds (default: 3)'
    )
    
    parser.add_argument(
        '--save-profile',
        help='Save current probe P values to JSON file'
    )
    
    parser.add_argument(
        '--list-presets',
        action='store_true',
        help='List available beam angle presets'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Handle special commands that don't require connection
    if args.list_presets:
        setter = KS236PValueSetter()
        setter.list_presets()
        return
    
    # Validate required arguments
    if not args.probe:
        print("✗ Probe number is required (use --probe)")
        sys.exit(1)
    
    # Count operation types
    operations = sum([
        bool(args.preset),
        bool(args.profile),
        any(getattr(args, f'p{i}') is not None for i in range(1, 18)),
        bool(args.save_profile)
    ])
    
    if operations == 0:
        print("✗ No operation specified. Use --preset, --profile, --p1-p17, or --save-profile")
        sys.exit(1)
    elif operations > 1:
        print("✗ Only one operation allowed at a time")
        sys.exit(1)
    
    # Create setter instance
    setter = KS236PValueSetter(
        device_path=args.device,
        baudrate=args.baudrate,
        timeout=args.timeout
    )
    
    try:
        # Connect
        if not setter.connect():
            sys.exit(1)
        
        verify = not args.no_verify
        
        if args.save_profile:
            # Save current values to file
            print(f"Reading current P values from probe {args.probe}...")
            current_values = setter.read_probe_p_values(args.probe)
            if current_values:
                success = setter.save_profile_to_file(
                    current_values, 
                    args.save_profile,
                    f"Probe {args.probe} Profile",
                    f"P values from probe {args.probe} saved on {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                sys.exit(0 if success else 1)
            else:
                print(f"✗ Failed to read P values from probe {args.probe}")
                sys.exit(1)
        
        elif args.preset:
            # Apply preset
            success = setter.apply_preset(
                args.probe, args.preset, 
                permanent=args.permanent, verify=verify
            )
            
        elif args.profile:
            # Load and apply profile
            p_values = setter.load_profile_from_file(args.profile)
            if p_values:
                success = setter.set_probe_p_values(
                    args.probe, p_values,
                    permanent=args.permanent
                )
                if success and verify:
                    # Verify profile application
                    time.sleep(0.5)
                    updated = setter.read_probe_p_values(args.probe)
                    if updated == p_values:
                        print("🎉 Profile applied successfully")
                    else:
                        print("⚠️ Profile not applied correctly")
                        success = False
            else:
                success = False
        
        else:
            # Set individual P values
            p_updates = {}
            for i in range(1, 18):
                value = getattr(args, f'p{i}')
                if value is not None:
                    if 0 <= value <= 31:
                        p_updates[f'P{i}'] = value
                    else:
                        print(f"✗ P{i} value {value} out of range (0-31)")
                        sys.exit(1)
            
            success = setter.set_individual_p_values(
                args.probe, p_updates,
                permanent=args.permanent, verify=verify
            )
        
        # Exit with appropriate code
        if success:
            print(f"\n✓ Operation completed successfully")
            sys.exit(0)
        else:
            print(f"\n✗ Operation failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠ Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        setter.disconnect()

if __name__ == "__main__":
    main() 
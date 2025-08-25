#!/usr/bin/env python3
"""
KS236 Ultrasonic Probe P-Value Reader
=====================================

This script reads P-value parameters from KS236 ultrasonic probes via RS485 communication.
Based on the RS485 P-control protocol documentation (rs485_p_control_v0.2.md).

P values (P1-P17) are core configuration parameters that control probe phase and beam angle:
- P1-P12: Main phase parameters controlling beam angle for different distance ranges
- P13-P17: Auxiliary parameters (usually kept at default values)

Features:
- Reads P values from probes 1-9
- Supports retry mechanism for reliable communication
- Validates BCC checksums
- Provides detailed output and error handling
- Shows distance range mapping for each P parameter

Usage:
    python ks236_p_get.py [--device /dev/ttyUS] [--baudrate 115200] [--timeout 3]

Author: Generated for Halo82 ultrasonic system
Date: 2025-06-30
"""

import serial
import time
import argparse
import sys
from typing import Optional, Dict, List, Any

class KS236PValueReader:
    """KS236 ultrasonic probe P-value parameter reader"""
    
    # Protocol constants
    ADDR_CODE = 0xE8
    CMD_CODE = 0x99
    PROBE_PARAMS = {
        1: 0xE1, 2: 0xE2, 3: 0xE3, 4: 0xE4, 5: 0xE5,
        6: 0xE6, 7: 0xE7, 8: 0xE8, 9: 0xE9
    }
    EXPECTED_RESPONSE_LENGTH = 21
    
    # P-value descriptions and distance ranges
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
    
    # Default values for auxiliary parameters
    DEFAULT_AUX_VALUES = {
        'P13': 0x00, 'P14': 0x03, 'P15': 0x01, 'P16': 0x00, 'P17': 0x01
    }
    
    def __init__(self, device_path: str = '/dev/ttyUS', baudrate: int = 115200, timeout: int = 3):
        """
        Initialize the KS236 P-value reader
        
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
        """
        Calculate BCC checksum (XOR of all bytes)
        
        Args:
            data: Bytes to calculate checksum for
            
        Returns:
            BCC checksum value
        """
        bcc = 0
        for byte in data:
            bcc ^= byte
        return bcc
    
    def create_query_command(self, probe_num: int) -> bytes:
        """
        Create RS485 query command for specified probe
        
        Args:
            probe_num: Probe number (1-9)
            
        Returns:
            Command bytes to send
            
        Raises:
            ValueError: If probe number is invalid
        """
        if probe_num not in self.PROBE_PARAMS:
            raise ValueError(f"Invalid probe number: {probe_num}. Must be 1-9.")
        
        param = self.PROBE_PARAMS[probe_num]
        bcc = self.ADDR_CODE ^ self.CMD_CODE ^ param
        
        return bytes([self.ADDR_CODE, self.CMD_CODE, param, bcc])
    
    def validate_response(self, response: bytes, expected_probe_num: int) -> bool:
        """
        Validate response format and checksum
        
        Args:
            response: Response bytes received
            expected_probe_num: Expected probe number
            
        Returns:
            True if response is valid
        """
        if len(response) != self.EXPECTED_RESPONSE_LENGTH:
            return False
        
        # Check address and command codes
        if response[0] != self.ADDR_CODE or response[1] != self.CMD_CODE:
            return False
        
        # Check probe parameter
        expected_param = self.PROBE_PARAMS[expected_probe_num]
        if response[2] != expected_param:
            return False
        
        # Validate BCC checksum
        expected_bcc = self.calculate_bcc(response[:-1])
        if response[-1] != expected_bcc:
            return False
        
        return True
    
    def parse_response(self, response: bytes, probe_num: int) -> Dict[str, Any]:
        """
        Parse response data into structured format
        
        Args:
            response: Response bytes
            probe_num: Probe number
            
        Returns:
            Dictionary with parsed P-value parameters
        """
        p_values = response[3:20]  # P1-P17 are bytes 3-19
        
        result = {
            'probe_num': probe_num,
            'probe_id': f"0x{response[2]:02X}",
            'main_phase_params': {},
            'auxiliary_params': {},
            'bcc': f"0x{response[20]:02X}",
            'raw_response': ' '.join(f'{b:02X}' for b in response)
        }
        
        # Parse main phase parameters P1-P12
        for i in range(12):
            p_name = f'P{i+1}'
            result['main_phase_params'][p_name] = {
                'value': p_values[i],
                'hex': f'0x{p_values[i]:02X}', 
                'range': self.P_DESCRIPTIONS[p_name]
            }
        
        # Parse auxiliary parameters P13-P17
        for i in range(12, 17):
            p_name = f'P{i+1}'
            result['auxiliary_params'][p_name] = {
                'value': p_values[i],
                'hex': f'0x{p_values[i]:02X}',
                'description': self.P_DESCRIPTIONS[p_name],
                'default': f'0x{self.DEFAULT_AUX_VALUES[p_name]:02X}',
                'is_default': p_values[i] == self.DEFAULT_AUX_VALUES[p_name]
            }
        
        return result
    
    def query_probe(self, probe_num: int, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Query single probe with retry mechanism
        
        Args:
            probe_num: Probe number (1-9)
            max_retries: Maximum retry attempts
            
        Returns:
            Parsed probe data or None if failed
        """
        command = self.create_query_command(probe_num)
        
        for attempt in range(max_retries):
            try:
                # Clear input buffer
                self.serial_port.reset_input_buffer()
                
                # Send command
                bytes_sent = self.serial_port.write(command)
                self.serial_port.flush()
                
                if bytes_sent != len(command):
                    print(f"Warning: Probe {probe_num} attempt {attempt + 1} - only sent {bytes_sent}/{len(command)} bytes")
                    continue
                
                # Wait for response (recommended 100ms delay)
                time.sleep(0.1 + attempt * 0.05)  # Progressive delay
                
                # Read response
                response = self.serial_port.read(self.EXPECTED_RESPONSE_LENGTH)
                
                if len(response) == self.EXPECTED_RESPONSE_LENGTH:
                    if self.validate_response(response, probe_num):
                        return self.parse_response(response, probe_num)
                    else:
                        print(f"Warning: Probe {probe_num} attempt {attempt + 1} - invalid response format")
                elif len(response) > 0:
                    print(f"Warning: Probe {probe_num} attempt {attempt + 1} - incomplete response ({len(response)} bytes)")
                else:
                    print(f"Warning: Probe {probe_num} attempt {attempt + 1} - no response")
                
                # Wait before retry
                if attempt < max_retries - 1:
                    time.sleep(0.2)
                    
            except Exception as e:
                print(f"Error querying probe {probe_num} attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.2)
        
        return None
    
    def connect(self) -> bool:
        """
        Establish serial connection
        
        Returns:
            True if connection successful
        """
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
    
    def read_all_probes(self) -> List[Dict[str, Any]]:
        """
        Read P values from all probes (1-9)
        
        Returns:
            List of probe data dictionaries
        """
        results = []
        failed_probes = []
        
        print("Reading P values from probes 1-9...")
        print("=" * 60)
        
        for probe_num in range(1, 10):
            print(f"Querying probe {probe_num}...")
            result = self.query_probe(probe_num)
            
            if result:
                results.append(result)
                print(f"✓ Probe {probe_num}: Successfully read P values")
            else:
                failed_probes.append(probe_num)
                print(f"✗ Probe {probe_num}: Failed to read P values")
            
            # Inter-probe delay
            time.sleep(0.1)
        
        print("=" * 60)
        
        if failed_probes:
            print(f"Failed to read from probes: {failed_probes}")
        
        return results
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """
        Print summary of all probe P values
        
        Args:
            results: List of probe data from read_all_probes()
        """
        if not results:
            print("No probe data to display.")
            return
        
        print(f"\nP-VALUE SUMMARY ({len(results)} probes)")
        print("=" * 80)
        
        # Check if all probes have identical P values
        if len(results) > 1:
            first_probe = results[0]
            all_identical = True
            for result in results[1:]:
                for p_name in first_probe['main_phase_params']:
                    if result['main_phase_params'][p_name]['value'] != first_probe['main_phase_params'][p_name]['value']:
                        all_identical = False
                        break
                if not all_identical:
                    break
            
            if all_identical:
                print("✓ All probes have identical P-value configuration")
                print()
        
        # Display detailed P values for first probe or all if different
        display_probes = [results[0]] if len(results) > 1 and all_identical else results
        
        for result in display_probes:
            probe_num = result['probe_num']
            print(f"PROBE {probe_num} P-VALUES:")
            print("-" * 40)
            
            # Main phase parameters
            print("Main Phase Parameters (Control beam angle for distance ranges):")
            for p_name, p_data in result['main_phase_params'].items():
                print(f"  {p_name:3}: {p_data['value']:2d} ({p_data['hex']}) - {p_data['range']}")
            
            # Auxiliary parameters
            print("\nAuxiliary Parameters:")
            for p_name, p_data in result['auxiliary_params'].items():
                status = "✓ DEFAULT" if p_data['is_default'] else "⚠ CUSTOM"
                print(f"  {p_name:3}: {p_data['value']:2d} ({p_data['hex']}) - {p_data['description']} [{status}]")
            
            print(f"\nRaw Response: {result['raw_response']}")
            print()
        
        # If all identical, show which probes are active
        if len(results) > 1 and all_identical:
            active_probes = [r['probe_num'] for r in results]
            print(f"Active probes with this configuration: {active_probes}")
            print()
        
        # Analysis
        self.analyze_configuration(results[0] if all_identical else None)
    
    def analyze_configuration(self, sample_result: Optional[Dict[str, Any]]):
        """
        Analyze P-value configuration and provide insights
        
        Args:
            sample_result: Sample probe result for analysis (if all identical)
        """
        if not sample_result:
            print("Configuration Analysis: Skipped (probes have different configurations)")
            return
            
        print("CONFIGURATION ANALYSIS:")
        print("-" * 40)
        
        main_params = sample_result['main_phase_params']
        
        # Analyze beam focus pattern
        p1_3_avg = sum(main_params[f'P{i}']['value'] for i in range(1, 4)) / 3
        p4_12_avg = sum(main_params[f'P{i}']['value'] for i in range(4, 13)) / 9
        
        print(f"Close-range focus (P1-P3 avg): {p1_3_avg:.1f}")
        print(f"Long-range focus (P4-P12 avg): {p4_12_avg:.1f}")
        
        if p4_12_avg > p1_3_avg + 5:
            print("→ Configuration optimized for LONG-RANGE detection")
        elif p1_3_avg > p4_12_avg + 5:
            print("→ Configuration optimized for CLOSE-RANGE detection")
        else:
            print("→ Balanced configuration for mixed-range detection")
        
        # Check for maximum focus
        max_focus_params = [p for p, data in main_params.items() if data['value'] == 31]
        if max_focus_params:
            print(f"Maximum focus (P=31) applied to: {', '.join(max_focus_params)}")
        
        # Check auxiliary parameters
        aux_params = sample_result['auxiliary_params']
        custom_aux = [p for p, data in aux_params.items() if not data['is_default']]
        if custom_aux:
            print(f"⚠ Custom auxiliary parameters: {', '.join(custom_aux)}")
        else:
            print("✓ All auxiliary parameters at default values")

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Read P-value parameters from KS236 ultrasonic probes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ks236_p_get.py                    # Read from default device
  python ks236_p_get.py --device /dev/ttyUSB0  # Use specific device
  python ks236_p_get.py --timeout 5        # Increase timeout
        """
    )
    
    parser.add_argument('--device', '-d', 
                       default='/dev/ttyUS',
                       help='Serial device path (default: /dev/ttyUS)')
    
    parser.add_argument('--baudrate', '-b',
                       type=int, default=115200,
                       help='Serial baudrate (default: 115200)')
    
    parser.add_argument('--timeout', '-t',
                       type=int, default=3,
                       help='Read timeout in seconds (default: 3)')
    
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Create reader instance
    reader = KS236PValueReader(
        device_path=args.device,
        baudrate=args.baudrate,
        timeout=args.timeout
    )
    
    try:
        # Connect
        if not reader.connect():
            sys.exit(1)
        
        # Read all probes
        results = reader.read_all_probes()
        
        # Display results
        reader.print_summary(results)
        
        # Exit with appropriate code
        if results:
            print(f"\n✓ Successfully read P values from {len(results)} probes")
            sys.exit(0)
        else:
            print(f"\n✗ Failed to read P values from any probes")
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
        reader.disconnect()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
KS236 Ultrasonic Probe Energy Reader
====================================

This script reads energy parameters from KS236 ultrasonic probes via RS485 communication.
Based on the RS485 energy control protocol documentation.

Features:
- Reads energy data from probes 1-9
- Supports retry mechanism for reliable communication
- Validates BCC checksums
- Provides detailed output and error handling

Usage:
    python ks236_energy_get.py [--device /dev/ttyUSB0] [--baudrate 115200] [--timeout 3]

Author: Generated for Halo82 ultrasonic system
Date: 2025-06-30
"""

import serial
import time
import argparse
import sys
from typing import Optional, Dict, List, Any

class KS236EnergyReader:
    """KS236 ultrasonic probe energy parameter reader"""
    
    # Protocol constants
    ADDR_CODE = 0xE8
    CMD_CODE = 0x99
    PROBE_PARAMS = {
        1: 0xD1, 2: 0xD2, 3: 0xD3, 4: 0xD4, 5: 0xD5,
        6: 0xD6, 7: 0xD7, 8: 0xD8, 9: 0xD9
    }
    EXPECTED_RESPONSE_LENGTH = 15
    
    def __init__(self, device_path: str = '/dev/ttyUS', baudrate: int = 115200, timeout: int = 3):
        """
        Initialize the KS236 energy reader
        
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
            Dictionary with parsed energy parameters
        """
        return {
            'probe_num': probe_num,
            'probe_id': f"0x{response[2]:02X}",
            'range_2_5m': {
                'energy': response[3],
                'time': response[4],
                'threshold': response[5]
            },
            'range_1_5m': {
                'energy': response[6],
                'time': response[7],
                'threshold': response[8]
            },
            'range_6_5m': {
                'energy': response[9],
                'time': response[10],
                'threshold': response[11]
            },
            'fixed_params': {
                'param1': f"0x{response[12]:02X}",
                'param2': f"0x{response[13]:02X}"
            },
            'bcc': f"0x{response[14]:02X}",
            'raw_response': ' '.join(f'{b:02X}' for b in response)
        }
    
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
                
                # Wait for response
                time.sleep(0.1 + attempt * 0.1)  # Progressive delay
                
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
        Read energy parameters from all probes (1-9)
        
        Returns:
            List of probe data dictionaries
        """
        if not self.connect():
            return []
        
        results = []
        
        try:
            print("\n" + "="*60)
            print("Reading KS236 Ultrasonic Probe Energy Parameters")
            print("="*60)
            
            for probe_num in range(1, 10):
                print(f"\n--- Querying Probe {probe_num} ---")
                
                result = self.query_probe(probe_num)
                
                if result:
                    results.append(result)
                    print(f"✓ Probe {probe_num}: Success")
                    print(f"  2.5m range: E{result['range_2_5m']['energy']}/T{result['range_2_5m']['time']}/Th{result['range_2_5m']['threshold']}")
                    print(f"  1.5m range: E{result['range_1_5m']['energy']}/T{result['range_1_5m']['time']}/Th{result['range_1_5m']['threshold']}")
                    print(f"  6.5m range: E{result['range_6_5m']['energy']}/T{result['range_6_5m']['time']}/Th{result['range_6_5m']['threshold']}")
                else:
                    print(f"✗ Probe {probe_num}: Failed to read")
                
                # Inter-probe delay
                time.sleep(0.1)
            
        finally:
            self.disconnect()
        
        return results
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """
        Print formatted summary of results
        
        Args:
            results: List of probe data
        """
        if not results:
            print("\n❌ No probe data available")
            return
        
        print("\n" + "="*80)
        print("SUMMARY: KS236 Probe Energy Parameters")
        print("="*80)
        
        # Header
        print(f"{'Probe':<6} {'2.5m (E/T/Th)':<15} {'1.5m (E/T/Th)':<15} {'6.5m (E/T/Th)':<15} {'Status':<8}")
        print("-" * 80)
        
        # Data rows
        for result in results:
            probe_num = result['probe_num']
            r25 = result['range_2_5m']
            r15 = result['range_1_5m']
            r65 = result['range_6_5m']
            
            print(f"{probe_num:<6} "
                  f"{r25['energy']}/{r25['time']}/{r25['threshold']:<15} "
                  f"{r15['energy']}/{r15['time']}/{r15['threshold']:<15} "
                  f"{r65['energy']}/{r65['time']}/{r65['threshold']:<15} "
                  f"{'✓ OK':<8}")
        
        # Statistics
        total_probes = 9
        successful_probes = len(results)
        failed_probes = total_probes - successful_probes
        
        print("-" * 80)
        print(f"Success Rate: {successful_probes}/{total_probes} ({successful_probes/total_probes*100:.1f}%)")
        
        if failed_probes > 0:
            failed_nums = [i for i in range(1, 10) if i not in [r['probe_num'] for r in results]]
            print(f"Failed Probes: {', '.join(map(str, failed_nums))}")
        
        print("\nParameter Legend:")
        print("  E = Energy (0-7, higher = longer range)")
        print("  T = Time (0-7, higher = larger blind zone)")
        print("  Th = Threshold (0-3, lower = longer range)")


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Read energy parameters from KS236 ultrasonic probes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ks236_energy_get.py
  python ks236_energy_get.py --device /dev/ttyUSB0
  python ks236_energy_get.py --device /dev/ttyUSB1 --baudrate 9600
        """
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
        '--timeout', '-t',
        type=int,
        default=3,
        help='Read timeout in seconds (default: 3)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress detailed output, show only summary'
    )
    
    args = parser.parse_args()
    
    # Create reader instance
    reader = KS236EnergyReader(
        device_path=args.device,
        baudrate=args.baudrate,
        timeout=args.timeout
    )
    
    # Read all probes
    try:
        results = reader.read_all_probes()
        
        # Print summary
        if not args.quiet:
            reader.print_summary(results)
        
        # Return appropriate exit code
        if len(results) == 9:
            print(f"\n🎉 All probes read successfully!")
            sys.exit(0)
        elif len(results) > 0:
            print(f"\n⚠️  Partial success: {len(results)}/9 probes read")
            sys.exit(1)
        else:
            print(f"\n❌ Failed to read any probes")
            sys.exit(2)
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
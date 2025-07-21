#!/usr/bin/env python3
"""
Simple Bluetooth Scanner
Lists all Bluetooth devices with name and address
Kig ifter f.eks. Grain
"""

import asyncio
from bleak import BleakScanner

async def scan_devices(duration=10):
    """Scan for all Bluetooth devices and list them"""
    
    print(f"Scanning for Bluetooth devices for {duration} seconds...")
    print("-" * 50)
    
    devices = await BleakScanner.discover(timeout=duration)
    
    print(f"\nFound {len(devices)} devices:")
    print("-" * 50)
    
    for i, device in enumerate(devices, 1):
        name = device.name or "Unknown"
        address = device.address
        print(f"{i:2d}. {name:<30} {address}")
    
    print("-" * 50)

if __name__ == "__main__":
    import sys
    
    # Get scan duration from command line argument (default 10 seconds)
    duration = 10
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            print("Invalid duration, using 10 seconds")
    
    try:
        asyncio.run(scan_devices(duration))
    except KeyboardInterrupt:
        print("\nScan interrupted")
    except Exception as e:
        print(f"Error: {e}")

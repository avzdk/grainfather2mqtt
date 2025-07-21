# Grainfather Bluetooth Scanner

A Python script to scan for Grainfather brewing devices using Bluetooth Low Energy (BLE) on Raspberry Pi 4B.

https://github.com/kingpulsar/Grainfather-Bluetooth-Protocol

## Requirements

- Raspberry Pi 4B with Bluetooth enabled
- Python 3.7+
- Grainfather device with Bluetooth enabled

## Installation

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure Bluetooth is enabled on your Raspberry Pi:
   ```bash
   sudo systemctl enable bluetooth
   sudo systemctl start bluetooth
   ```

## Basic scan (10 seconds) for address:
```bash
python scan.py
```

## Usage

```bash
python gf2mqtt.py
```
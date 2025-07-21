#!/usr/bin/env python3
"""
Simpel Grainfather temperatur læser
Forbinder til Grainfather og læser temperaturen løbende
"""

import asyncio
import logging
import tomllib
from bleak import BleakClient
import paho.mqtt.client as mqtt  
from paho.mqtt.enums import CallbackAPIVersion
import uuid
import datetime
import json
import time

def load_config() -> dict:
    """Indlæser konfiguration fra config.toml"""
    with open('config.toml', 'rb') as f:
        config = tomllib.load(f)
    return config

CONFIG= load_config()

# Setup logging
logging.basicConfig(
    level=CONFIG['log_level'].upper(),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Grainfather Bluetooth UUIDs (fra protokol dokumentationen)
SERVICE_UUID = "0000cdd0-0000-1000-8000-00805f9b34fb"
READ_CHAR_UUID = "0003cdd1-0000-1000-8000-00805f9b0131"
WRITE_CHAR_UUID = "0003cdd2-0000-1000-8000-00805f9b0131"

def send_mqtt(mqtt_ip, data, topic="grainfather/data"):
    """Send data to MQTT broker"""
    try:
        # Create client instance (version 2.1 syntax)
        client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
        
        # Add metadata to data
        data['msg_uuid'] = str(uuid.uuid4())
        data['timestamp'] = str(datetime.datetime.now())
        
        # Connect to broker
        client.connect(mqtt_ip, 1883, 60)
        client.loop_start()
        
        # Publish message
        json_data = json.dumps(data)
        result = client.publish(topic, json_data, qos=1, retain=False)
        result.wait_for_publish()
        
        # Disconnect
        client.loop_stop()
        client.disconnect()
        
        logger.debug(f"MQTT data sent: {json_data}")
        
    except Exception as e:
        logger.error(f"MQTT send error: {e}")

class GrainfatherReader:
    def __init__(self, address, mqtt_ip):
        self.address = address
        self.mqtt_ip = mqtt_ip
        self.client = None
        self.running = False
        
        # Timer for MQTT sending (once per minute)
        self.last_mqtt_send = 0
        self.mqtt_interval = int(CONFIG['mqtt_delay'])  # seconds
        
        # Store latest data
        self.latest_temperature_data = None
        self.latest_status_data = None
        self.latest_timer_data = None

    def should_send_mqtt(self):
        """Check if enough time has passed to send MQTT data"""
        current_time = time.time()
        if current_time - self.last_mqtt_send >= self.mqtt_interval:
            self.last_mqtt_send = current_time
            return True
        return False
    
    def send_stored_data(self):
        """Send the latest stored data to MQTT"""
        if self.latest_temperature_data:
            send_mqtt(self.mqtt_ip, self.latest_temperature_data.copy())
            logger.debug("Sent temperature data to MQTT")
            
        if self.latest_status_data:
            send_mqtt(self.mqtt_ip, self.latest_status_data.copy())
            logger.debug("Sent status data to MQTT")
            
        if self.latest_timer_data:
            send_mqtt(self.mqtt_ip, self.latest_timer_data.copy())
            logger.debug("Sent timer data to MQTT")

    def notification_handler(self, sender, data):
        logger.debug(f"Raw data: {data}")
        """Håndterer notifikationer fra Grainfather"""
        try:
            message = data.decode('utf-8').strip()
            
            # X notifikationer indeholder temperatur data
            if message.startswith('X'):
                # Format: X{Target Temperature},{Current temperature}
                parts = message[1:].split(',')
                if len(parts) >= 2:
                    target_temp = parts[0]
                    current_temp = parts[1]
                    logger.info(f"Temperatur: {current_temp}°C | Mål: {target_temp}°C")
                    
                    # Store temperature data (don't send immediately)
                    self.latest_temperature_data = {
                        "device": "grainfather",
                        "type": "temperature",
                        "current_temp": float(current_temp),
                        "target_temp": float(target_temp)
                    }
            
            # Andre interessante notifikationer
            elif message.startswith('Y'):
                # Y{Heat Power},{Pump Status},{Auto Mode Status}...
                parts = message[1:].split(',')
                if len(parts) >= 3:
                    heat_power = parts[0]
                    pump_status = parts[1]
                    auto_mode = parts[2]
                    logger.info(f"Varme: {heat_power}% | Pumpe: {'ON' if pump_status == '1' else 'OFF'}")
                    
                    # Store status data (don't send immediately)
                    self.latest_status_data = {
                        "device": "grainfather",
                        "type": "status",
                        "heat_power": int(heat_power),
                        "pump_status": pump_status == '1',
                        "auto_mode": auto_mode == '1'
                    }
            
            elif message.startswith('T'):
                # Timer information
                parts = message[1:].split(',')
                if len(parts) >= 2:
                    timer_active = parts[0]
                    time_left = parts[1]
                    if timer_active == '1':
                        logger.info(f"Timer: {time_left} min tilbage")
                        
                        # Store timer data (don't send immediately)
                        self.latest_timer_data = {
                            "device": "grainfather",
                            "type": "timer",
                            "timer_active": True,
                            "time_left_minutes": int(time_left)
                        }
            
            # Check if it's time to send MQTT data
            if self.should_send_mqtt():
                logger.info("Sending MQTT data (1 minute interval)")
                self.send_stored_data()
                                
        except Exception as e:
            logger.error(f"Fejl ved parsing af besked: {e}")

    async def connect_and_read(self):
        """Opretter forbindelse og læser data løbende"""
        
        try:
            self.client = BleakClient(self.address)
            await self.client.connect()
            logger.info("Forbundet til Grainfather!")
            
            # Start notifikationer
            await self.client.start_notify(READ_CHAR_UUID, self.notification_handler)
            logger.info("Lytter efter data...")
            self.running = True
            
            # Hold forbindelsen åben og læs data
            while self.running:
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"Fejl: {e}")
        finally:
            if self.client and self.client.is_connected:
                await self.client.disconnect()
                logger.info("Afbrudt fra Grainfather")

    def stop(self):
        """Stopper læsningen"""
        self.running = False


async def main():
    """Hovedfunktion"""
    logger.info("Grainfather Temperatur Læser")
    logger.info("=" * 40)
    
    gf_address = CONFIG['gfaddr'] 
    logger.info(f"Grainfather adresse: {gf_address}")
    mqtt_ip = CONFIG['mqtt_ip']
    logger.info(f"MQTT IP: {mqtt_ip}")

    reader = GrainfatherReader(gf_address, mqtt_ip)

    try:
        await reader.connect_and_read()
    except KeyboardInterrupt:
        logger.info("\nStopper...")
        reader.stop()

if __name__ == "__main__":
    asyncio.run(main())

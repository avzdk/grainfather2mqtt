#!/usr/bin/env python3
"""
Simpel Grainfather temperatur læser
Forbinder til Grainfather og læser temperaturen løbende
"""

import asyncio
from cmath import log
import tomllib
from bleak import BleakClient
import paho.mqtt.client as mqtt
import uuid
import datetime
import json

# Grainfather Bluetooth UUIDs (fra protokol dokumentationen)
SERVICE_UUID = "0000cdd0-0000-1000-8000-00805f9b34fb"
READ_CHAR_UUID = "0003cdd1-0000-1000-8000-00805f9b0131"
WRITE_CHAR_UUID = "0003cdd2-0000-1000-8000-00805f9b0131"

class GrainfatherReader:
    def __init__(self, address):
        self.address = address
        self.client = None
        self.running = False

    def notification_handler(self, sender, data):
        print (data)
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
                    print(f"Temperatur : {current_temp}°C Mål: {target_temp}°C")
            
            # Andre interessante notifikationer
            elif message.startswith('Y'):
                # Y{Heat Power},{Pump Status},{Auto Mode Status}...
                parts = message[1:].split(',')
                if len(parts) >= 3:
                    heat_power = parts[0]
                    pump_status = parts[1]
                    auto_mode = parts[2]
                    print(f"Varme: {heat_power}% | 🔄 Pumpe: {'ON' if pump_status == '1' else 'OFF'}")
            
            elif message.startswith('T'):
                # Timer information
                parts = message[1:].split(',')
                if len(parts) >= 2:
                    timer_active = parts[0]
                    time_left = parts[1]
                    if timer_active == '1':
                        print(f"⏰ Timer: {time_left} min tilbage")
                        
        except Exception as e:
            print(f"Fejl ved parsing af besked: {e}")

    async def connect_and_read(self):
        """Opretter forbindelse og læser data løbende"""
        
        try:
            self.client = BleakClient(self.address)
            await self.client.connect()
            print("Forbundet til Grainfather!")
            
            # Start notifikationer
            await self.client.start_notify(READ_CHAR_UUID, self.notification_handler)
            print("Lytter efter data")
            self.running = True
            
            # Hold forbindelsen åben og læs data
            while self.running:
                await asyncio.sleep(5)
                
        except Exception as e:
            print(f"Fejl: {e}")
        finally:
            if self.client and self.client.is_connected:
                await self.client.disconnect()
                print("🔌 Afbrudt fra Grainfather")

    def stop(self):
        """Stopper læsningen"""
        self.running = False

def load_config() -> dict:
    """Indlæser konfiguration fra config.toml"""
    with open('config.toml', 'rb') as f:
        config = tomllib.load(f)
    return config

def sendMqtt(ip,data):
    mqtt_client = mqtt.Client("gf2mqtt")
    data['msg_uuid']=str(uuid.uuid4())
    data['time_send']=str(datetime.datetime.now())	
    mqtt_client.connect(ip)		
    response=mqtt_client.publish('grainfather/data',json.dumps(data),1,True)
    #log.debug(f"Succes: {response.rc}" )
    mqtt_client.disconnect()        

async def main():
    """Hovedfunktion"""
    print("Grainfather Temperatur Læser")
    print("=" * 40)
    
    CONFIG= load_config()
    gf_address = CONFIG['gfaddr'] 
    print(f"Grainfather adresse: {gf_address}")
        
    reader = GrainfatherReader(gf_address)

    mgtt_ip= CONFIG['mqtt_ip'] 
    


    try:
        await reader.connect_and_read()
    except KeyboardInterrupt:
        print("\n Stopper...")
        reader.stop()

if __name__ == "__main__":
    asyncio.run(main())

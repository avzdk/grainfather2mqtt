
import paho.mqtt.client as mqtt  
from paho.mqtt.enums import CallbackAPIVersion
# PAHO VERSION 2.1
import json
import uuid
import datetime
import time

def on_connect(client, userdata, flags, reason_code, properties):
    """Callback for when the client receives a CONNACK response from the server."""
    if reason_code == 0:
        print(f"Connected successfully")
    else:
        print(f"Failed to connect with result code {reason_code}")

def on_publish(client, userdata, mid, reason_code, properties):
    """Callback for when a message is published."""
    print(f"Message published successfully (mid: {mid})")

def sendMqtt(mqtt_ip, data, topic="grainfather/data"):
    """Send MQTT message - Version 2.1 compatible"""
    try:
        # Create client instance (version 2.1 syntax)
        client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
        
        # Set callbacks
        client.on_connect = on_connect
        client.on_publish = on_publish
        
        # Add metadata to data
        data['msg_uuid'] = str(uuid.uuid4())
        data['timestamp'] = str(datetime.datetime.now())
        
        # Connect to broker
        print(f"Connecting to MQTT broker at {mqtt_ip}...")
        client.connect(mqtt_ip, 1883, 60)
        
        # Start the network loop
        client.loop_start()
        
        # Wait a moment for connection
        time.sleep(1)
        
        # Publish message
        json_data = json.dumps(data)
        print(f"Publishing data: {json_data}")
        result = client.publish(topic, json_data, qos=1, retain=False)
        
        # Wait for publish to complete
        result.wait_for_publish()
        
        # Stop the loop and disconnect
        client.loop_stop()
        client.disconnect()
        print("Disconnected from MQTT broker")
        
    except Exception as e:
        print(f"Error sending MQTT message: {e}")

if __name__ == "__main__":
    mqtt_ip = "mqtt.home"
    
    # Test data
    data = {
        "temperature": 22.5, 
        "humidity": 60,
        "device": "test_sensor"
    }
    
    print("=== Simple MQTT Send Test ===")
    sendMqtt(mqtt_ip, data)
    print("Test completed!")
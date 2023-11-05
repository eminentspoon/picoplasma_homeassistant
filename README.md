# picoplasma_homeassistant
A Home Assistant compatible project for the Pimoroni Wireless Plasma kit

# Overview

Adds the capability of putting an MQTT supported light to Home Assistant using the [Pimoroni Wireless Plasma](https://shop.pimoroni.com/products/wireless-plasma-kit) kit. It will be exposed as a light and you can set brightness, hue / sat and state through the UI / automations. Based on Plasma Kit example from Pimoroni and using am umqtt client (from (RuiSantosdotmet)[https://github.com/RuiSantosdotme/ESP-MicroPython]) for MQTT integration.

# Dependencies

- You'll need to be running the Pimoroni Micropython (see store page listed in overview)
- Create a valid MQTT_CONFIG.py (see 'Configuration' section) on the device
- Create a valid WIFI_CONFIG.py (see 'Configuration' section) on the device
- Add the device to your Home Assistant configuration (see 'Home Assistant Setup')

# Configuration

## MQTT_CONFIG.py

You will need to create an MQTT_CONFIG.py at the root of your Pico that contains the configuration for your MQTT server. This should look like:

```python
MQTT_SERVICE = "my_server_name" # you might need to use IP address if DNS resolution is patchy
MQTT_PORT = 1883
MQTT_CLIENTID = "my_client_id"
```

Please note, the MQTT setup for this project is currently set for open authentication, if your MQTT server needs creds, alter the following line in main.py:

```python
client = MQTTClient(MQTT_CONFIG.MQTT_CLIENTID, MQTT_CONFIG.MQTT_SERVER, MQTT_CONFIG.MQTT_PORT, "username", "password", keepalive=3600)
```

## WIFI_CONFIG.py

You will need to create a WIFI_CONFIG.py at the root of your Pico that contains the configuration for your Wifi. This should look like:

```python
SSID = "your_ssid"
PSK = "your_password"
COUNTRY = "gb"
```

# Home Assistant Setup

In order to work with Home Assistant, you will need to add the device to the configuration.yaml on your installation. This should be populated under the ```mqtt:``` section (please note, you'll need to create a new configuration entry if you don't have this already but don't duplicate it, same goes for the ```light:``` section too). This should look like the following (ignoring comments):

```yaml
mqtt:
  light:
    - name: "Bookshelf Jar Light" # This is how it will be listed in Home Assistant
      qos: 1
      unique_id: "jarlight_01" # If you setup multiple, you will need to setup a unique id for each entry as well as altering topic names
      # All this topics will work with the default setup of main.py, if you want to run multiple, you will need to alter in both script and configuration in home assistant
      state_topic: "homeassistant/light/jar_light/state"
      command_topic: "homeassistant/light/jar_light/set"
      brightness_state_topic: "homeassistant/light/jar_light/brightness"
      brightness_command_topic: "homeassistant/light/jar_light/brightness/set"
      payload_on: "ON"
      payload_off: "OFF"
      hs_state_topic: "homeassistant/light/jar_light/color"
      hs_command_topic: "homeassistant/light/jar_light/color/set"
```

Once altered, you should check for any configuration problems under Developer Tools in Home Assistant and then restart to pick up the new changes.

# How to run

- Copy the files in this project to the device using your preferred method of getting Micropython scripts onto the device (e.g. Thonny etc.)
- Ensure that the configuration above is valid and populated
- Ensure that Home Assistant has been setup ready for the new device
- Fire it up and see whether you can control events correct from Home Assistant

# Configuration in main.py

There are a few pieces of configuration that you can set in the main.py file to tweak to your needs, these are:

- ```BRIGHTNESS``` - This is how bright you want the light to be by default when powering on from no power
- ```COLOUR_HUE``` - This is the hue that you want the light to be by default when powering on from no power
- ```COLOUR_SAT``` - This is the sat that you want the light to be by default when powering on from no power
- ```DEVICE_STATE``` - This is whether you want the device to be lit when you first power on from no power
- ```POLL_FREQUENCY``` - This is how frequently you want the device to ping Home Assistant with its state (checks for Wifi connection too as well as refreshing values in Home Assistant)

# Troubleshooting

There are plenty of logging messages output via console if you run with a connected COM port (e.g. run via Thonny hooked up to the Pico) which should hopefully point you in the right direction. If you're cycling white flashing lights, this is failing to connect to Wifi.

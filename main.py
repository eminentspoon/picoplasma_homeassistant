import WIFI_CONFIG
import MQTT_CONFIG
import time
import plasma
from umqtt.simple import MQTTClient
from network_manager import NetworkManager
from plasma import plasma_stick
import uasyncio
import math
import machine

# Set how many LEDs you have
NUM_LEDS = 50

# Update to change device defaults for first boot
# Then takes values from homeassistant integration
# 0 - 1 in .1 increments
BRIGHTNESS = 0.8
# 0 - 360
COLOUR_HUE = 44.0
# 0.0 - 100.0
COLOUR_SAT = 99.0
# Whether device is turned on
DEVICE_STATE = True

# Poll frequency to MQTT server
POLL_FREQUENCY = 600.0
# Last poll time
LAST_UPDATE = time.time()

# MQTT topics (replace jar_light in topic if running multiples)
STATE_TOPIC = b'homeassistant/light/jar_light/state'
COMMAND_TOPIC = b'homeassistant/light/jar_light/set'
BRIGHTNESS_STATE_TOPIC = b'homeassistant/light/jar_light/brightness'
BRIGHTNESS_COMMAND_TOPIC = b'homeassistant/light/jar_light/brightness/set'
HSL_STATE_TOPIC = b'homeassistant/light/jar_light/color'
HSL_COMMAND_TOPIC = b'homeassistant/light/jar_light/color/set'

MQTT_ON_COMMAND = "ON"
MQTT_OFF_COMMAND = "OFF"

def mqtt_connect():
        client = MQTTClient(MQTT_CONFIG.MQTT_CLIENTID, MQTT_CONFIG.MQTT_SERVER, MQTT_CONFIG.MQTT_PORT, keepalive=3600)
        client.connect()
        client.set_callback(subscription_callback)
        print('Connected to %s MQTT Broker'%(MQTT_CONFIG.MQTT_SERVER))
        return client

def subscription_callback(topic, msg):
    global DEVICE_STATE
    topic = topic.decode('utf-8')
    msg = msg.decode('utf-8')

    print("topic sub fire : {}".format(topic))
    print("message : {}".format(msg))
    
    if topic == BRIGHTNESS_COMMAND_TOPIC.decode("utf-8"):
        # handle brightness command
        print("handling brightness")
        amount = int(msg)
        handle_brightness(amount)
    
    if topic == HSL_COMMAND_TOPIC.decode("utf-8"):
        print("handling colour change")
        values = msg.split(",")
        
        handle_colour(round(float(values[0]),0), round(float(values[1]),0))
        
    if topic == COMMAND_TOPIC.decode("utf-8"):
        print("handling state")
        DEVICE_STATE = True if MQTT_ON_COMMAND == msg else False
        update_led_state()                

def reconnect():
   print('Failed to connect to the MQTT Broker. Reconnecting...')
   time.sleep(5)

def update_led_state():
    print("updating LEDs")
    brightnessToUse = BRIGHTNESS if DEVICE_STATE else 0

    for i in range(NUM_LEDS):
        led_strip.set_hsv(i, round(COLOUR_HUE / 360,1), round(COLOUR_SAT / 100,1), brightnessToUse)
    update_mqtt_state()

def update_mqtt_state():
    global LAST_UPDATE
    print("updating mqtt state")
    client.publish(STATE_TOPIC, MQTT_ON_COMMAND if DEVICE_STATE else MQTT_OFF_COMMAND)
    client.publish(BRIGHTNESS_STATE_TOPIC, str(math.floor(255*BRIGHTNESS)))
    client.publish(HSL_STATE_TOPIC, str(COLOUR_HUE)+","+str(COLOUR_SAT))
    LAST_UPDATE = time.time()

def handle_brightness(amount):
    global BRIGHTNESS
    converted = round(amount / 255, 1)
    if converted == 0.0:
        converted = 0.1
    BRIGHTNESS = converted
    update_led_state()

def handle_colour(hue, sat):
    global COLOUR_HUE, COLOUR_SAT
    
    COLOUR_HUE = hue
    COLOUR_SAT = sat
    update_led_state()
        
def status_handler(mode, status, ip):
    # reports wifi connection status
    print(mode, status, ip)
    print('Connecting to wifi...')
    # flash while connecting
    for i in range(NUM_LEDS):
        led_strip.set_rgb(i, 255, 255, 255)
        time.sleep(0.02)
    for i in range(NUM_LEDS):
        led_strip.set_rgb(i, 0, 0, 0)
    if status is not None:
        if status:
            print('Wifi connection successful!')
        else:
            print('Wifi connection failed!')

def check_for_force_poll():
    # fix bug where it drops off randomly
    global LAST_UPDATE, POLL_FREQUENCY
    
    curr_time = time.time()
    
    if (curr_time - LAST_UPDATE) > POLL_FREQUENCY:
        # revive if the wifi dropped at some point whilst up...a simple reboot would fix but try and heal
        if not network_manager.isconnected():
            print("Wifi detected as disconnected...firing error event handler")
            handle_wifi_error("", "Wifi detected as disconnected")
        else:
            print("time limit expired - forcing update to mqtt server")
            update_mqtt_state()
        
def subscribe_to_events():
    client.subscribe(COMMAND_TOPIC)
    client.subscribe(BRIGHTNESS_COMMAND_TOPIC)
    client.subscribe(HSL_COMMAND_TOPIC)
    
def handle_wifi_error(mode, message):
    print("Wifi error occurred", message);
    time.sleep(15)
    if not network_manager.isconnected():
        print("Attempting to reconnect to Wifi..")
        uasyncio.get_event_loop().run_until_complete(network_manager.client(WIFI_CONFIG.SSID, WIFI_CONFIG.PSK))
        update_led_state()
    
# set up the WS2812 / NeoPixel™ LEDs
led_strip = plasma.WS2812(NUM_LEDS, 0, 0, plasma_stick.DAT, color_order=plasma.COLOR_ORDER_RGB)

# start updating the LED strip
led_strip.start()

# set up wifi
try:
    network_manager = NetworkManager(WIFI_CONFIG.COUNTRY, status_handler=status_handler, error_handler=handle_wifi_error)
    uasyncio.get_event_loop().run_until_complete(network_manager.client(WIFI_CONFIG.SSID, WIFI_CONFIG.PSK))
except Exception as e:
    print(f'Wifi connection failed! {e}')
    
try:
    client = mqtt_connect()
except OSError as e:
   reconnect()

# set initial led state
update_led_state()
subscribe_to_events()

# set up loop and listen to command topics
while True:
    check_for_force_poll()
    client.check_msg()
    time.sleep(0.1)

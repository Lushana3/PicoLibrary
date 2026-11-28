"""
# config.py
# Settings for the Lab 4 IoT CRM device. Change these before running.
# Author: Lushana3
"""

# WiFi settings
# On real hardware use your phone hotspot. On the Wokwi simulator use 'Wokwi-GUEST' and ''.
WIFI_SSID = 'apt_502_2ghz'
WIFI_PASSWORD = ''

# REST web service base URL (swap ism6205 for ism6106 if one server is down)
BASE_URL = 'https://iacademy.oracle.com/ords/ism6205/customer'

# Loading strategy for the sequence you want to run:
#   'A' = retrieve ALL customers, contacts and activities first (eager)
#   'B' = retrieve customers first, contacts/activities only when a customer is selected (lazy)
LOAD_MODE = 'A'

# My own customer record (TODO 1) - device starts on this customer if found
MY_CUSTOMER_NAME = 'Lushana Joseph'

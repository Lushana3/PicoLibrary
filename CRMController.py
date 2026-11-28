"""
# CRMController.py
# State machine controller for the Lab 4 IoT CRM device.
# Connects to WiFi, retrieves CRM data through CRMService using either the
# EagerLoader (Option A) or LazyLoader (Option B), and lets the user browse
# customers -> contacts -> activities with three buttons.
# Author: Lushana3
"""

import time
from Log import *
from Trace import seq, note
from Displays import LCDDisplay
from LightStrip import LightStrip
from Buzzer import PassiveBuzzer
from Button import Button
from StateModel import StateModel
from Net import Net

import config
from CRMService import CRMService
from DataLoader import EagerLoader, LazyLoader
from CRMView import CRMView

# State numbers
CONNECTING = 0      # join WiFi + load customer list (and everything else in Option A)
CUSTOMERS = 1       # browse customers
LOAD_DETAILS = 2    # make sure contacts/activities are available (REST call in Option B)
CONTACTS = 3        # browse contacts of the selected customer
ACTIVITIES = 4      # browse activities of the selected customer
ERROR = 5           # network or web service problem

STATE_NAMES = ['CONNECTING', 'CUSTOMERS', 'LOAD_DETAILS', 'CONTACTS', 'ACTIVITIES', 'ERROR']


class CRMController:
    """
    **CRMController**

    Buttons:
      green  = next item
      red    = previous item
      yellow = select / go to the next screen (Customers -> Contacts -> Activities -> Customers)
    """

    def __init__(self, mode=None):
        self._mode = (mode or config.LOAD_MODE).upper()
        note(f"CRMController starting in Option {self._mode}")

        # View (hardware wiring is the same as Lab 3)
        display = LCDDisplay(sda=0, scl=1)
        lights = LightStrip(pin=2, name='Neopixel', numleds=8)
        buzzer = PassiveBuzzer(15, name='Buzzer')
        self.view = CRMView(display, lights, buzzer)

        # Model / web service
        self.net = Net()
        self.service = CRMService(self.net, config.BASE_URL)
        if self._mode == 'A':
            self.loader = EagerLoader(self.service)
        else:
            self.loader = LazyLoader(self.service)

        self.customers = []
        self._ci = 0     # customer index
        self._ii = 0     # item index (contact or activity)
        self._busy = False
        self._error = ''

        # State model
        self.model = StateModel(6, self, debug=True)
        self.model.addButton(Button(18, 'green'))
        self.model.addButton(Button(19, 'yellow'))
        self.model.addButton(Button(20, 'red'))
        for e in ['data_ready', 'details_ready', 'load_failed']:
            self.model.addCustomEvent(e)

        self.model.addTransition(CONNECTING, ['data_ready'], CUSTOMERS)
        self.model.addTransition(CONNECTING, ['load_failed'], ERROR)
        self.model.addTransition(CUSTOMERS, ['yellow_press'], LOAD_DETAILS)
        self.model.addTransition(LOAD_DETAILS, ['details_ready'], CONTACTS)
        self.model.addTransition(LOAD_DETAILS, ['load_failed'], ERROR)
        self.model.addTransition(CONTACTS, ['yellow_press'], ACTIVITIES)
        self.model.addTransition(ACTIVITIES, ['yellow_press'], CUSTOMERS)
        self.model.addTransition(ERROR, ['yellow_press'], CONNECTING)

    def run(self):
        self.model.run()

    def stop(self):
        self.view.lightsOff()
        self.model.stop()

    # ------------------------------------------------------------------
    # StateModel handlers
    # ------------------------------------------------------------------

    def stateEntered(self, state, event):
        seq('StateModel', 'CRMController', f"stateEntered({STATE_NAMES[state]}) on {event}")

        if state == CONNECTING:
            self.view.showMessage('IoT CRM Opt ' + self._mode, 'Connecting WiFi')
            self._busy = True          # stateDo will do the slow work once

        elif state == CUSTOMERS:
            self._showCustomer()

        elif state == LOAD_DETAILS:
            customer = self.customers[self._ci]
            if not customer.detailsLoaded:
                self.view.showMessage('Retrieving...', customer.name)
            self._busy = True

        elif state == CONTACTS:
            self._ii = 0
            self._showContact()

        elif state == ACTIVITIES:
            self._ii = 0
            self._showActivity()

        elif state == ERROR:
            self.view.showMessage('Network error', 'Yellow: retry')
            self.view.sadTone()

    def stateLeft(self, state, event):
        pass

    def stateDo(self, state):
        """ Slow network work happens here (once) so entry actions stay quick """
        if not self._busy:
            return
        self._busy = False

        if state == CONNECTING:
            try:
                if not self.net.isConnected():
                    seq('CRMController', 'Net', f"connect('{config.WIFI_SSID}')")
                    self.net.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
                    seq('Net', 'CRMController', f"connected, ip {self.net.getLocalIp()}")
                self.view.showMessage('Loading', 'customers...')
                self.service.resetStats()
                seq('CRMController', self.loader.name, "loadCustomers()")
                self.customers = self.loader.loadCustomers(progress=self.view.showProgress)
                seq(self.loader.name, 'CRMController', f"{len(self.customers)} customers")
                if not self.customers:
                    raise RuntimeError('No customers returned')
                self._ci = self._findMyCustomer()
                self.view.readyChime()
                self.model.processEvent('data_ready')
            except Exception as e:
                Log.e(f"Loading failed: {e}")
                self.model.processEvent('load_failed')

        elif state == LOAD_DETAILS:
            customer = self.customers[self._ci]
            try:
                seq('CRMController', self.loader.name, f"ensureDetails({customer.name})")
                self.loader.ensureDetails(customer)
                self.model.processEvent('details_ready')
            except Exception as e:
                Log.e(f"Detail loading failed: {e}")
                self.model.processEvent('load_failed')

    def stateEvent(self, state, event):
        """ green/red move through the list without leaving the state """
        if event not in ('green_press', 'red_press'):
            return False
        step = 1 if event == 'green_press' else -1
        seq('Button', 'CRMController', f"{event}")

        if state == CUSTOMERS:
            self._ci = (self._ci + step) % len(self.customers)
            self.view.click()
            self._showCustomer()
            return True

        if state in (CONTACTS, ACTIVITIES):
            customer = self.customers[self._ci]
            items = customer.contacts if state == CONTACTS else customer.activities
            if items:
                self._ii = (self._ii + step) % len(items)
                self.view.click()
                if state == CONTACTS:
                    self._showContact()
                else:
                    self._showActivity()
            return True

        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _findMyCustomer(self):
        for i, c in enumerate(self.customers):
            if c.name == config.MY_CUSTOMER_NAME:
                return i
        return 0

    def _showCustomer(self):
        c = self.customers[self._ci]
        seq('CRMController', 'CRMView', f"showCustomer({c.name})")
        self.view.showCustomer(c, self._ci, len(self.customers))

    def _showContact(self):
        c = self.customers[self._ci]
        if not c.contacts:
            self.view.showEmpty('contacts')
            return
        seq('CRMController', 'CRMView', f"showContact({c.contacts[self._ii].name})")
        self.view.showContact(c.contacts[self._ii], self._ii, len(c.contacts))

    def _showActivity(self):
        c = self.customers[self._ci]
        if not c.activities:
            self.view.showEmpty('activities')
            return
        seq('CRMController', 'CRMView', f"showActivity({c.activities[self._ii].name})")
        self.view.showActivity(c.activities[self._ii], self._ii, len(c.activities))

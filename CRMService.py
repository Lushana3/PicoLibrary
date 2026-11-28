"""
# CRMService.py
# Web service client for the Oracle ORDS REST API. Wraps the PicoLibrary Net
# class and turns JSON into Customer, Contact and Activity objects.
# Also counts calls and time spent so Option A and B can be compared.
# Author: Lushana3
"""

import time
from Log import *
from Trace import seq, note
from CRMModel import Customer, Contact, Activity


class CRMService:
    """
    **CRMService** - one method per REST endpoint.

    Parameters:
    ----------
    net : Net
        A connected PicoLibrary Net object.
    baseUrl : str
        e.g. https://iacademy.oracle.com/ords/ism6205/customer
    """

    def __init__(self, net, baseUrl):
        self._net = net
        self._baseUrl = baseUrl.rstrip('/')
        self.callCount = 0
        self.totalMs = 0

    # ------------------------------------------------------------------
    # Public endpoint methods
    # ------------------------------------------------------------------

    def getVersion(self):
        """ GET /version - quick check that the service is reachable """
        return self._get('version')

    def getCustomers(self):
        """ GET /get_customers -> list of Customer """
        items = self._getItems('get_customers')
        return [Customer(i) for i in items]

    def getContacts(self, custId):
        """ GET /get_contacts/:cust_id -> list of Contact """
        items = self._getItems(f'get_contacts/{custId}')
        return [Contact(i) for i in items]

    def getActivities(self, custId):
        """ GET /get_activities/:cust_id -> list of Activity """
        items = self._getItems(f'get_activities/{custId}')
        return [Activity(i) for i in items]

    def resetStats(self):
        self.callCount = 0
        self.totalMs = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, path):
        """ One HTTP GET. Returns the parsed JSON dict, or raises on failure """
        url = path if path.startswith('http') else f"{self._baseUrl}/{path}"
        short = url.replace(self._baseUrl, '')
        seq('CRMService', 'OracleREST', f"GET {short}")
        start = time.ticks_ms()
        data = self._net.getJson(url)
        ms = time.ticks_diff(time.ticks_ms(), start)
        self.callCount += 1
        self.totalMs += ms
        if data is None:
            seq('OracleREST', 'CRMService', f"ERROR (no JSON) after {ms} ms")
            raise RuntimeError(f"Web service call failed: {short}")
        seq('OracleREST', 'CRMService', f"200 OK JSON in {ms} ms")
        return data

    def _getItems(self, path):
        """
        GET a collection. ORDS returns at most 25 items per page with
        hasMore=True and a 'next' link, so keep following pages until done.
        """
        items = []
        url = path
        while url:
            data = self._get(url)
            items.extend(data.get('items', []))
            url = None
            if data.get('hasMore'):
                for link in data.get('links', []):
                    if link.get('rel') == 'next':
                        url = link.get('href')
                        note(f"hasMore=True, following next page ({len(items)} items so far)")
        return items

"""
# DataLoader.py
# Strategy classes that decide WHEN contacts and activities are retrieved.
#   EagerLoader  = Option A: retrieve everything at startup
#   LazyLoader   = Option B: retrieve details only when a customer is selected
# The controller only talks to the DataLoader superclass, so switching between
# A and B is one setting in config.py.
# Author: Lushana3
"""

import time
from Log import *
from Trace import seq, note


class DataLoader:
    """
    **DataLoader** - abstract strategy base class.

    Parameters:
    ----------
    service : CRMService
        The web service client used to retrieve data.
    """

    name = 'DataLoader'

    def __init__(self, service):
        self._service = service

    def loadCustomers(self):
        """ Return the list of Customers to browse. Subclasses decide how much to load. """
        raise NotImplementedError

    def ensureDetails(self, customer):
        """ Make sure contacts/activities for this customer are available. """
        raise NotImplementedError

    def _loadDetails(self, customer):
        """ Shared helper: two REST calls for one customer """
        seq(self.name, 'CRMService', f"getContacts({customer.name})")
        contacts = self._service.getContacts(customer.id)
        seq(self.name, 'CRMService', f"getActivities({customer.name})")
        activities = self._service.getActivities(customer.id)
        seq(self.name, 'Customer', f"setDetails({len(contacts)} contacts, {len(activities)} activities)")
        customer.setDetails(contacts, activities)


class EagerLoader(DataLoader):
    """
    **EagerLoader** - Option A.
    Retrieves all customers, then loops through every customer to retrieve
    contacts and activities before the user can browse. Browsing is instant after.
    """

    name = 'EagerLoader'

    def loadCustomers(self, progress=None):
        start = time.ticks_ms()
        seq(self.name, 'CRMService', "getCustomers()")
        customers = self._service.getCustomers()
        note(f"Option A: {len(customers)} customers - now loading details for ALL of them")
        for i, c in enumerate(customers):
            if progress:
                progress(i + 1, len(customers))
            self._loadDetails(c)
        ms = time.ticks_diff(time.ticks_ms(), start)
        note(f"Option A startup: {self._service.callCount} REST calls, {ms} ms total")
        return customers

    def ensureDetails(self, customer):
        # Already loaded at startup - no web call needed
        seq(self.name, 'Customer', f"detailsLoaded? {customer.detailsLoaded} (no REST call)")
        return 0


class LazyLoader(DataLoader):
    """
    **LazyLoader** - Option B.
    Retrieves only the customer list at startup. Contacts and activities are
    retrieved the first time a customer is selected, then cached.
    """

    name = 'LazyLoader'

    def loadCustomers(self, progress=None):
        start = time.ticks_ms()
        seq(self.name, 'CRMService', "getCustomers()")
        customers = self._service.getCustomers()
        ms = time.ticks_diff(time.ticks_ms(), start)
        note(f"Option B startup: {self._service.callCount} REST call(s), {ms} ms total")
        return customers

    def ensureDetails(self, customer):
        """ Returns how many ms the selection had to wait for the network """
        if customer.detailsLoaded:
            seq(self.name, 'Customer', "detailsLoaded? True (cached, no REST call)")
            return 0
        seq(self.name, 'Customer', "detailsLoaded? False -> retrieve now")
        start = time.ticks_ms()
        self._loadDetails(customer)
        ms = time.ticks_diff(time.ticks_ms(), start)
        note(f"Option B selection wait for {customer.name}: {ms} ms")
        return ms

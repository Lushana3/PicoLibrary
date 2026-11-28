"""
# CRMModel.py
# Business model classes for the IoT CRM device: Customer, Contact, Activity.
# Each class builds itself from the JSON dictionary returned by the REST service.
# Author: Lushana3
"""

from Log import *


def _text(value, default=''):
    """ JSON nulls come back as None - turn them into a safe string """
    return default if value is None else str(value)


class Contact:
    """
    **Contact** - a person who works for a Customer.

    Built from one item of get_contacts/:cust_id
    JSON fields: id, name, title, company, phone, contact_type
    """

    def __init__(self, data):
        self.id = _text(data.get('id'))
        self.name = _text(data.get('name'), 'Unknown')
        self.title = _text(data.get('title'))
        self.company = _text(data.get('company'))
        self.phone = _text(data.get('phone'))
        self.contactType = _text(data.get('contact_type'), 'Other')

    def getDisplayLines(self):
        """ Two 16 char lines for the LCD """
        return [self.name[:16], (self.title or self.contactType)[:16]]


class Activity:
    """
    **Activity** - something we already did with a Customer.

    Built from one item of get_activities/:cust_id
    JSON fields: id, activity_type, name, description, activity_date, owner, location
    """

    def __init__(self, data):
        self.id = _text(data.get('id'))
        self.activityType = _text(data.get('activity_type'), 'Other')
        self.name = _text(data.get('name'), 'Activity')
        self.description = _text(data.get('description'))
        self.activityDate = _text(data.get('activity_date'))[:10]   # keep YYYY-MM-DD
        self.owner = _text(data.get('owner'))
        self.location = _text(data.get('location'))

    def getDisplayLines(self):
        """ Two 16 char lines for the LCD: name, then date + location """
        line1 = f"{self.activityDate[5:]} {self.location}"   # MM-DD Miami
        return [self.name[:16], line1[:16]]


class Customer:
    """
    **Customer** - a client company/person in the CRM.

    Built from one item of get_customers.
    JSON fields: id, customer_name, category, category_description, geography_name, type

    A Customer owns 0..* Contacts and 0..* Activities. detailsLoaded tells the
    controller whether contacts/activities have been retrieved yet - this is what
    makes Option A (eager) and Option B (lazy) possible with the same class.
    """

    def __init__(self, data):
        self.id = _text(data.get('id'))
        self.name = _text(data.get('customer_name'), 'Unknown')
        self.category = _text(data.get('category'))
        self.geography = _text(data.get('geography_name'))
        self.type = _text(data.get('type'))
        self.contacts = []
        self.activities = []
        self.detailsLoaded = False

    def setDetails(self, contacts, activities):
        """ Attach the contacts and activities retrieved from the web service """
        self.contacts = contacts
        self.activities = activities
        self.detailsLoaded = True
        Log.i(f"Customer {self.name}: {len(contacts)} contacts, {len(activities)} activities")

    def hasActivities(self):
        return self.detailsLoaded and len(self.activities) > 0

    def getDisplayLines(self, index, total):
        """ Line 0: name. Line 1: position plus counts (? if not loaded yet) """
        if self.detailsLoaded:
            counts = f"C:{len(self.contacts)} A:{len(self.activities)}"
        else:
            counts = "C:? A:?"
        return [self.name[:16], f"{index + 1}/{total} {counts}"[:16]]

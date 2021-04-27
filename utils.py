import json
import secrets
import re

from consts import (EC2_INSTANCE_IP,
                    PENDING,
                    PENDING_MESSAGE,
                    APPROVED,
                    REGISTERED_MESSAGE,
                    API_KEY,
                    SITE_KEY,
                    URL)


def register_to_civi(payload, session):
    """
    Make the API request to CiviCRM and Drupal for registering a new contact
    :param payload: Request parameters
    :param session: API Session
    :return: True if registered successfully else False
    """
    response = session.post(f"{EC2_INSTANCE_IP}/user/register", data=payload)

    response_str = str(response.content)

    if PENDING_MESSAGE in response_str:
        return True, PENDING

    if REGISTERED_MESSAGE in response_str:
        return True, APPROVED
    return False, APPROVED


def login_to_civi(payload, session):
    """
    Login to the system
    :param payload: Login parameters
    :param session: API Session
    :return: True If successfully login. else False
    """
    response = session.post(f"{EC2_INSTANCE_IP}/user", data=payload)
    response = session.post(f"{EC2_INSTANCE_IP}/user", data=payload)

    if 'Log out' in str(response.content):
        return True
    return False


def get_contact_details(email, session):
    """
    Get CiviCRM Contact details
    :param email: Contact's email
    :param session: API session
    :return: CiviCRM Contact
    """
    params = {
        'entity': 'Contact',
        'action': 'get',
        'json': json.dumps({"sequential": 1, "email": email}),
        'api_key': API_KEY,
        'key': SITE_KEY
    }

    response = session.get(URL, params=params)
    response_json = response.json()

    if response_json.get('values', []):
        if response_json.get('values', [])[0]:
            return response_json.get('values', [])[0]
        return ''
    return ''


def add_to_contact_group(group_name, contact_id, session):
    """
    Add contact to CiviCRM group
    :param group_name: Name of the group to add the contact to
    :param contact_id: ID of the contact that should be added
    :param session: API Session
    :return: None.
    """
    params = {
        'entity': 'GroupContact',
        'action': 'create',
        'json': json.dumps({"group_id": group_name, "contact_id": contact_id}),
        'api_key': API_KEY,
        'key': SITE_KEY
    }

    response = session.post(URL, params=params)
    #     TODO: add error handling


def create_api_key():
    """
    Generate an API key.
    :return: API key
    """
    return re.sub("[^\w]|[\_]", 'q', secrets.token_urlsafe(16))


def attach_api_key_to_contact(contact_id, api_key, session):
    """
    Attach a generated API key to CiviCRM contact
    :param contact_id: CiviCRM Contact ID
    :param api_key: Generated API key
    :param session: API Session
    :return: None.
    """
    params = {
        'entity': 'Contact',
        'action': 'create',
        'json': json.dumps({"id": contact_id, "api_key": api_key}),
        'api_key': API_KEY,
        'key': SITE_KEY
    }

    response = session.post(URL, params=params)


#     TODO: add error handling


def fill_contact_details(contact_id, firstname, lastname, contact_sub_type, session):
    """
    Enrich CiviCRM contact details
    :param contact_id: CiviCRM Contact ID
    :param firstname: First name of the contact
    :param lastname: Last name of the contact
    :param contact_sub_type: contact sub type
    :param session: API Session
    :return: None.
    """
    params = {
        'entity': 'Contact',
        'action': 'create',
        'json': json.dumps({"id": contact_id, 'first_name': firstname, 'last_name': lastname, "contact_sub_type": contact_sub_type}),
        'api_key': API_KEY,
        'key': SITE_KEY
    }

    response = session.post(URL, params=params)


def json_response(is_error, message, json_data):
    """
    Creates json response
    :param is_error: Error status
    :param message: Message to send to the client
    :param json_data: Data should be returned
    :return: Json response
    """
    return {
        "is_error": is_error,
        "Message": message,
        "Data": json_data
    }
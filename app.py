from flask import Flask, jsonify, request

import requests
import json
import sys
import secrets
import re


EC2_INSTANCE_IP = "http://52.90.78.193"

URL = "http://52.90.78.193/modules/contrib/civicrm/extern/rest.php?"

API_KEY = 'HLd3GTnYMRw6FGMgW7XxFD3K'
SITE_KEY = 'aacce8033f7a9730040b45df047e3191'


app = Flask(__name__)


@app.route('/register')
def register():
    data = json.loads(request.data)
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    firstname = data.get('firstname')
    lastname = data.get('lastname')
    contact_type = data.get('content_type')
    session = requests.Session()
    session.headers.update()

    contact_id = ''
    api_key = ''

    payload = {
        'name': username,
        'mail': email,
        'pass[pass1]': password,
        'pass[pass2]': password,
        'form_id': 'user_register_form',
        'op': 'Create new account',
        'timezone': 'UTC',
        'first_name': firstname,
        'last_name': lastname,
        # '_qf_default': 'Dynamic:upload',
        # 'MAX_FILE_SIZE': 83886080,
        # 'street_address-1': '',
        # 'city-1': '',
        # 'postal_code-1': '',
        # 'country-1': '',
        'edit[civicrm_dummy_field]': 'CiviCRM Dummy Field for Drupal',
    }

    is_registered = register_to_civi(payload=payload, session=session)

    if not is_registered:
        return json_response(
            is_error=1,
            message="Failed register to the system",
            json_data={"data": ""}
        )

    contact_id = get_contact_id(email, session)

    if not contact_id:
        return json_response(
            is_error=1,
            message="Failed register to the system",
            json_data={"data": ""}
        )

    api_key = create_api_key()
    attach_api_key_to_contact(contact_id, api_key, session)
    fill_contact_details(contact_id, contact_type, firstname, lastname, session)

    return json_response(
        is_error=0,
        message="Successfully registered to the system",
        json_data={"API_KEY": api_key}
    )


@app.route('/login')
def login():
    username = request.args.get('username')
    password = request.args.get('password')
    email = request.args.get('email')
    session = requests.Session()
    session.headers.update()
    payload = {
        'name': username,
        'pass': password,
        'form_id': 'user_login',
        'op': 'Log in'
    }

    contact_id = ''
    api_key = ''

    is_logged_in = login_to_civi(payload=payload, session=session)
    if not is_logged_in:
        return json_response(
            is_error=1,
            message="Failed to log in",
            json_data={"data": ""}
        )

    contact_id = get_contact_id(email, session)
    api_key = create_api_key()

    if not contact_id:
        return json_response(
            is_error=1,
            message="Failed to log in",
            json_data={"data": ""}
        )

    attach_api_key_to_contact(contact_id, api_key, session)

    if contact_id:
        return json_response(
            is_error=0,
            message="Successfully logged in",
            json_data={"API_KEY": api_key}
        )


def login_to_civi(payload, session):
    response = session.post(f"{EC2_INSTANCE_IP}/user", data=payload)
    print(response.text)
    print(response.headers)
    print(session.cookies)
    response = session.post(f"{EC2_INSTANCE_IP}/user", data=payload)

    if 'Log out' in str(response.content):
        return True
    return False
    # return str(response.content)


def register_to_civi(payload, session):
    response = session.post(f"{EC2_INSTANCE_IP}/user/register", data=payload)

    if 'Registration successful' in str(response.content):
        return True
    return False


def get_contact_id(email, session):
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
            return response_json.get('values', [])[0].get('contact_id')
        return ''
    return ''


def create_api_key():
    return re.sub("[^\w]|[\_]",  'q', secrets.token_urlsafe(16))


def attach_api_key_to_contact(contact_id, api_key, session):
    params = {
        'entity': 'Contact',
        'action': 'create',
        'json': json.dumps({"id": contact_id, "api_key": api_key}),
        'api_key': API_KEY,
        'key': SITE_KEY
    }

    response = session.post(URL, params=params)
#     TODO: add error handling


def fill_contact_details(contact_id, api_key, firstname, lastname, session):
    params = {
        'entity': 'Contact',
        'action': 'create',
        'json': json.dumps({"id": contact_id, "api_key": api_key, 'first_name': firstname, 'last_name': lastname}),
        'api_key': API_KEY,
        'key': SITE_KEY
    }

    response = session.post(URL, params=params)

@app.route('/logout')
def logout():
    email = request.args.get('email')
    session = requests.Session()
    session.headers.update()
    contact_id = get_contact_id(email, session)

    empty_api = ''
    attach_api_key_to_contact(contact_id, empty_api, session)
    return json_response(
        is_error=0,
        message="Successfully logged out",
        json_data={"API_KEY": empty_api}
    )


def json_response(is_error, message, json_data):
    return {
        "is_error": is_error,
        "Message": message,
        "Data": json_data
    }


if __name__ == '__main__':
    app.run(debug=True)

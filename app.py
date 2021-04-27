from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import requests
import json
import sys
import secrets
import re

EC2_INSTANCE_IP = "http://52.90.78.193"

URL = "http://52.90.78.193/modules/contrib/civicrm/extern/rest.php?"

API_KEY = 'qtjrB1QzwvBIhMVcPcT3Nw'
SITE_KEY = 'aacce8033f7a9730040b45df047e3191'

GROUP_NAME_TO_NAME_ID_MAPPER = {
    "volunteer": "Volunteers_5",
    "soldier": "Soldiers_7",
    "staff": "StaffMembers_8"
}

GROUP_NAME_CONTACT_SUB_TYPE = {
    "volunteer": "Volunteer",
    "soldier": "Soldier",
    "staff": "StaffMember",
    "admin": "Admin"
}

# Registration/Login status options:
PENDING = "Pending"
APPROVED = "approved"


PENDING_MESSAGE = "Thank you for applying for an account. Your account is currently pending approval by the site administrator."
REGISTERED_MESSAGE = "Registration successful"

app = Flask(__name__)

cors = CORS(app, resources={r"/*": {"origins": "*", "allow_headers": "*", "expose_headers": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/register', methods=['POST'])
@cross_origin()
def register():
    """
    Register to Drupal and CiviCRM System.
    :return: None.
    """
    data = json.loads(request.data)
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    firstname = data.get('firstname')
    lastname = data.get('lastname')
    contact_sub_type = [PENDING, GROUP_NAME_CONTACT_SUB_TYPE.get(data.get('group_name'))]
    group_name_id = GROUP_NAME_TO_NAME_ID_MAPPER.get(data.get('group_name'))
    session = requests.Session()
    session.headers.update()

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
        'edit[civicrm_dummy_field]': 'CiviCRM Dummy Field for Drupal',
        'status': 1
    }

    is_registered, status = register_to_civi(payload=payload, session=session)

    if not is_registered:
        return json_response(
            is_error=1,
            message="Failed register to the system",
            json_data={"data": ""}
        )

    contact = get_contact_details(email=email,
                                  session=session)

    contact_id = contact.get('contact_id')

    add_to_contact_group(group_name=group_name_id,
                         contact_id=contact_id,
                         session=session)

    if not contact_id:
        return json_response(
            is_error=1,
            message="Failed register to the system",
            json_data={"data": ""}
        )

    api_key = create_api_key()
    attach_api_key_to_contact(contact_id=contact_id,
                              api_key=api_key,
                              session=session)

    fill_contact_details(contact_id=contact_id,
                         contact_sub_type=contact_sub_type,
                         firstname=firstname,
                         lastname=lastname,
                         session=session)

    contact = get_contact_details(email=email,
                                  session=session)

    return json_response(
        is_error=0,
        message=PENDING_MESSAGE,
        json_data={
            "contact": contact
        }
    )


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
    return False


@app.route('/login', methods=['POST'])
@cross_origin()
def login():
    """
    Login To Drupal and CiviCRM user
    :return: None.
    """
    data = json.loads(request.data)
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    session = requests.Session()
    session.headers.update()
    payload = {
        'name': username,
        'pass': password,
        'form_id': 'user_login',
        'op': 'Log in'
    }

    is_logged_in = login_to_civi(payload=payload, session=session)
    if not is_logged_in:
        return json_response(
            is_error=1,
            message="Failed to log in",
            json_data={"data": ""}
        )

    contact = get_contact_details(email=email,
                                  session=session)
    contact_id = contact.get('contact_id')
    api_key = create_api_key()

    if not contact_id:
        return json_response(
            is_error=1,
            message="Failed to log in",
            json_data={"data": ""}
        )

    attach_api_key_to_contact(contact_id=contact_id,
                              api_key=api_key,
                              session=session)

    if contact_id:
        return json_response(
            is_error=0,
            message="Successfully logged in",
            json_data={
                "API_KEY": api_key,
                "contact": contact
            }
        )


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
    return re.sub("[^\w]|[\_]", 'q', secrets.token_urlsafe(16))


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


def fill_contact_details(contact_id, firstname, lastname, contact_sub_type, session):
    params = {
        'entity': 'Contact',
        'action': 'create',
        'json': json.dumps({"id": contact_id, 'first_name': firstname, 'last_name': lastname, "contact_sub_type": contact_sub_type}),
        'api_key': API_KEY,
        'key': SITE_KEY
    }

    response = session.post(URL, params=params)


@app.route('/logout', methods=['POST'])
def logout():
    """
    Logout from Drupal CiviCRM user
    :return: None.
    """
    data = json.loads(request.data)
    email = data.get('email')
    session = requests.Session()
    session.headers.update()
    contact = get_contact_details(email=email,
                                  session=session)

    if not contact:
        return json_response(
            is_error=1,
            message="Failed to log out",
            json_data={"data": ""}
        )

    contact_id = contact.get('contact_id')

    empty_api = ''
    attach_api_key_to_contact(contact_id=contact_id,
                              api_key=empty_api,
                              session=session)
    return json_response(
        is_error=0,
        message="Successfully logged out",
        json_data={"API_KEY": empty_api}
    )


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


if __name__ == '__main__':
    app.run(debug=True)

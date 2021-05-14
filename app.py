from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import requests
import json
import sys

from consts import (EC2_INSTANCE_IP,
                    URL,
                    API_KEY,
                    SITE_KEY,
                    GROUP_NAME_TO_NAME_ID_MAPPER,
                    GROUP_NAME_CONTACT_SUB_TYPE,
                    PENDING,
                    APPROVED,
                    PENDING_MESSAGE,
                    REGISTERED_MESSAGE,
                    UNRECOGNIZED_MESSAGE)

from utils import (register_to_civi,
                   login_to_civi,
                   get_contact_details,
                   add_to_contact_group,
                   create_api_key,
                   attach_api_key_to_contact,
                   fill_contact_details,
                   json_response,
                   add_details_to_contact)

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
    image_url = data.get('image_url')
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

    is_logged_in, message = login_to_civi(payload=payload, session=session)

    if not is_logged_in:
        return json_response(
            is_error=1,
            message=message,
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
            message=message,
            json_data={
                "API_KEY": api_key,
                "contact": contact
            }
        )


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


@app.route('/upload_doc', methods=['POST'])
def upload_doc():
    """
    Upload document to a CivCRM contact.
    :return: None.
    """
    data = json.loads(request.data)
    email = data.get('email')
    doc_url = data.get('image_URL')

    session = requests.Session()
    session.headers.update()

    contact = get_contact_details(email=email,
                                  session=session)

    contact_id = contact.get('contact_id')
    empty_api = ''

    add_details_to_contact(session=session,
                           contact_details_dict={
                               "id": contact_id,
                               "image_URL": doc_url
                           })

    return json_response(
        is_error=0,
        message="Successfully uploaded document.",
        json_data={"API_KEY": empty_api}
    )


if __name__ == '__main__':
    app.run(debug=True)

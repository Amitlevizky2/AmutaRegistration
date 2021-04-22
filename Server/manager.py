from flask import Flask, jsonify, request, Blueprint
import requests
import json
import sys
import secrets
import re
import globals

manager = Blueprint('manager', __name__)

# Requests Routes:
@manager.route('/search')
def search():
    data = json.loads(request.data)
    api_key = data.get('api_key')
    key = globals.SITE_KEY

    contact_id = data.get('contact_id')
    email = data.get('email')
    contact_type = data.get('contact_type')
    first_name = data.get('first_name')
    last_name = data.get('last_name')

    session = requests.Session()
    session.headers.update()

    params = {
        'entity': 'Contact',
        'action': 'get',
        'json': json.dumps({"sequential": 1,"id": contact_id, "email": email, "contact_type": contact_type, "first_name": first_name, "last_name": last_name}),
        'api_key': api_key,
        'key': globals.SITE_KEY
    }

    response = session.get(globals.URL, params=params)
    response_json = response.json()
    return response_json


@manager.route('/update')
def update_contact():
    data = json.loads(request.data)
    api_key = data.get('api_key')
    key = globals.SITE_KEY

    contact_id = data.get('contact_id')
    email = data.get('email')
    contact_type = data.get('contact_type')
    first_name = data.get('first_name')
    last_name = data.get('last_name')

    session = requests.Session()
    session.headers.update()

    params = {
        'entity': 'Contact',
        'action': 'create',
        'json': json.dumps({"sequential": 1,"id": contact_id, "email": email, "contact_type": contact_type, "first_name": first_name, "last_name": last_name}),
        'api_key': api_key,
        'key': globals.SITE_KEY
    }

    response = session.get(globals.URL, params=params)
    response_json = response.json()
    return response_json
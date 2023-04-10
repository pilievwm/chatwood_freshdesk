"""
This script handles webhook events related to user logins on the CloudCart platform.
It extracts relevant data from the webhook payload and updates Freshdesk contact and company custom fields with the data.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

FRESHDESK_API_KEY = os.getenv('FRESHDESK_API_KEY')
FRESHDESK_API_URL = os.getenv('FRESHDESK_API_URL')


def handle_login_user(request):
    webhook_data = request.get_json()
    email = webhook_data['data']['admin']['email']
    owner_name = webhook_data['data']['site']['user']['cc_user']['name']
    owner_email = webhook_data['data']['site']['user']['cc_user']['email']
    status = webhook_data['data']['site']['status']
    plan = webhook_data['data']['site']['plan']
    freshdesk_company_id = webhook_data['data']['site']['freshdesk_id']

    status_mapping = {
        0: 'Canceled',
        1: 'Active',
        2: 'Past Due',
        3: 'Expired'
    }

    status_number = webhook_data['data']['site'].get('status', None)
    status_text = status_mapping.get(status_number, 'Unknown')

    # Get the Freshdesk contact by email
    freshdesk_contact = get_freshdesk_contact_by_email(email)
    if freshdesk_contact is not None:
        freshdesk_id = freshdesk_contact['id']
        update_contact_result = update_freshdesk_contact(freshdesk_id, owner_name, owner_email)
    else:
        update_contact_result = 'Error: Freshdesk contact not found by email'

    update_contact_result, freshdesk_contact_id = update_freshdesk_contact(freshdesk_id, owner_name, owner_email)
    update_company_result, freshdesk_updated_company_id = update_freshdesk_company(freshdesk_company_id, plan, status_text)

    return f'Contact update result: {update_contact_result} (ID: {freshdesk_contact_id}, Email: {email})\nCompany update result: {update_company_result} (ID: {freshdesk_updated_company_id})'



def get_freshdesk_contact_by_email(email):
    url = f'{FRESHDESK_API_URL}/contacts?email={email}'
    headers = {
        'Content-Type': 'application/json'
    }
    auth = (FRESHDESK_API_KEY, 'X')

    response = requests.get(url, headers=headers, auth=auth)

    if response.status_code == 200:
        contacts = response.json()
        if len(contacts) > 0:
            return contacts[0]
        else:
            return None
    else:
        return None


def update_freshdesk_contact(freshdesk_id, owner_name, owner_email):
    url = f'{FRESHDESK_API_URL}/contacts/{freshdesk_id}'
    headers = {
        'Content-Type': 'application/json'
    }
    auth = (FRESHDESK_API_KEY, 'X')

    data = {
        'custom_fields': {
            'owner': owner_email,
            'owner_name': owner_name
        }
    }

    response = requests.put(url, json=data, headers=headers, auth=auth)

    if response.status_code == 200:
        return 'Freshdesk contact updated successfully', freshdesk_id
    else:
        return f'Error updating Freshdesk contact: {response.status_code} - {response.text}', None


def update_freshdesk_company(freshdesk_company_id, plan, status):
    url = f'{FRESHDESK_API_URL}/companies/{freshdesk_company_id}'
    headers = {
        'Content-Type': 'application/json'
    }
    auth = (FRESHDESK_API_KEY, 'X')

    data = {
        'custom_fields': {
            'plan1': plan,
            'status': status
        }
    }

    response = requests.put(url, json=data, headers=headers, auth=auth)

    if response.status_code == 200:
        return 'Freshdesk company updated successfully', freshdesk_company_id
    else:
        return f'Error updating Freshdesk company: {response.status_code} - {response.text}', None
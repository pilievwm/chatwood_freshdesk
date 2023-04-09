import os
import requests
from dotenv import load_dotenv

load_dotenv()

FRESHDESK_API_KEY = os.getenv('FRESHDESK_API_KEY')
FRESHDESK_API_URL = os.getenv('FRESHDESK_API_URL')

def handle_login_user(request):
    webhook_data = request.get_json()

    owner_name = webhook_data['data']['site']['user']['cc_user']['name']
    owner_email = webhook_data['data']['site']['user']['cc_user']['email']
    status = webhook_data['data']['site']['status']
    plan = webhook_data['data']['site']['plan']
    freshdesk_id = webhook_data['data']['site']['user']['freshdesk_id']
    freshdesk_company_id = webhook_data['data']['site']['freshdesk_id']
    calendly_url = webhook_data['data']['site']['user']['cc_user'].get('calendly_url', None)
    
    # Map status to text
    status_mapping = {
        0: 'Canceled',
        1: 'Active',
        2: 'Past Due',
        3: 'Expired'
    }

    # Get the status number from the webhook data
    status_number = webhook_data['data']['site'].get('status', None)

    # Map the status number to its corresponding text
    status_text = status_mapping.get(status_number, 'Unknown')

    # Update Freshdesk contact with owner_name and owner_email
    update_contact_result = update_freshdesk_contact(freshdesk_id, owner_name, owner_email)

    # Update Freshdesk company with plan and status
    update_company_result = update_freshdesk_company(freshdesk_company_id, plan, status_text)

    # Add your code to process the extracted data here

    return f'Contact update result: {update_contact_result}\nCompany update result: {update_company_result}'


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
        return 'Freshdesk contact updated successfully'
    else:
        return f'Error updating Freshdesk contact: {response.status_code} - {response.text}'


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
        return 'Freshdesk company updated successfully'
    else:
        return f'Error updating Freshdesk company: {response.status_code} - {response.text}'

import requests
import os
from team import get_availability, get_team_structure

# Constants
CHAT_API_ACCESS_TOKEN = os.environ['CHAT_API_ACCESS_TOKEN']
VIBER_API_URL = os.environ['VIBER_API_URL']
X_VIBER_AUTH_TOKEN = os.environ['X_VIBER_AUTH_TOKEN']
CHAT_API_URL = os.environ['CHAT_API_URL']


def get_headers(api_access_token=None, viber_auth_token=None):
    headers = {"Content-Type": "application/json"}
    
    if api_access_token:
        headers["api_access_token"] = api_access_token
        
    if viber_auth_token:
        headers["X-Viber-Auth-Token"] = viber_auth_token
        
    return headers

def assign_conversation(conversation_id, assignee_id, api_access_token):
    assign_url = f"{CHAT_API_URL}/conversations/{conversation_id}/assignments"
    headers = {
        "Content-Type": "application/json",
        "api_access_token": api_access_token
    }
    payload = {
        "assignee_id": assignee_id
    }
    response = requests.post(assign_url, json=payload, headers=headers)

    return response

def update_contact_viber_id(contact_id, viber_id, received_message, api_access_token):
    update_contact_url = f"{CHAT_API_URL}/contacts/{contact_id}"
    update_contact_payload = {
        "custom_attributes": {
            "viberid": viber_id
        }
    }
    headers = get_headers(api_access_token=api_access_token)

    requests.put(update_contact_url, json=update_contact_payload, headers=headers)

def create_conversation(contact_id, inbox_id, api_access_token):
    create_conversation_url = f"{CHAT_API_URL}/conversations"
    create_conversation_payload = {
        "contact_id": contact_id,
        "inbox_id": inbox_id
    }

    headers = {
        "Content-Type": "application/json",
        "api_access_token": api_access_token
    }

    response = requests.post(create_conversation_url, json=create_conversation_payload, headers=headers)
    return response.json()

def get_latest_conversation(contact_id, inbox_id, api_access_token):
    get_conversations_url = f"{CHAT_API_URL}/contacts/{contact_id}/conversations"
    headers = {
        "Content-Type": "application/json",
        "api_access_token": api_access_token
    }
    response = requests.get(get_conversations_url, headers=headers)
    conversations_data = response.json()

    latest_conversation = None
    for conversation in conversations_data['payload']:
        if conversation['inbox_id'] == int(inbox_id):
            latest_conversation = conversation
            break

    return latest_conversation

def request_contact_search(user_id, api_access_token):
    contact_search_url = f"{CHAT_API_URL}/contacts/filter"
    contact_search_payload = {
        "payload": [
            {
                "attribute_key": "viberid",
                "filter_operator": "equal_to",
                "values": [user_id]
            }
        ]
    }
    headers = get_headers(api_access_token=api_access_token)

    response = requests.post(contact_search_url, json=contact_search_payload, headers=headers)
    return response.json()

def email_contact_search(message_text, api_access_token):
    email_contact_search_url = f"{CHAT_API_URL}/contacts/filter"
    email_contact_search_payload = {
        "payload": [
            {
                "attribute_key": "email",
                "filter_operator": "equal_to",
                "values": [message_text]
            }
        ]
    }
    headers = get_headers(api_access_token=api_access_token)

    response = requests.post(email_contact_search_url, json=email_contact_search_payload, headers=headers)
    return response.json()

def handle_team_availability(email, team_structure):
    if email in team_structure:
        response = {}
        for key in team_structure[email]:
            target_email = team_structure[email][key]
            availability, available_name, agent_id = get_availability(target_email, CHAT_API_ACCESS_TOKEN, CHAT_API_URL)
            response[key] = {
                "email": target_email,
                "status": availability,
                "name": available_name,
                "id": agent_id,
            }
        return response
    else:
        return {'error': 'Email not found'}
    
def get_owner_by_email(owner_email):
    team_structure = get_team_structure()
    
    if owner_email in team_structure:
        response_data = handle_team_availability(owner_email, team_structure)

        if "am" in response_data:
            am_data = response_data["am"]
            owner_name = am_data["name"]
            owner_id = am_data["id"]
            owner_status = am_data["status"]
        else:
            owner_name = None
            owner_id = None
            owner_status = None

        if "ta" in response_data:
            ta_data = response_data["ta"]
            owner_ta_name = ta_data["name"]
            owner_ta_id = ta_data["id"]
            owner_ta_status = ta_data["status"]
        else:
            owner_ta_name = None
            owner_ta_id = None
            owner_ta_status = None

        return owner_id, owner_name, owner_status, owner_ta_name, owner_ta_id, owner_ta_status

    else:
        print(f"Email not found: {owner_email}")  # Debugging line
        return None, None, None, None, None, None

def get_user_id_by_email(email, api_access_token):
    user_search_url = f"{CHAT_API_URL}/agents/filter"
    user_search_payload = {
        "payload": [
            {
                "attribute_key": "email",
                "filter_operator": "equal_to",
                "values": [email]
            }
        ]
    }
    headers = get_headers(api_access_token=api_access_token)

    response = requests.post(user_search_url, json=user_search_payload, headers=headers)
    user_data = response.json()
    if user_data['meta']['count'] > 0:
        return user_data['payload'][0]['id']
    else:
        return None
import requests
import os
import json
from team import get_availability, get_team_structure
from gpt import user_chat_histories

# Constants
CHAT_API_ACCESS_TOKEN = os.environ['CHAT_API_ACCESS_TOKEN']
VIBER_API_URL = os.environ['VIBER_API_URL']
X_VIBER_AUTH_TOKEN = os.environ['X_VIBER_AUTH_TOKEN']
CHAT_API_URL = os.environ['CHAT_API_URL']
SLACK_TOKEN = os.environ['SLACK_TOKEN']
CCCONSOLE_API_TOKEN = os.environ['CCCONSOLE_API_TOKEN']

def get_headers(api_access_token=None, viber_auth_token=None):
    headers = {"Content-Type": "application/json"}
    
    if api_access_token:
        headers["api_access_token"] = api_access_token
        
    if viber_auth_token:
        headers["X-Viber-Auth-Token"] = viber_auth_token
        
    return headers

def formatHistory(user_id):
    chat_history = user_chat_histories.get(user_id, [])

    # Convert the chat history into a human-readable format
    formatted_chat_history = ""
    for entry in chat_history:
        formatted_chat_history += f"*{entry['role'].capitalize()}*: {entry['content']}\n\n"
    return formatted_chat_history

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

def update_contact_viber_id(contact_id, viber_id, api_access_token):
    update_contact_url = f"{CHAT_API_URL}/contacts/{contact_id}"
    update_contact_payload = {
        "custom_attributes": {
            "viberid": viber_id
        }
    }
    headers = get_headers(api_access_token=api_access_token)

    requests.put(update_contact_url, json=update_contact_payload, headers=headers)

def update_contact_bot_conversation(contact_id, api_access_token, bot_conversation):
    update_contact_url = f"{CHAT_API_URL}/contacts/{contact_id}"
    update_contact_payload = {
        "custom_attributes": {
            "bot_conversation": bot_conversation
        }
    }
    headers = get_headers(api_access_token=api_access_token)

    requests.put(update_contact_url, json=update_contact_payload, headers=headers)

def update_contact_owner(contact_id, api_access_token, owner_email, owner_name, owner_phone, plan, owenr_avatar, contact_domain):
    update_contact = f"{CHAT_API_URL}/contacts/{contact_id}"
    update_contact_payload = {
        "additional_attributes": {
            "description": "",
            "company_name": contact_domain,
            "social_profiles": {
                "github": "",
                "twitter": "",
                "facebook": "",
                "linkedin": ""
                }
        },
        "custom_attributes": {
            "role": owner_email,
            "owner": owner_name,
            "owner_email": owner_email,
            "owner_phone": owner_phone,
            "pricingPlan": plan,
            "owenr_avatar": owenr_avatar
        }
    }
    headers = get_headers(api_access_token=api_access_token)
    response = requests.put(update_contact, json=update_contact_payload, headers=headers)
    # print(response)
    return response.json()

def create_contact_owner(cc_contact_id, contact_name, contact_email, contact_phone, api_access_token, owner_email, owner_name, owner_phone, plan, owenr_avatar, contact_domain):
    create_contact = f"{CHAT_API_URL}/contacts"
    create_contact_payload = {
        "inbox_id": 14,
        "name": contact_name,
        "email": contact_email,
        "phone_number": contact_phone,
        "identifier": cc_contact_id,
        "additional_attributes": {
            "description": "",
            "company_name": contact_domain,
            "social_profiles": {
                "github": "",
                "twitter": "",
                "facebook": "",
                "linkedin": ""
                }
        },
        "custom_attributes": {
            "role": owner_email,
            "owner": owner_name,
            "owner_email": owner_email,
            "owner_phone": owner_phone,
            "pricingPlan": plan,
            "owenr_avatar": owenr_avatar
        }
    }
    headers = get_headers(api_access_token=api_access_token)

    response = requests.post(create_contact, json=create_contact_payload, headers=headers)
    
    return response.json()

def create_conversation(contact_id, inbox_id, owner_id, api_access_token):
    create_conversation_url = f"{CHAT_API_URL}/conversations"
    create_conversation_payload = {
        "contact_id": contact_id,
        "inbox_id": inbox_id,
        "assignee_id": owner_id
    }

    headers = {
        "Content-Type": "application/json",
        "api_access_token": api_access_token
    }

    response = requests.post(create_conversation_url, json=create_conversation_payload, headers=headers)
    return response.json()

def toggle_conversation(latest_conversation, api_access_token):
    get_url = f"{CHAT_API_URL}/conversations/{latest_conversation['id']}"
    toggle_url = f"{CHAT_API_URL}/conversations/{latest_conversation['id']}/toggle_status"
    headers = {
        "Content-Type": "application/json",
        "api_access_token": api_access_token
    }

    # Get conversation details
    response = requests.get(get_url, headers=headers)
    conversation_data = response.json()

    # Check current status
    current_status = conversation_data.get('status')
    # Toggle status
    new_status = 'resolved' if current_status == 'open' else 'open'
    payload = {
        "status": new_status
    }
    # Update conversation status
    response = requests.post(toggle_url, json=payload, headers=headers)
    # print(response)
    return response


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

def chat_message_send(message_text, latest_conversation, private_msg, type):
    # Create a message in the conversation
    message_create_url = f"{CHAT_API_URL}/conversations/{latest_conversation['id']}/messages"
    message_create_payload = {
        "content": message_text,
        "message_type": type,
        "private": private_msg
    }
    headers = {
        "Content-Type": "application/json",
        "api_access_token": CHAT_API_ACCESS_TOKEN
    }
    response = requests.post(message_create_url, json=message_create_payload, headers=headers)
    return response


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
        #print(f"Email not found: {owner_email}")  # Debugging line
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
    
def get_slack_users(assignee_email, latest_conversation):
    # Replace 'your_bot_token' with your bot's OAuth access token

    headers = {
        'Authorization': f'Bearer {SLACK_TOKEN}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    params = {
        'email': assignee_email
    }

    response = requests.get('https://slack.com/api/users.lookupByEmail', headers=headers, params=params)

    # Check if the API request was successful
    if response.status_code == 200:
        data = response.json()

        if data['ok']:
            slack_userName = data['user']['name']
            slack_userId = data['user']['id']
            send_slack_message(slack_userName, slack_userId, latest_conversation)
            return slack_userName, slack_userId
            
        else:
            # print(f"Error: {data['error']}")
            return None
    else:
        #print(f"Request failed with status code: {response.status_code}")
        return None
    

def send_slack_message(slack_userName, slack_userId, latest_conversation):
    #print(f"Sending slack, {slack_userName}, {slack_userId}")
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "channel": f"@{slack_userName}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<@{slack_userId}>, Имаш нов/отворен чат :loud_sound:*"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Към чата",
                            "emoji": True
                        },
                        
                        "url": f"https://chat.cloudcart.com/app/accounts/1/inbox/14/conversations/{latest_conversation}",
                        
                        "action_id": "button-action"
                    }
                ]
            }
        ]
    }
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=json.dumps(payload))

    return response

def get_cloudcart_user_info(user_email):
    headers = {
        'Content-Type': 'application/json',
        'Webhook-Api-Key': CCCONSOLE_API_TOKEN
    }
    params = {
        'email': user_email
    }
    response = requests.get('https://console.cloudcart.com/webhooks/lead', headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error: API request failed with status code {response.status_code}")
        return {}

    data = response.json()

    if not isinstance(data, dict):
        print(f"Error: Unexpected API response, expected a dictionary but got {type(data)}")
        return {}

    return data


        
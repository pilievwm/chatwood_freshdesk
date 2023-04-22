import os
import re
import time
import requests
from flask import jsonify
from team import handle_team_availability, get_team_structure, get_availability


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

def send_viber_url_message(user_id, message_url):
    send_message_url = f"{VIBER_API_URL}/send_message"
    send_message_payload = {
        "receiver": user_id,
        "type": "url",
        "min_api_version": 7,
        "media": message_url
    }
    headers = get_headers(viber_auth_token=X_VIBER_AUTH_TOKEN)

    response = requests.post(send_message_url, json=send_message_payload, headers=headers)
    return response.status_code, response.text

def send_viber_message(user_id, message_text):
    send_message_url = f"{VIBER_API_URL}/send_message"
    send_message_payload = {
        "receiver": user_id,
        "type": "text",
        "min_api_version": 7,
        "text": message_text
    }
    headers = get_headers(viber_auth_token=X_VIBER_AUTH_TOKEN)

    response = requests.post(send_message_url, json=send_message_payload, headers=headers)
    return response.status_code, response.text

def send_personalized_viber_message(user_id, contact_name):
    message_text = f"{contact_name} Моля, изберете една от следните опции, за да можем да Ви съдействаме:"
    send_message_payload = {
        "receiver": user_id,
        "min_api_version": 7,
        "type": "text",
        "text": message_text,
        "keyboard": {
            "Type": "keyboard",
            "DefaultHeight": False,
            "Buttons": [
                {
                    "ActionType": "reply",
                    "ActionBody": f"Искам да се свържа с моя акаунт мениджър",
                    "Text": f"Искам да се свържа с моя акаунт мениджър",
                    "TextSize": "regular",
                    "Columns": 3, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#d3b8ff" # Blue color
                },
                {
                    "ActionType": "reply",
                    "ActionBody": "Искам да се свържа с техническия екип",
                    "Text": "Искам да се свържа с техническия екип",
                    "TextSize": "regular",
                    "Columns": 3, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#ffd6b8" # Yellow color
                }
            ]
        }
    }

    headers = get_headers(viber_auth_token=X_VIBER_AUTH_TOKEN)
    response = requests.post(VIBER_API_URL + "/send_message", json=send_message_payload, headers=headers)
    return response.status_code, response.text

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

def process_viber_request(request):
    data = request.json
    event = data.get("event")
    

    if event == "webhook":
        return '', 200

    if event == "message":
        user_key = 'sender'
    elif event == "conversation_started":
        user_key = 'user'
    else:
        return jsonify({'status': 'ignored'})

    if user_key not in data:
        print(f"No {user_key} information in the received data.")
        return '', 400

    user_id = data[user_key]['id']
    message_text = data['message']['text'] if event == "message" else None

    response_data = request_contact_search(user_id, CHAT_API_ACCESS_TOKEN)
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    contact = None

    if response_data['meta']['count'] == 0:
        if re.fullmatch(email_regex, message_text):
            email_contact_search_data = email_contact_search(message_text, CHAT_API_ACCESS_TOKEN)

            if email_contact_search_data['meta']['count'] > 0:
                contact = email_contact_search_data['payload'][0]
                contact_id = contact['id']

                send_personalized_viber_message(user_id)
                update_contact_viber_id(contact_id, user_id, True, CHAT_API_ACCESS_TOKEN)
            else:
                message_text = f"Не е открит потребител с този имейл: {message_text}. Моля, опитайте отново."
                status_code, response_text = send_viber_message(user_id, message_text)
                print(f"Viber API response status code: {status_code}")
                print(f"Viber API response content: {response_text}")
        else:
            message_text = "Здравейте, моля, изпратете ни Вашия имейл, който ползвате за вход в административния панел на магазина"
            status_code, response_text = send_viber_message(user_id, message_text)
            print(f"Viber API response status code: {status_code}")
            print(f"Viber API response content: {response_text}")
    else:
        contact = response_data['payload'][0]
        contact_name = contact['name']
        pricing_plan = contact['custom_attributes'].get('pricingPlan')
        if pricing_plan not in ['cc-employees1', 'enterprise1', 'business1']:
            message_text = f"{contact_name}, за съжаление Вашият абонаментен план *{pricing_plan}* не включва чат поддръжка. \n\nТук можете да се запознаете с цените на нашите абонаментни планове:"
            status_code, response_text = send_viber_message(user_id, message_text)

            # Add a delay between messages
            time.sleep(2)

            message_url = "https://cloudcart.com/bg/pricing?utm_source=viberBot"
            status_code, response_text = send_viber_url_message(user_id, message_url)

        else:
            contact_id = contact['id']
            inbox_id = "14"  # Replace this value with your desired fixed ID

            # Get conversations
            get_conversations_url = f"{CHAT_API_URL}/contacts/{contact_id}/conversations"
            headers = {
                "Content-Type": "application/json",
                "api_access_token": CHAT_API_ACCESS_TOKEN
            }
            get_conversations_response = requests.get(get_conversations_url, headers=headers)
            conversations_data = get_conversations_response.json()

            # Check if a conversation exists for the specified inbox_id
            latest_conversation = get_latest_conversation(contact_id, inbox_id, CHAT_API_ACCESS_TOKEN)

            # If no conversation exists, create a new one
            if latest_conversation is None:
                latest_conversation = create_conversation(contact_id, inbox_id, CHAT_API_ACCESS_TOKEN)

            if latest_conversation is not None:
                # Get the status of the conversation
                conversation_status = latest_conversation['status']

                # If the conversation is not open, send the personalized Viber message
                if conversation_status != "open":
                    send_personalized_viber_message(user_id)

                # Create a message in the conversation
                message_create_url = f"{CHAT_API_URL}/conversations/{latest_conversation['id']}/messages"
                message_create_payload = {
                    "content": message_text,
                    "message_type": "incoming",
                    "private": False
                }

                headers = {
                    "Content-Type": "application/json",
                    "api_access_token": CHAT_API_ACCESS_TOKEN
                }

                requests.post(message_create_url, json=message_create_payload, headers=headers)
                


    owner_ta_id = None
    owner_id = None
    action_body = data['message']['text']

    if contact is not None:
        owner_email = contact['custom_attributes']['owner_email']
        pricing_plan = contact['custom_attributes'].get('pricingPlan')

        owner_id, owner_name, owner_status, owner_ta_name, owner_ta_id, owner_ta_status = get_owner_by_email(owner_email)

        if action_body == "Искам да се свържа с моя акаунт мениджър":
            if owner_id is not None:
                if owner_status == "online":
                    status_code, response_text = send_viber_message(user_id, f"Разговорът е насочен към Вашия акаунт мениджър {owner_name}. \n\nМоля, опишете подробно въпроса, който имате.")
                else:
                    status_code, response_text = send_viber_message(user_id, f"Вашият акаунт мениджър {owner_name} в момента не е на линия. Ще се свърже с вас при първа възможност. \n\nМоля, опишете подробно въпроса, който имате.")
            else:
                print(f"Failed to find user with email {owner_email}.")

            if action_body == "Искам да се свържа с моя акаунт мениджър":
                assignee_id = owner_id
            elif action_body == "Искам да се свържа с техническия екип":
                print("Assigning to technical assistant")
                assignee_id = owner_ta_id
            else:
                print("No assignment")
                assignee_id = None

            if assignee_id is not None:
                print(f"Assigning conversation {latest_conversation['id']} to {assignee_id}")
                assign_conversation(latest_conversation['id'], assignee_id, CHAT_API_ACCESS_TOKEN)

        elif action_body == "Искам да се свържа с техническия екип":
            # Handle the action for connecting with the technical team here
            if owner_ta_id is not None:
                if owner_status == "online":
                    status_code, response_text = send_viber_message(user_id, f"Свързвам ви с технически асистент {owner_ta_name}. \n\nМоля, опишете подробно въпроса, който имате.")
                else:
                    status_code, response_text = send_viber_message(user_id, f"Вашият технически асистент {owner_ta_name} в момента не е на линия. \n\nМоля, опишете подробно въпроса, който имате.")
            else:
                print(f"Failed to find user with email {owner_email}.")

            # Assign the conversation to the owner or the technical assistant
            
            if action_body == "Искам да се свържа с моя акаунт мениджър":
                print("Reassigning to sales owner")
                assignee_id = owner_id
            elif action_body == "Искам да се свържа с техническия екип":
                print("Assigning to technical assistant")
                assignee_id = owner_ta_id
            else:
                print("No assignment")
                assignee_id = None

            if assignee_id is not None:
                print(f"Assigning conversation {latest_conversation['id']} to {assignee_id}")
                assign_conversation(latest_conversation['id'], assignee_id, CHAT_API_ACCESS_TOKEN)

            

    return jsonify({'status': 'success'})

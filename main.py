import os
import re
import time
import requests
from flask import jsonify
from chatHelpers import *
from viber_msg import *


# Constants
CHAT_API_ACCESS_TOKEN = os.environ['CHAT_API_ACCESS_TOKEN']
VIBER_API_URL = os.environ['VIBER_API_URL']
X_VIBER_AUTH_TOKEN = os.environ['X_VIBER_AUTH_TOKEN']
CHAT_API_URL = os.environ['CHAT_API_URL']


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
    if event == "message":
        message_type = data['message'].get('type', 'text')
        if message_type == 'text':
            message_text = data['message']['text']
        elif message_type == 'picture' or message_type == 'video':
            message_media_url = data['message']['media']
        else:
            message_text = None
            message_media_url = None
    else:
        message_text = None
        message_media_url = None

    response_data = request_contact_search(user_id, CHAT_API_ACCESS_TOKEN)
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    contact = None
    latest_conversation = None

    if response_data['meta']['count'] == 0:
        if re.fullmatch(email_regex, message_text):
            email_contact_search_data = email_contact_search(message_text, CHAT_API_ACCESS_TOKEN)

            if email_contact_search_data['meta']['count'] > 0:
                contact = email_contact_search_data['payload'][0]
                contact_id = contact['id']
                contact_name = contact['name']
                send_personalized_viber_message(user_id, contact_name)
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
        if pricing_plan not in ['cc-employees', 'enterprise', 'business']:
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
                    send_personalized_viber_message(user_id, contact_name)

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
            if latest_conversation and (owner_id is not None or owner_ta_id is not None):
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
            if latest_conversation and (owner_id is not None or owner_ta_id is not None):
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
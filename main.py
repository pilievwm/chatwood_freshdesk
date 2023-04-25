import os
import re
import time
import requests
from flask import jsonify
from chatHelpers import *
from viber_msg import *
from gpt import *
from searchBot import *




# Constants
CHAT_API_ACCESS_TOKEN = os.environ['CHAT_API_ACCESS_TOKEN']
VIBER_API_URL = os.environ['VIBER_API_URL']
X_VIBER_AUTH_TOKEN = os.environ['X_VIBER_AUTH_TOKEN']
CHAT_API_URL = os.environ['CHAT_API_URL']

ACCEPTED_PLANS = ['cc-employees1', 'enterprise', 'business']
MESSAGE_DELAY = 2
TIME_THRESHOLD = 3000
MAX_SEARCH_RESULTS = 1

def send_pricing_plan_message(user_id, contact_name, pricing_plan, delay=None):
    message_text = f"{contact_name}, за съжаление Вашият абонаментен план *{pricing_plan}* не включва чат поддръжка. \n\nТук можете да се запознаете с цените на нашите абонаментни планове:"
    status_code, response_text = send_viber_message(user_id, message_text)

    if MESSAGE_DELAY:
        time.sleep(MESSAGE_DELAY)

    message_url = "https://cloudcart.com/bg/pricing?utm_source=viberBot"
    status_code, response_text = send_viber_url_message(user_id, message_url)


def send_email_not_found_message(user_id, email):
    message_text = f"Не е открит потребител с този имейл: {email}. Моля, опитайте отново."
    status_code, response_text = send_viber_message(user_id, message_text)
    print(f"Viber API response status code: {status_code}")
    print(f"Viber API response content: {response_text}")


def send_message_to_user(user_id, message_text):
    status_code, response_text = send_viber_message(user_id, message_text)
    print(f"Viber API response status code: {status_code}")
    print(f"Viber API response content: {response_text}")


def send_message_to_user(user_id, message_text):
    status_code, response_text = send_viber_message(user_id, message_text)
    print(f"Viber API response status code: {status_code}")
    print(f"Viber API response content: {response_text}")

def create_or_get_latest_conversation(contact_id, inbox_id, api_access_token):
    latest_conversation = get_latest_conversation(contact_id, inbox_id, api_access_token)
    if latest_conversation is None:
        latest_conversation = create_conversation(contact_id, inbox_id, api_access_token)
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

    current_time = int(time.time()*1000)
    message_timestamp = data['timestamp']

    if current_time - message_timestamp > TIME_THRESHOLD:
        print(f"Ignoring old message with timestamp {message_timestamp}")
        return jsonify({'status': 'ignored'})    

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
                pricing_plan = contact['custom_attributes'].get('pricingPlan')

                if pricing_plan not in ACCEPTED_PLANS:
                    update_contact_viber_id(contact_id, user_id, True, CHAT_API_ACCESS_TOKEN)
                    gpt_response = generate_response_for_bad_pricing_plans(user_id, contact_name, search_result=None, message_text=f"Здравейте, какзвам се {contact_name}")
                    send_viber_message(user_id, gpt_response,sender_name="AI", sender_avatar="https://png.pngtree.com/png-clipart/20190419/ourmid/pngtree-rainbow-unicorn-image-png-image_959412.jpg")

                else:
                    send_personalized_viber_message(user_id, contact_name)
                    update_contact_viber_id(contact_id, user_id, True, CHAT_API_ACCESS_TOKEN)
            else:
                send_email_not_found_message(user_id, message_text)
        else:
            message_text = "Здравейте, моля, изпратете ни Вашия имейл, който ползвате за вход в административния панел на магазина"
            send_message_to_user(user_id, message_text)
    else:
        contact = response_data['payload'][0]
        contact_name = contact['name']
        pricing_plan = contact['custom_attributes'].get('pricingPlan')
        
        # Todo: Add external source for controlling the accepted plans
        if pricing_plan not in ACCEPTED_PLANS:
            # send_pricing_plan_message(user_id, contact_name, pricing_plan, MESSAGE_DELAY)
            search_result = answer_bot(message_text, num_results=MAX_SEARCH_RESULTS)
            print(f"\n\nНамерен резултат: {search_result}\n\n")
            gpt_response = generate_response_for_bad_pricing_plans(user_id, search_result, message_text, contact_name)

            # Analyze the response
            analyzer_response = analyze_response(gpt_response)

            # Process the analyzer's response
            conversation_ended = process_analyzer_response(analyzer_response, user_id)

            # If the conversation has ended, call finalize_ai_conversation_viber_message
            if conversation_ended:
                finalize_ai_conversation_viber_message(user_id, gpt_response, sender_name="AI", sender_avatar="https://png.pngtree.com/png-clipart/20190419/ourmid/pngtree-rainbow-unicorn-image-png-image_959412.jpg")
            else:
                send_viber_message(user_id, gpt_response, sender_name="AI", sender_avatar="https://png.pngtree.com/png-clipart/20190419/ourmid/pngtree-rainbow-unicorn-image-png-image_959412.jpg")




        else:
            contact_id = contact['id']
            inbox_id = "14"  # Replace this value with your desired fixed ID

            # Get or create the conversation
            latest_conversation = create_or_get_latest_conversation(contact_id, inbox_id, CHAT_API_ACCESS_TOKEN)

            if latest_conversation is not None:
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

        assignee_id = None  # Initialize assignee_id
        
        if latest_conversation and (owner_id is not None or owner_ta_id is not None):
            if action_body == "Искам да се свържа с моя акаунт мениджър":
                if owner_id is not None:
                    if owner_status == "online":
                        send_viber_message(user_id, f"Разговорът е насочен към Вашия акаунт мениджър {owner_name}. \n\nМоля, изчакайте")
                    else:
                        send_viber_message(user_id, f"Препратихме съобщението Ви към Вашият акаунт мениджър. \n\n{owner_name} в момента не е на линия но ще се свърже с Вас при първа възможност.")
                        if MESSAGE_DELAY:
                            time.sleep(MESSAGE_DELAY)
                            handle_ai_help_request(user_id)
                else:
                    print(f"Failed to find user with email {owner_email}.")
                assignee_id = owner_id

            elif action_body == "Искам да се свържа с техническия екип":
                if owner_ta_id is not None:
                    if owner_ta_status == "online":
                        send_viber_message(user_id, f"Свързвам ви с технически асистент {owner_ta_name}. \n\nМоля, изчакайте.")
                    else:
                        send_viber_message(user_id, f"Препратихме съобщението Ви към технически асистент. \n\n{owner_ta_name} в момента не е на линия но ще се свърже с Вас при първа възможност.")
                        if MESSAGE_DELAY:
                            time.sleep(MESSAGE_DELAY)
                            handle_ai_help_request(user_id)
                else:
                    print(f"Failed to find user with email {owner_email}.")
                assignee_id = owner_ta_id

            if assignee_id is not None:
                print(f"Assigning conversation {latest_conversation['id']} to {assignee_id}")
                assign_conversation(latest_conversation['id'], assignee_id, CHAT_API_ACCESS_TOKEN)
    
    ### If user without plan decide to start a new AI session ###
    if action_body == "имам въпрос на различна тема":
        # Call the function to wipe user_chat_histories
        wipe_user_chat_history(user_id)

        # Send a Viber message asking the user to ask a new question
        gpt_response = generate_response_for_bad_pricing_plans(user_id, contact_name, search_result="", message_text=message_text)

    return jsonify({'status': 'success'})
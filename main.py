import os
import re
import time
import requests
from flask import current_app, Flask, jsonify
from chatHelpers import *
from viber_msg import *
from gpt import (
    generate_response_for_bad_pricing_plans, 
    analyze_response, 
    process_analyzer_response, 
    wipe_user_chat_history)
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

# Constants
CHAT_API_ACCESS_TOKEN = os.environ['CHAT_API_ACCESS_TOKEN']
VIBER_API_URL = os.environ['VIBER_API_URL']
X_VIBER_AUTH_TOKEN = os.environ['X_VIBER_AUTH_TOKEN']
CHAT_API_URL = os.environ['CHAT_API_URL']

ACCEPTED_PLANS = ['cc-employees', 'enterprise', 'business']
MESSAGE_DELAY = 2
TIME_THRESHOLD = 5000
MAX_SEARCH_RESULTS = 3

# Global variable to store the last message for each user
last_messages = {}
continue_checking = {}
message_timestamps = {}
message_counters = {}

def async_main():
    process_viber_request

def should_trigger_event(user_id, interval=30):
    while continue_checking.get(user_id, False):
        current_time = time.time()
        last_message_time = last_message_timestamps.get(user_id)

        if last_message_time and current_time - last_message_time >= interval:
            stop_viber_typing_status()
            print("async sent request to stop typing")
            break  # Exit the loop once the condition is met

        time.sleep(1)  # Sleep for 1 second before checking again



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


def send_message_to_user(user_id, message_text):
    status_code, response_text = send_viber_message(user_id, message_text)

def talk_to_ta(user_id, latest_conversation, owner_ta_status, owner_ta_name, owner_ta_id, message_text):
    if owner_ta_id is not None:
        if owner_ta_status == "online":
            send_viber_message(user_id, f"Свързвам ви с технически асистент {owner_ta_name}. \n\nМоля, изчакайте.")
            assignee_id = owner_ta_id
            assign_conversation(latest_conversation['id'], assignee_id, CHAT_API_ACCESS_TOKEN)

        else:
            first_name = owner_ta_name.split(' ')[0]
            send_viber_message(user_id, f"Свързах Ви в чат сесия с {owner_ta_name}. Тъй като той не е на разположение в момента, моля, оставете своето съобщение тук. \n\n{first_name} ще се свърже с Вас, веднага щом бъде на линия. \n\nБлагодарим за търпението!")
            print("TA Offline")
            assignee_id = owner_ta_id
            assign_conversation(latest_conversation['id'], assignee_id, CHAT_API_ACCESS_TOKEN)

            initiate_close_chat_viber_message(user_id, message_text=" ")

    else:
        print(f"Failed to find user with email {owner_ta_name}.")


def talk_to_am(user_id, latest_conversation, owner_id, owner_status, owner_name, message_text, owner_email):
    if owner_id is not None:
        if owner_status == "online":
            send_viber_message(user_id, message_text=f"Разговорът е насочен към Вашия акаунт мениджър {owner_name}. \n\nМоля, изчакайте!")

        else:
            first_name = owner_name.split(' ')[0]
            send_viber_message(user_id, message_text=f"Свързах Ви в чат сесия с {owner_name}. Тъй като той не е на разположение в момента, моля, оставете своето съобщение тук. \n\n{first_name} ще се свърже с Вас, веднага щом бъде на линия. \n\nБлагодарим за търпението!")
            print("AM Offline")
            assignee_id = owner_id
            assign_conversation(latest_conversation['id'], assignee_id, CHAT_API_ACCESS_TOKEN)
            print("AM Offline")
            initiate_close_chat_viber_message(user_id, message_text=" ")

            
    else:
        print(f"Failed to find user with email {owner_name}.")


def create_or_get_latest_conversation(contact_id, inbox_id, api_access_token):
    latest_conversation = get_latest_conversation(contact_id, inbox_id, api_access_token)
    if latest_conversation is None:
        latest_conversation = create_conversation(contact_id, inbox_id, api_access_token)
    return latest_conversation


def process_viber_request(request_data, app):
    with app.app_context():
        data = request_data
        event = data.get("event")

        if event == "webhook":
            return '', 200

        if event == "message":
            print(1)
            user_key = 'sender'
        elif event == "conversation_started":
            print(2)
            user_key = 'user'
            visitor_name = data[user_key]['name']
            welcome_message = send_welcome_message(visitor_name)
            return jsonify(welcome_message), 200

        else:
            print(3)
            return jsonify({'status': 'ignored'})

        if user_key not in data:
            print(f"No {user_key} information in the received data.")
            return '', 400
        print(4)
        user_id = data[user_key]['id']
        print(user_id)
        # Throttle check
        current_time = time.time()
        if user_id in message_timestamps and current_time - message_timestamps[user_id] < 1:
            message_counters[user_id] += 1
            if message_counters[user_id] > 3:
                return jsonify({'status': 'throttled'}), 429
        else:
            message_timestamps[user_id] = current_time
            message_counters[user_id] = 1

        if event == "message":
            message_type = data['message'].get('type', 'text')
            if message_type == 'text':
                message_text = data['message']['text']

                # Check if the message is equal to the previous one
                if user_id in last_messages and message_text == last_messages[user_id]:
                    return jsonify({'status': 'message_skipped'}), 200
                else:
                    last_messages[user_id] = message_text

            elif message_type == 'picture' or message_type == 'video':
                message_media_url = data['message']['media']
            else:
                message_text = None
                message_media_url = None
        else:
            message_text = None
            message_media_url = None


################################# RECEIVING AND PROCESSING THE VIBER MESSAGE #################################
     
        response_data = request_contact_search(user_id, CHAT_API_ACCESS_TOKEN)

        ################################# CHECK IF THERE IS SUCH USER AT CHATWOOT #################################
        if response_data['payload']:
            contact = response_data['payload'][0]
            pricing_plan = contact['custom_attributes'].get('pricingPlan')
            latest_conversation = None


    
            ################################# IF PLAN IS VALID #################################

            if pricing_plan in ACCEPTED_PLANS:
                action_body = data['message']['text']
                contact_name = contact['name']
                owner_email = contact['custom_attributes']['owner_email']
                bot_conversation = contact['custom_attributes'].get('bot_conversation')
                contact_id = contact['id']
                inbox_id = "14"  # Replace this value with your desired fixed ID

                assignee_id = None  # Initialize assignee_id    
                # Get or create the conversation
                
                latest_conversation = create_or_get_latest_conversation(contact_id, inbox_id, CHAT_API_ACCESS_TOKEN)
                owner_id, owner_name, owner_status, owner_ta_name, owner_ta_id, owner_ta_status = get_owner_by_email(owner_email)
                print("check completed!")
                for _ in range(1):  
                    print("enter the loop")
                    if latest_conversation and (owner_id is not None or owner_ta_id is not None):
                        combined_text = formatHistory(user_id)
                        print("check pricing plans")
                        ####### When user decide to talk with AM from the viber message ######
                        if (action_body == "Искам да се свържа с моя акаунт мениджър" and bot_conversation is None) or (action_body == "Искам да се свържа с моя акаунт мениджър" and bot_conversation == "No") or (action_body == "Искам да се свържа с моя акаунт мениджър" and bot_conversation == "Yes"):
                            print(f"Case 1 {action_body} - Bot conv: {bot_conversation}")
                            if owner_id is not None:
                                print("Case 1 has owner ID")
                                talk_to_am(user_id, latest_conversation, owner_id, owner_status, owner_name, message_text, owner_email)
                                chat_message_send(message_text, latest_conversation, False, type="incoming")
                                
                                if combined_text is not None:
                                    chat_message_send(combined_text, latest_conversation, True, type="outgoing")
                                    wipe_user_chat_history(user_id)
                                        
                        # When user decide to talk with his personal Technical assistant
                        elif action_body == "Искам да говоря с технически асистент" and bot_conversation == "Yes":
                            print(f"Case 2 {action_body} - Bot conv: {bot_conversation}")
                            talk_to_ta(user_id, latest_conversation, owner_ta_status, owner_ta_name, owner_ta_id, message_text)
                            toggle_conversation(latest_conversation, CHAT_API_ACCESS_TOKEN) 
                            chat_message_send(message_text, latest_conversation, False, type="incoming")
                                # Add bot conversation as private note
                            if combined_text is not None:
                                    chat_message_send(combined_text, latest_conversation, True, type="outgoing")
                                    wipe_user_chat_history(user_id)
                        
                        ### If user without plan decide to start a new AI session ###
                        elif action_body == "Имам въпрос на различна тема" and bot_conversation == "Yes":
                            print(f"Case 3 {action_body} - Bot conv: {bot_conversation}")
                            update_contact_bot_conversation(contact_id, CHAT_API_ACCESS_TOKEN, bot_conversation="Yes")

                            # Add bot conversation as private note
                            if combined_text is not None:
                                    chat_message_send(combined_text, latest_conversation, True, type="outgoing")

                            # Call the function to wipe user_chat_histories
                            wipe_user_chat_history(user_id)
                            search_result = ""
                            # Send a Viber message asking the user to ask a new question
                            # gpt_response = generate_response_for_bad_pricing_plans(user_id, search_result, message_text, contact_name)
                            gpt_response = f"{contact_name}, какъв е Вашият въпрос? Моля опишете го възможно най-добре"
                            send_viber_message(user_id, gpt_response, sender_name="CloudCart AI assistant", sender_avatar="https://png.pngtree.com/png-clipart/20190419/ourmid/pngtree-rainbow-unicorn-image-png-image_959412.jpg")
                        
                        ####### When user decide to talk with Technical assistant support team ######
                        elif action_body == "Имам въпрос свързан с работата на платформата" or action_body == "Имам още въпроси по темата" or bot_conversation == "Yes":
                            print(f"Case 4 {action_body} - Bot conv: {bot_conversation}")
                            update_contact_bot_conversation(contact_id, CHAT_API_ACCESS_TOKEN, bot_conversation="Yes")
                            if action_body == "Имам още въпроси по темата":
                                send_viber_message(user_id, message_text="Моля, продължете с въпросите по темата...", sender_name="CloudCart AI assistant", sender_avatar="https://png.pngtree.com/png-clipart/20190419/ourmid/pngtree-rainbow-unicorn-image-png-image_959412.jpg")
                            elif owner_ta_id is not None:
                                # send_pricing_plan_message(user_id, contact_name, pricing_plan, MESSAGE_DELAY)
                                send_viber_typing_status(user_id, sender_name="CloudCart AI assistant", sender_avatar="https://png.pngtree.com/png-clipart/20190419/ourmid/pngtree-rainbow-unicorn-image-png-image_959412.jpg")
                                socketio.start_background_task(should_trigger_event, user_id)
                                from searchDB import answer_db
                                from searchBot import answer_bot
                                # search_result = None
                                # search_result = answer_db(message_text)
                                search_result = answer_bot(message_text, num_results=MAX_SEARCH_RESULTS)
                                print(f"\n\nНамерен резултат: {search_result}\n\n")
                                gpt_response = generate_response_for_bad_pricing_plans(user_id, search_result, message_text, contact_name)


                                # Analyze the response
                                # analyzer_response = analyze_response(gpt_response)

                                # Process the analyzer's response
                                # conversation_ended = process_analyzer_response(analyzer_response, user_id)

                                # If the conversation has ended, call finalize_ai_conversation_viber_message
                                #if conversation_ended:
                                #    update_contact_bot_conversation(contact_id, CHAT_API_ACCESS_TOKEN,  bot_conversation="Maybe")
                                #else:
                                # send_viber_message(user_id, gpt_response, sender_name="CloudCart AI assistant", sender_avatar="https://png.pngtree.com/png-clipart/20190419/ourmid/pngtree-rainbow-unicorn-image-png-image_959412.jpg")                   
                                finalize_ai_conversation_before_real_human_viber_message(user_id, gpt_response, sender_name="CloudCart AI assistant", sender_avatar="https://png.pngtree.com/png-clipart/20190419/ourmid/pngtree-rainbow-unicorn-image-png-image_959412.jpg")

                        # Continues conversation with agent                
                        elif bot_conversation == "Human" and not action_body == "Прекрати чат сесията":
                            print(f"Case 5 {action_body} - Bot conv: {bot_conversation}")
                            chat_message_send(message_text, latest_conversation, False, type="incoming")
                        
                        # User intent to close chat session
                        elif action_body == "Прекрати чат сесията" and bot_conversation == "Human":
                            print(f"Case 6 {action_body} - Bot conv: {bot_conversation}")
                            chat_message_send(message_text=f"The chat was closed by the customer: {contact_name}", latest_conversation=latest_conversation, private_msg=True, type="outgoing")
                            toggle_conversation(latest_conversation, CHAT_API_ACCESS_TOKEN)     
                        else:
                            send_personalized_viber_message(user_id, contact_name)
                            print(f"ELSE Case 7 {action_body} - Bot conv: {bot_conversation}")
            
            
            ###################################### ELSE PLAN IS NOT VALID ###########################################
            
            else:
                contact = response_data['payload'][0]
                contact_name = contact['name']
                pricing_plan = contact['custom_attributes'].get('pricingPlan')
                print("Step 0")
                if "Искам да се свържа с моя акаунт мениджър" in message_text or "Искам да се свържа с техническия екип" in message_text:
                    message_text = "С кого разговарям?"
                if message_text == "Имам въпрос на различна тематика":
                    wipe_user_chat_history(user_id)

                print(f"Step 1 - Message: {message_text} Plan: {pricing_plan}")
                print(f"ACCEPTED_PLANS: {ACCEPTED_PLANS}, pricing_plan: {pricing_plan}")
                # Todo: Add external source for controlling the accepted plans
                if pricing_plan not in ACCEPTED_PLANS:
                    # send_pricing_plan_message(user_id, contact_name, pricing_plan, MESSAGE_DELAY)
                    print(f"Step 2 - Plan: {pricing_plan}")
                    send_viber_typing_status(user_id, sender_name="CloudCart AI assistant", sender_avatar="https://png.pngtree.com/png-clipart/20190419/ourmid/pngtree-rainbow-unicorn-image-png-image_959412.jpg")
                    socketio.start_background_task(should_trigger_event, user_id)
                    from searchBot import answer_db
                    from searchBot import answer_bot
                    search_result = answer_bot(message_text, num_results=MAX_SEARCH_RESULTS)
                    print(f"\n\nНамерен резултат: {search_result}\n\n")
                    gpt_response = generate_response_for_bad_pricing_plans(user_id, search_result, message_text, contact_name)

                    # Analyze the response
                    analyzer_response = analyze_response(gpt_response)
                    print(f"Step 3 - Analized: {analyzer_response}")
                    # Process the analyzer's response
                    conversation_ended = process_analyzer_response(analyzer_response, user_id)

                    # If the conversation has ended, call finalize_ai_conversation_viber_message
                    if conversation_ended:
                        print(f"Step 4 - Conversation ended: {conversation_ended}")
                        finalize_ai_conversation_viber_message(user_id, gpt_response, sender_name="CloudCart AI assistant", sender_avatar="https://png.pngtree.com/png-clipart/20190419/ourmid/pngtree-rainbow-unicorn-image-png-image_959412.jpg")
                    else:
                        print(f"Step 5 - Send viber message")
                        send_viber_message(user_id, gpt_response, sender_name="CloudCart AI assistant", sender_avatar="https://png.pngtree.com/png-clipart/20190419/ourmid/pngtree-rainbow-unicorn-image-png-image_959412.jpg")                
        
        
        ################################# ELSE THERE IS NO SUCH USER AT CHATWOOT #################################
        else:
            response_data = request_contact_search(user_id, CHAT_API_ACCESS_TOKEN)
            print("User is not found at Chatwoot")
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
                            # gpt_response = generate_response_for_bad_pricing_plans(user_id=user_id, contact_name=contact_name, search_result=None, message_text=f"Здравейте, какзвам се {contact_name}")
                            send_viber_message(user_id, message_text=f"Здравейте, {contact_name}, разговаряте с CloudCart AI асистент. С какво мога да ви съдействам?", sender_name="CloudCart AI assistant", sender_avatar="https://png.pngtree.com/png-clipart/20190419/ourmid/pngtree-rainbow-unicorn-image-png-image_959412.jpg")
                            print("Welcome user with selection, Plan: No Valid!")
                            update_contact_viber_id(contact_id, user_id, CHAT_API_ACCESS_TOKEN)
                            update_contact_bot_conversation(contact_id, CHAT_API_ACCESS_TOKEN,  bot_conversation="No")
                        else:
                            send_personalized_viber_message(user_id, contact_name)
                            print("Welcome user with selection, Plan: VALID!")
                            update_contact_viber_id(contact_id, user_id, CHAT_API_ACCESS_TOKEN)
                            update_contact_bot_conversation(contact_id, CHAT_API_ACCESS_TOKEN,  bot_conversation="No")
                    else:
                        send_email_not_found_message(user_id, message_text)
                else:
                    message_text = "Здравейте, моля, изпратете ни Вашия имейл, който ползвате за вход в административния панел на магазина"
                    send_message_to_user(user_id, message_text)

        with app.app_context():
            return jsonify({'status': 'ignored'})
if __name__ == "__main__":
    socketio.run(app)
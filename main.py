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
from viber_onboarding import request_user_info
from globals import *

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

# Constants
CHAT_API_ACCESS_TOKEN = os.environ['CHAT_API_ACCESS_TOKEN']
VIBER_API_URL = os.environ['VIBER_API_URL']
X_VIBER_AUTH_TOKEN = os.environ['X_VIBER_AUTH_TOKEN']
CHAT_API_URL = os.environ['CHAT_API_URL']

ACCEPTED_PLANS = ['cc-employees', 'enterprise', 'business', 'cc-pro', 'Glovo', 'dsk-enterprise', 'enterprise-plus', 'unicorn', 'startup']
MESSAGE_DELAY = 2
TIME_THRESHOLD = 5000
MAX_SEARCH_RESULTS = 3


def async_main():
    process_viber_request

def should_trigger_event(user_id, interval=30):
    while continue_checking.get(user_id, False):
        current_time = time.time()
        last_message_time = last_message_timestamps.get(user_id)

        if last_message_time and current_time - last_message_time >= interval:
            stop_viber_typing_status()
            #print("async sent request to stop typing")
            break  # Exit the loop once the condition is met

        time.sleep(1)  # Sleep for 1 second before checking again


def talk_to_ta(user_id, latest_conversation, owner_ta_status, owner_ta_name, owner_ta_id, message_text):
    
    if owner_ta_id is not None:
        if owner_ta_status == "online":
            send_viber_message(user_id, f"Свързвам ви с технически асистент {owner_ta_name}. \n\nМоля, изчакайте.")
            assignee_id = owner_ta_id
            assign_conversation(latest_conversation['id'], assignee_id, CHAT_API_ACCESS_TOKEN)

        else:
            first_name = owner_ta_name.split(' ')[0]
            send_viber_message(user_id, f"Свързах Ви в чат сесия с {owner_ta_name}. Тъй като не е на разположение в момента, моля, оставете своето съобщение тук. \n\n{first_name} ще се свърже с Вас, веднага щом бъде на линия. \n\nБлагодарим за търпението!")
            #print("TA Offline")
            assignee_id = owner_ta_id
            assign_conversation(latest_conversation['id'], assignee_id, CHAT_API_ACCESS_TOKEN)
            initiate_close_chat_viber_message(user_id, message_text=" ")

    else:
        print(f"Failed to find user with email {owner_ta_name}.")


def talk_to_am(user_id, latest_conversation, owner_id, owner_status, owner_name, message_text):
    if owner_id is not None:
        if owner_status == "online":
            send_viber_message(user_id, message_text=f"Разговорът е насочен към Вашия акаунт мениджър {owner_name}. \n\nМоля, изчакайте!")
            assignee_id = owner_id
            assign_conversation(latest_conversation['id'], assignee_id, CHAT_API_ACCESS_TOKEN)
        else:
            first_name = owner_name.split(' ')[0]
            send_viber_message(user_id, message_text=f"Свързах Ви в чат сесия с {owner_name}. Тъй като не е на разположение в момента, моля, оставете своето съобщение тук. \n\n{first_name} ще се свърже с Вас, веднага щом бъде на линия. \n\nБлагодарим за търпението!")
            #print("AM Offline")
            assignee_id = owner_id
            assign_conversation(latest_conversation['id'], assignee_id, CHAT_API_ACCESS_TOKEN)
            #print("AM Offline")
            initiate_close_chat_viber_message(user_id, message_text=" ")

    else:
        print(f"Failed to find user with email {owner_name}.")


def create_or_get_latest_conversation(contact_id, inbox_id, owner_id, api_access_token):
    latest_conversation = get_latest_conversation(contact_id, inbox_id, api_access_token)
    if latest_conversation is None:
        latest_conversation = create_conversation(contact_id, inbox_id, owner_id, api_access_token)
    return latest_conversation


def process_viber_request(request_data, app):
    with app.app_context():
        data = request_data
        event = data.get("event")
        if event == "webhook":
            return '', 200

        if event == "conversation_started":
            user_key = 'user'
            visitor_name = data[user_key]['name']
            welcome_message = send_welcome_message(visitor_name)
            return jsonify(welcome_message), 200
        elif event == "unsubscribed":
            user_id = data.get("user_id")
            user_data = request_contact_search(user_id, CHAT_API_ACCESS_TOKEN)
            if user_data['meta']['count'] == 0:
                return
            else:
                contact_id = user_data['payload'][0]['id']
                update_contact_bot_conversation(contact_id, CHAT_API_ACCESS_TOKEN, bot_conversation="Unsubscribed")
                return
            
        elif event == "message":
            user_key = 'sender'

            # Define Viber ID at user_id
            user_id = data[user_key]['id']

            # Throttle check
            current_time = time.time()

            if user_id in message_timestamps and current_time - message_timestamps[user_id] < 1:
                message_counters[user_id] += 1

                if message_counters[user_id] > 5:
                    return jsonify({'status': 'throttled'}), 429
            else:
                message_timestamps[user_id] = current_time
                message_counters[user_id] = 1
                

            if event == "message":
                message_type = data['message'].get('type', 'text')
                if message_type == 'text':
                    message_text = data['message']['text']
                    # Check if the message is equal to the previous one
                    with last_messages_lock:
                        if (user_id in last_messages and message_text == last_messages[user_id] and (user_id in last_messages and message_text != "Да, клиент съм" or user_id in last_messages and message_text != "Не, но искам да стана клиент" or user_id in last_messages and message_text != "Прекрати чат сесията")):
                            #print(last_messages)
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
        else:
            #print(3)
            return jsonify({'status': 'ignored'})


################################# RECEIVING AND PROCESSING THE VIBER MESSAGE #################################

        response_data = request_contact_search(user_id, CHAT_API_ACCESS_TOKEN)
        
        ################################# CHECK IF THERE IS SUCH USER AT CHATWOOT #################################
        if response_data['payload']:
            contact = response_data['payload'][0]
            pricing_plan = contact['custom_attributes'].get('pricingPlan')
            #owner_email = contact['custom_attributes']['owner_email']
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
                owner_id = None
                owner_ta_id = None
                owner_status = None
                owner_ta_status = None
                owner_name = None
                owner_ta_name = None
                owner_id, owner_name, owner_status, owner_ta_name, owner_ta_id, owner_ta_status = get_owner_by_email(owner_email)
                latest_conversation = create_or_get_latest_conversation(contact_id, inbox_id, owner_id, CHAT_API_ACCESS_TOKEN)
                toggle_conversation(latest_conversation, CHAT_API_ACCESS_TOKEN)
                #print(f"Owner ID: {owner_id}")
                #print("check completed!")
                for _ in range(1):  
                    #print("enter the loop")
                    if latest_conversation and (owner_id is not None or owner_ta_id is not None):
                        combined_text = formatHistory(user_id)
                        #print("check pricing plans")
                        ####### When user decide to talk with AM from the viber message ######
                        if (action_body == "Искам да се свържа с моя акаунт мениджър" and bot_conversation is None) or (action_body == "Искам да се свържа с моя акаунт мениджър" and bot_conversation == "No") or (action_body == "Искам да се свържа с моя акаунт мениджър" and bot_conversation == "Yes"):
                            # print(f"Case 1 {action_body} - Bot conv: {bot_conversation}")
                            if owner_id is not None:
                                #print("Case 1 has owner ID")
                                talk_to_am(user_id, latest_conversation, owner_id, owner_status, owner_name, message_text)
                                chat_message_send(message_text, latest_conversation, False, type="incoming")
                                
                                if combined_text is not None:
                                    chat_message_send(combined_text, latest_conversation, True, type="outgoing")
                                    wipe_user_chat_history(user_id)
                                        
                        # When user decide to talk with his personal Technical assistant
                        elif action_body == "Искам да говоря с технически асистент" and bot_conversation == "Yes":
                            #print(f"Case 2 {action_body} - Bot conv: {bot_conversation}")
                            talk_to_ta(user_id, latest_conversation, owner_ta_status, owner_ta_name, owner_ta_id, message_text)
                            toggle_conversation(latest_conversation, CHAT_API_ACCESS_TOKEN)
                            chat_message_send(message_text, latest_conversation, False, type="incoming")
                                # Add bot conversation as private note
                            if combined_text is not None:
                                    chat_message_send(combined_text, latest_conversation, True, type="outgoing")
                                    wipe_user_chat_history(user_id)
                        
                        ### If user without plan decide to start a new AI session ###
                        elif action_body == "Имам въпрос на различна тема" and bot_conversation == "Yes":
                            #print(f"Case 3 {action_body} - Bot conv: {bot_conversation}")
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
                            send_viber_message(user_id, gpt_response, sender_name="CloudCart AI assistant", sender_avatar="https://cdncloudcart.com/storage/cc_118509.png")
                        
                        ####### When user decide to talk with Technical assistant support team ######
                        elif action_body == "Имам въпрос свързан с работата на платформата" or action_body == "Имам още въпроси по темата" or bot_conversation == "Yes":
                            #print(f"Case 4 {action_body} - Bot conv: {bot_conversation}")
                            update_contact_bot_conversation(contact_id, CHAT_API_ACCESS_TOKEN, bot_conversation="Yes")
                            
                            if action_body == "Имам още въпроси по темата":
                                send_viber_message(user_id, message_text="Моля, продължете с въпросите по темата...", sender_name="CloudCart AI assistant", sender_avatar="https://cdncloudcart.com/storage/cc_118509.png")
                            elif action_body == "Имам въпрос свързан с работата на платформата":
                                send_viber_message(user_id, message_text="Моля, задайте вашия въпрос и ще се постарая да ви помогна с информацията, свързана с работата на платформата CloudCart.", sender_name="CloudCart AI assistant", sender_avatar="https://cdncloudcart.com/storage/cc_118509.png")
                            elif owner_ta_id is not None:
                                # send_pricing_plan_message(user_id, contact_name, pricing_plan, MESSAGE_DELAY)
                                send_viber_typing_status(user_id, sender_name="CloudCart AI assistant", sender_avatar="https://cdncloudcart.com/storage/cc_118509.png")
                                socketio.start_background_task(should_trigger_event, user_id)
                                from searchDB import answer_db
                                from searchBot import answer_bot
                                # search_result = None
                                # search_result = answer_db(message_text)
                                search_result = answer_bot(message_text, num_results=MAX_SEARCH_RESULTS)
                                #print(f"\n\nНамерен резултат: {search_result}\n\n")
                                gpt_response = generate_response_for_bad_pricing_plans(user_id, search_result, message_text, contact_name)


                                # Analyze the response
                                # analyzer_response = analyze_response(gpt_response)

                                # Process the analyzer's response
                                # conversation_ended = process_analyzer_response(analyzer_response, user_id)

                                # If the conversation has ended, call finalize_ai_conversation_viber_message
                                #if conversation_ended:
                                #    update_contact_bot_conversation(contact_id, CHAT_API_ACCESS_TOKEN,  bot_conversation="Maybe")
                                #else:
                                # send_viber_message(user_id, gpt_response, sender_name="CloudCart AI assistant", sender_avatar="https://cdncloudcart.com/storage/cc_118509.png")                   
                                finalize_ai_conversation_before_real_human_viber_message(user_id, gpt_response, sender_name="CloudCart AI assistant", sender_avatar="https://cdncloudcart.com/storage/cc_118509.png")

                        # Continues conversation with agent                
                        elif bot_conversation == "Human" and not action_body == "Прекрати чат сесията":
                            #print(f"Case 5 {action_body} - Bot conv: {bot_conversation}")
                            chat_message_send(message_text, latest_conversation, False, type="incoming")
                        
                        # User intent to close chat session
                        elif action_body == "Прекрати чат сесията" and bot_conversation == "Human":
                            print(f"Case 6 {action_body} - Bot conv: {bot_conversation}")
                            chat_message_send(message_text=f"The chat was closed by the customer: {contact_name}", latest_conversation=latest_conversation, private_msg=True, type="outgoing")
                            toggle_conversation(latest_conversation, CHAT_API_ACCESS_TOKEN)     
                        else:
                            send_personalized_viber_message(user_id, contact_name)
                            # update_contact_owner(contact_id, CHAT_API_ACCESS_TOKEN, owner_email, owner_name)
                            print(f"ELSE Case 7 {action_body} - Bot conv: {bot_conversation}")
            
            
            ###################################### ELSE PLAN IS NOT VALID ###########################################
            
            else:
                contact = response_data['payload'][0]
                contact_name = contact['name']
                pricing_plan = contact['custom_attributes'].get('pricingPlan')
                # print(f"Else case 1 {action_body} - Bot conv: {bot_conversation}")
                if "Искам да се свържа с моя акаунт мениджър" in message_text or "Искам да се свържа с техническия екип" in message_text:
                    message_text = "С кого разговарям?"
                if message_text == "Имам въпрос на различна тематика":
                    wipe_user_chat_history(user_id)

                #print(f"Step 1 - Message: {message_text} Plan: {pricing_plan}")
                #print(f"ACCEPTED_PLANS: {ACCEPTED_PLANS}, pricing_plan: {pricing_plan}")
                # Todo: Add external source for controlling the accepted plans
                if pricing_plan not in ACCEPTED_PLANS:
                    # send_pricing_plan_message(user_id, contact_name, pricing_plan, MESSAGE_DELAY)
                    # print(f"Step 2 - Plan: {pricing_plan}")
                    send_viber_typing_status(user_id, sender_name="CloudCart AI assistant", sender_avatar="https://cdncloudcart.com/storage/cc_118509.png")
                    socketio.start_background_task(should_trigger_event, user_id)
                    from searchBot import answer_db
                    from searchBot import answer_bot
                    search_result = answer_bot(message_text, num_results=MAX_SEARCH_RESULTS)
                    # print(f"\n\nНамерен резултат: {search_result}\n\n")
                    gpt_response = generate_response_for_bad_pricing_plans(user_id, search_result, message_text, contact_name)

                    # Analyze the response
                    analyzer_response = analyze_response(gpt_response)
                    # print(f"Step 3 - Analized: {analyzer_response}")
                    # Process the analyzer's response
                    conversation_ended = process_analyzer_response(analyzer_response, user_id)

                    # If the conversation has ended, call finalize_ai_conversation_viber_message
                    if conversation_ended:
                        # print(f"Step 4 - Conversation ended: {conversation_ended}")
                        finalize_ai_conversation_viber_message(user_id, gpt_response, sender_name="CloudCart AI assistant", sender_avatar="https://cdncloudcart.com/storage/cc_118509.png")
                    else:
                        # print(f"Step 5 - Send viber message")
                        send_viber_message(user_id, gpt_response, sender_name="CloudCart AI assistant", sender_avatar="https://cdncloudcart.com/storage/cc_118509.png")                
        
        
        ################################# ELSE THERE IS NO SUCH USER AT CHATWOOT #################################
        # If the user is not found in Chatwoot
        else:
            # Attempt to find the user's contact information
            response_data = request_contact_search(user_id, CHAT_API_ACCESS_TOKEN)
            # Define an email regex pattern for validation
            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            action_body = data['message']['text']
            #print(f"If the user is not found in Chatwoot: {action_body}")
            # Initialize contact and latest_conversation variables
            contact = None
            latest_conversation = None

            # Check if there are no contacts found in the response data
            if response_data['meta']['count'] == 0:
                if action_body == "Да, клиент съм":
                    # Ask the user to provide their email associated with their store's administrative panel
                    send_message_to_user(user_id, message_text="Здравейте, моля, изпратете ни Вашия имейл, който ползвате за вход в административния панел на магазина")
                elif action_body == "Не, но искам да стана клиент":
                    visitor_name = data[user_key]['name']
                    request_user_info(user_id, visitor_name)
                # If the message text matches the email regex
                elif re.fullmatch(email_regex, message_text):
                    # Search for the contact using their email
                    email_contact_search_data = email_contact_search(message_text, CHAT_API_ACCESS_TOKEN)

                    # If the contact is found
                    if email_contact_search_data['meta']['count'] > 0:
                        # Extract contact's information and pricing plan
                        contact = email_contact_search_data['payload'][0]
                        contact_id = contact['id']
                        contact_name = contact['name']
                        contact_email = contact['email']
                        pricing_plan = contact['custom_attributes'].get('pricingPlan')
                        
                        #Get data from Console CloudCart
                        cc_data = get_cloudcart_user_info(contact_email)
                        cc_data_get = cc_data.get('cc_user')
                        print(cc_data_get)
                        if cc_data_get is not None:
                            owner_email = cc_data['cc_user'].get('email')
                            owner_name = cc_data['cc_user'].get('name')
                        else:
                            owner_email = None
                            owner_name = None

                        # If the pricing plan is not in the accepted plans
                        if pricing_plan not in ACCEPTED_PLANS:
                            # Send a message to the user with a greeting and update the contact's Viber ID and bot conversation status
                            send_viber_message(user_id, message_text=f"Здравейте, {contact_name}, разговаряте с CloudCart AI асистент. С какво мога да ви съдействам?", sender_name="CloudCart AI assistant", sender_avatar="https://cdncloudcart.com/storage/cc_118509.png")
                            # print("Welcome user with selection, Plan: No Valid!")
                            update_contact_viber_id(contact_id, user_id, CHAT_API_ACCESS_TOKEN)
                            update_contact_bot_conversation(contact_id, CHAT_API_ACCESS_TOKEN,  bot_conversation="No")
                            #update_contact_owner(contact_id, CHAT_API_ACCESS_TOKEN, owner_email, owner_name)
                            

                        # If the pricing plan is valid
                        else:
                            # Send a personalized message to the user and update the contact's Viber ID and bot conversation status
                            send_personalized_viber_message(user_id, contact_name)
                            print("Welcome user with selection, Plan: VALID!")
                            # Update contact's Viber ID and bot conversation status
                            update_contact_viber_id(contact_id, user_id, CHAT_API_ACCESS_TOKEN)
                            update_contact_bot_conversation(contact_id, CHAT_API_ACCESS_TOKEN,  bot_conversation="No")
                            #update_contact_owner(contact_id, CHAT_API_ACCESS_TOKEN, owner_email, owner_name)

                    # If no contact is found
                    else:
                        # Send not found message to the user
                        send_email_not_found_message(user_id, message_text)
                # elif 
                # If the message text does not match the email regex
                else:
                    # Ask the user to provide their email associated with their store's administrative panel
                    message_text = "Здравейте, моля, изпратете ни Вашия имейл, който ползвате за вход в административния панел на магазина"
                    send_message_to_user(user_id, message_text)

        with app.app_context():
            return jsonify({'status': 'ignored'})
if __name__ == "__main__":
    socketio.run(app)
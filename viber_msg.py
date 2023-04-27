import requests
import os
from flask import jsonify, make_response

# Constants
CHAT_API_ACCESS_TOKEN = os.environ['CHAT_API_ACCESS_TOKEN']
VIBER_API_URL = os.environ['VIBER_API_URL']
X_VIBER_AUTH_TOKEN = os.environ['X_VIBER_AUTH_TOKEN']
CHAT_API_URL = os.environ['CHAT_API_URL']

def send_welcome_message(visitor_name):
    welcome_message = {
        "type": "text",
        "text": f"Здравейте, {visitor_name}, Вие ползвате ли услугите на CloudCart",
        "keyboard": {
            "Type": "keyboard",
            "DefaultHeight": False,
            "Buttons": [
                {
                    "ActionType": "reply",
                    "ActionBody": f"Да, клиент съм",
                    "Text": f"Да, клиент съм",
                    "TextSize": "regular",
                    "Columns": 3, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#d3b8ff" # Blue color
                },
                {
                    "ActionType": "reply",
                    "ActionBody": "Не, но искам да стана клиент",
                    "Text": "Не, но искам да стана клиент",
                    "TextSize": "regular",
                    "Columns": 3, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#ffd6b8" # Yellow color
                }
            ]
        }
    }
    
    return welcome_message

def get_headers(api_access_token=None, viber_auth_token=None):
    headers = {"Content-Type": "application/json"}
    
    if api_access_token:
        headers["api_access_token"] = api_access_token
        
    if viber_auth_token:
        headers["X-Viber-Auth-Token"] = viber_auth_token
        
    return headers

def send_viber_image_message(user_id, data_url, sender_name=None, sender_avatar=None, message_text=None):
    send_message_url = f"{VIBER_API_URL}/send_message"
    send_message_payload = {
        "receiver": user_id,
        "type": "picture",
        "min_api_version": 7,
        "media": data_url
    }

    if message_text:
        send_message_payload["text"] = message_text

    if sender_name:
        send_message_payload["sender"] = {
            "name": sender_name,
        }

        if sender_avatar:
            send_message_payload["sender"]["avatar"] = sender_avatar

    headers = get_headers(viber_auth_token=X_VIBER_AUTH_TOKEN)

    response = requests.post(send_message_url, json=send_message_payload, headers=headers)
    return response.status_code, response.text

def send_viber_typing_status(user_id, sender_name=None, sender_avatar=None):
    send_message_url = f"{VIBER_API_URL}/send_message"
    send_message_payload = {
        "receiver": user_id,
        "type": "text",
        "text": "```is typing...```",
        "min_api_version": 2,
        "sender_name": "CloudCart"
    }

    if sender_name:
        send_message_payload["sender"] = {
            "name": sender_name,
        }

        if sender_avatar:
                send_message_payload["sender"]["avatar"] = sender_avatar

    headers = get_headers(viber_auth_token=X_VIBER_AUTH_TOKEN)

    response = requests.post(send_message_url, json=send_message_payload, headers=headers)
    return response.status_code, response.text

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

def send_viber_message(user_id, message_text, sender_name=None, sender_avatar=None):
    send_message = f"{VIBER_API_URL}/send_message"
    send_message_payload = {
        "receiver": user_id,
        "type": "text",
        "min_api_version": 7,
        "text": message_text,
    }

    if sender_name:
        send_message_payload["sender"] = {
            "name": sender_name,
        }

        if sender_avatar:
            send_message_payload["sender"]["avatar"] = sender_avatar

    headers = get_headers(viber_auth_token=X_VIBER_AUTH_TOKEN)

    response = requests.post(send_message, json=send_message_payload, headers=headers)
    return response.status_code, response.text


def send_personalized_viber_message(user_id, contact_name):
    message_text = f"{contact_name}, моля, изберете една от следните опции, за да можем да Ви съдействаме:"
    send_message_payload = {
        "receiver": user_id,
        "min_api_version": 7,
        "type": "text",
        "text": message_text,
        "keyboard": {
            "Type": "keyboard",
            "DefaultHeight": False,
            "InputFieldState": "hidden",
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
                    "ActionBody": "Имам въпрос свързан с работата на платформата",
                    "Text": "Имам въпрос свързан с работата на платформата",
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

def initiate_new_viber_message(user_id):
    message_text = " "
    send_message_payload = {
        "receiver": user_id,
        "min_api_version": 7,
        "type": "text",
        "text": message_text,
        "keyboard": {
            "Type": "keyboard",
            "DefaultHeight": False,
            "InputFieldState": "hidden",
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
                    "ActionBody": "Имам въпрос свързан с работата на платформата",
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

def finalize_ai_conversation_viber_message(user_id, gpt_response, sender_name=None, sender_avatar=None):
    send_message_payload = {
        "receiver": user_id,
        "min_api_version": 7,
        "type": "text",
        "text": gpt_response,
        "keyboard": {
            "Type": "keyboard",
            "DefaultHeight": False,
            "InputFieldState": "hidden",
            "Buttons": [
                {
                    "ActionType": "reply",
                    "ActionBody": f"Имам още въпроси по темата",
                    "Text": f"Имам още въпроси по темата",
                    "TextSize": "regular",
                    "Columns": 4, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#b8c0ff"
                },
                {
                    "ActionType": "reply",
                    "ActionBody": "Имам въпрос на различна тематика",
                    "Text": "Имам въпрос на различна тематика",
                    "TextSize": "regular",
                    "Columns": 4, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#ffb8c3"
                }
            ]
        }
    }
    if sender_name:
        send_message_payload["sender"] = {
            "name": sender_name,
        }

        if sender_avatar:
            send_message_payload["sender"]["avatar"] = sender_avatar

    headers = get_headers(viber_auth_token=X_VIBER_AUTH_TOKEN)
    response = requests.post(VIBER_API_URL + "/send_message", json=send_message_payload, headers=headers)
    return response.status_code, response.text

def finalize_ai_conversation_before_real_human_viber_message(user_id, gpt_response, sender_name=None, sender_avatar=None):
    send_message_payload = {
        "receiver": user_id,
        "min_api_version": 7,
        "type": "text",
        "text": gpt_response,
        "keyboard": {
            "Type": "keyboard",
            "DefaultHeight": False,
            "InputFieldState": "hidden",
            "Buttons": [
                {
                    "ActionType": "reply",
                    "ActionBody": f"Искам да се свържа с моя акаунт мениджър",
                    "Text": f"Искам да се свържа с моя акаунт мениджър",
                    "TextSize": "regular",
                    "Columns": 3, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#ff99ff"
                },
                {
                    "ActionType": "reply",
                    "ActionBody": f"Имам още въпроси по тази тема",
                    "Text": f"Имам въпроси по тази тема",
                    "TextSize": "regular",
                    "Columns": 3, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#b8c0ff"
                },
                {
                    "ActionType": "reply",
                    "ActionBody": "Имам въпрос на различна тема",
                    "Text": "Имам въпрос на различна тема",
                    "TextSize": "regular",
                    "Columns": 3, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#ffb8c3"
                }
                ,
                {
                    "ActionType": "reply",
                    "ActionBody": "Искам да говоря с технически асистент",
                    "Text": "Искам да говоря с технически асистент",
                    "TextSize": "regular",
                    "Columns": 3, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#ff0022"
                }
            ]
        }
    }
    if sender_name:
        send_message_payload["sender"] = {
            "name": sender_name,
        }

        if sender_avatar:
            send_message_payload["sender"]["avatar"] = sender_avatar

    headers = get_headers(viber_auth_token=X_VIBER_AUTH_TOKEN)
    response = requests.post(VIBER_API_URL + "/send_message", json=send_message_payload, headers=headers)
    return response.status_code, response.text

def handle_ai_help_request(user_id):
    send_message_url = f"{VIBER_API_URL}/send_message"
    send_message_payload = {
        "receiver": user_id,
        "type": "text",
        "min_api_version": 7,
        "text": "Докато очаквате отговор, можете да използвате изкуствения интелект на CloudCart",
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
                    "ActionBody": "Имам въпрос свързан с работата на платформата",
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

    response = requests.post(send_message_url, json=send_message_payload, headers=headers)
    return response.status_code, response.text
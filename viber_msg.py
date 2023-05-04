import requests
import os
import time
from flask import jsonify, make_response



# Constants
CHAT_API_ACCESS_TOKEN = os.environ['CHAT_API_ACCESS_TOKEN']
VIBER_API_URL = os.environ['VIBER_API_URL']
X_VIBER_AUTH_TOKEN = os.environ['X_VIBER_AUTH_TOKEN']
CHAT_API_URL = os.environ['CHAT_API_URL']

last_message_timestamps = {}

def update_last_message_timestamp(user_id):
    global last_message_timestamps
    last_message_timestamps[user_id] = time.time()

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
                    "BgColor": "#eee3ff" # Blue color
                },
               # {
               #     "ActionType": "reply",
               #     "ActionBody": "Не, но искам да стана клиент",
               #     "Text": "Не, но искам да стана клиент",
               #     "TextSize": "regular",
               #     "Columns": 3, # Change this value as needed
               #     "Rows": 1,
               #     "BgColor": "#ffefe3" # Yellow color
               # }
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
    update_last_message_timestamp(user_id)
    send_message_url = f"{VIBER_API_URL}/send_message"
    send_message_payload = {
        "receiver": user_id,
        "type": "text",
        "text": "```is typing...```",
        "min_api_version": 7,
        "keyboard": {
            "Type": "keyboard",
            "DefaultHeight": False,
            "InputFieldState": "hidden",
            "Buttons": [
                {
                    "Columns": 6,
                    "Rows": 1,
                    "BgColor": "#eee3ff",
                    "BgMediaType": "gif",
                    "BgMedia": "https://cdn.dribbble.com/users/1152773/screenshots/3832732/loader2.gif",
                    "BgLoop": True,
                    "ActionType": "none",
                    "ActionBody": "...",
                    "Text": "...",
                    "TextOpacity": 0,
                    "TextSize": "regular"
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
    response = requests.post(send_message_url, json=send_message_payload, headers=headers)
    return response.status_code, response.text

def stop_viber_typing_status(user_id, sender_name=None, sender_avatar=None):
    send_message_url = f"{VIBER_API_URL}/send_message"
    send_message_payload = {
        "receiver": user_id,
        "type": "text",
        "text": "Възникна грешка в системата, моля, повторете въпроса си",
        "min_api_version": 7
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
                    "BgColor": "#eee3ff" # Blue color
                },
                {
                    "ActionType": "reply",
                    "ActionBody": "Имам въпрос свързан с работата на платформата",
                    "Text": "Имам въпрос свързан с работата на платформата",
                    "TextSize": "regular",
                    "Columns": 3, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#ffefe3" # Yellow color
                }
            ]
        }
    }

    headers = get_headers(viber_auth_token=X_VIBER_AUTH_TOKEN)
    response = requests.post(VIBER_API_URL + "/send_message", json=send_message_payload, headers=headers)
    return response.status_code, response.text

def initiate_new_viber_message(user_id, message_text):
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
                    "BgColor": "#eee3ff" # Blue color
                },
                {
                    "ActionType": "reply",
                    "ActionBody": "Имам въпрос свързан с работата на платформата",
                    "Text": "Искам да се свържа с техническия екип",
                    "TextSize": "regular",
                    "Columns": 3, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#ffefe3" # Yellow color
                }
            ]
        }
    }

    headers = get_headers(viber_auth_token=X_VIBER_AUTH_TOKEN)
    response = requests.post(VIBER_API_URL + "/send_message", json=send_message_payload, headers=headers)
    return response.status_code, response.text

def initiate_close_chat_viber_message(user_id, message_text):
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
                    "ActionBody": f"Прекрати чат сесията",
                    "Text": f"Прекрати чат сесията",
                    "Columns": 6, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#eee3ff",
                    "TextVAlign": "middle",
                    "TextHAlign": "center",
                    "TextOpacity": 60,
                    "TextSize": "small" # Blue color
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
            "Buttons": [
                {
                    "ActionType": "reply",
                    "ActionBody": "Имам въпрос на различна тематика",
                    "Text": "Имам въпрос на различна тематика",
                    "TextSize": "regular",
                    "Columns": 6, # Change this value as needed
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
            "Buttons": [
                {
                    "ActionType": "reply",
                    "ActionBody": "Имам още въпроси по темата",
                    "Text": "Имам още въпроси по темата",
                    "TextSize": "regular",
                    "Columns": 6, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#ceffb8"
                },
                {
                    "ActionType": "reply",
                    "ActionBody": "Имам въпрос на различна тема",
                    "Text": "Имам въпрос на различна тема",
                    "TextSize": "regular",
                    "Columns": 6, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#ffb8c3"
                },
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
                    "ActionBody": "Искам да говоря с технически асистент",
                    "Text": "Искам да говоря с технически асистент",
                    "TextSize": "regular",
                    "Columns": 3, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#ffe0e4"
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
                    "BgColor": "#eee3ff" # Blue color
                },
                {
                    "ActionType": "reply",
                    "ActionBody": "Имам въпрос свързан с работата на платформата",
                    "Text": "Искам да се свържа с техническия екип",
                    "TextSize": "regular",
                    "Columns": 3, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#ffefe3" # Yellow color
                }
            ]
        }
    }
    headers = get_headers(viber_auth_token=X_VIBER_AUTH_TOKEN)

    response = requests.post(send_message_url, json=send_message_payload, headers=headers)
    return response.status_code, response.text


def send_pricing_plan_message(user_id, contact_name, pricing_plan, delay=None):
    message_text = f"{contact_name}, за съжаление Вашият абонаментен план *{pricing_plan}* не включва чат поддръжка. \n\nТук можете да се запознаете с цените на нашите абонаментни планове:"
    status_code, response_text = send_viber_message(user_id, message_text)

    time.sleep(2)

    message_url = "https://cloudcart.com/bg/pricing?utm_source=viberBot"
    status_code, response_text = send_viber_url_message(user_id, message_url)


def send_email_not_found_message(user_id, email):
    message_text = f"Не е открит потребител с този имейл: {email}. Моля, опитайте отново."
    status_code, response_text = send_viber_message(user_id, message_text)


def send_message_to_user(user_id, message_text):
    status_code, response_text = send_viber_message(user_id, message_text)

################################# VIBER ONBOARDING #################################

def vo_get_user_details(user_id, message_text):
    send_message_url = f"{VIBER_API_URL}/send_message"
    send_message_payload = {
        "receiver": user_id,
        "type": "text",
        "text": message_text,
        "min_api_version": 7
        }
    
    headers = get_headers(viber_auth_token=X_VIBER_AUTH_TOKEN)
    response = requests.post(send_message_url, json=send_message_payload, headers=headers)
    return response.status_code, response.text

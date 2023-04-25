import requests
import os
from chatHelpers import get_headers


# Constants
CHAT_API_ACCESS_TOKEN = os.environ['CHAT_API_ACCESS_TOKEN']
VIBER_API_URL = os.environ['VIBER_API_URL']
X_VIBER_AUTH_TOKEN = os.environ['X_VIBER_AUTH_TOKEN']
CHAT_API_URL = os.environ['CHAT_API_URL']

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

def finalize_ai_conversation_viber_message(user_id, gpt_response, sender_name=None, sender_avatar=None):
    message_text = " "
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
                    "ActionBody": f"имам още въпроси по темата",
                    "Text": f"Имам въпроси по същата тема",
                    "TextSize": "regular",
                    "Columns": 3, # Change this value as needed
                    "Rows": 1,
                    "BgColor": "#b8c0ff"
                },
                {
                    "ActionType": "reply",
                    "ActionBody": "имам въпрос на различна тема",
                    "Text": "Имам въпрос на различна тема",
                    "TextSize": "regular",
                    "Columns": 3, # Change this value as needed
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

def handle_viber_message_response(user_id, action_body):
    if action_body == "Искам да се свържа с моя акаунт мениджър":
        return "owner"
    elif action_body == "Искам да се свържа с техническия екип":
        return "technical_assistant"
    else:
        return None

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

    response = requests.post(send_message_url, json=send_message_payload, headers=headers)
    return response.status_code, response.text
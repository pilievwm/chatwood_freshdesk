import requests
import os
from chatHelpers import get_headers


# Constants
CHAT_API_ACCESS_TOKEN = os.environ['CHAT_API_ACCESS_TOKEN']
VIBER_API_URL = os.environ['VIBER_API_URL']
X_VIBER_AUTH_TOKEN = os.environ['X_VIBER_AUTH_TOKEN']
CHAT_API_URL = os.environ['CHAT_API_URL']

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
    send_message_url = f"{VIBER_API_URL}/send_message"
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

    response = requests.post(send_message_url, json=send_message_payload, headers=headers)
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
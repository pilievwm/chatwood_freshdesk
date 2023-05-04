import requests
import os
import time
from flask import jsonify, make_response
from viber_msg import vo_get_user_details
from globals import *


# Constants
CHAT_API_ACCESS_TOKEN = os.environ['CHAT_API_ACCESS_TOKEN']
VIBER_API_URL = os.environ['VIBER_API_URL']
X_VIBER_AUTH_TOKEN = os.environ['X_VIBER_AUTH_TOKEN']
CHAT_API_URL = os.environ['CHAT_API_URL']

def request_user_info(user_id, visitor_name):
    
    # Get user email
    message_text = f"{visitor_name}, моля, въведете Вашия имейл"
    vo_get_user_details(user_id, message_text)

    if user_id not in onboarding_data:
        onboarding_data[user_id] = {'name': visitor_name}
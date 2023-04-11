import os
import csv
import requests
from io import StringIO
from dotenv import load_dotenv
from flask import jsonify

load_dotenv()

CHAT_API_ACCESS_TOKEN = os.getenv("CHAT_API_ACCESS_TOKEN")
CHAT_API_URL = os.getenv("CHAT_API_URL")

def get_team_structure():
    url = "https://cdncloudcart.com/storage/do_not_delete_sales_support_team.csv"
    response = requests.get(url)
    data = response.content.decode("utf-8")
    team_structure = {}

    csv_reader = csv.reader(StringIO(data))
    for row in csv_reader:
        am, jam, ta = [email.strip() for email in row]  # Strip extra spaces
        team_structure[am] = {'jam': jam, 'ta': ta}
        team_structure[jam] = {'am': am, 'ta': ta}
        team_structure[ta] = {'am': am, 'jam': jam}

    return team_structure

def get_availability(email, chat_api_access_token, chat_api_url):
    headers = {'api_access_token': CHAT_API_ACCESS_TOKEN}

    agents_url = f'{chat_api_url}/agents'
    response = requests.get(agents_url, headers=headers)

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}", None, None

    agents = response.json()

    for agent in agents:
        if agent['email'] == email:
            return (
                agent.get('availability_status'),
                agent.get('available_name', 'N/A'),
                agent.get('id'),
            )

    return None, None, None


def handle_team_availability(request, team_structure):
    email = request.args.get('email')
    route = request.args.get('route')

    if email in team_structure:
        if route and route in team_structure[email]:
            target_email = team_structure[email][route]
            availability, available_name, agent_id = get_availability(target_email, CHAT_API_ACCESS_TOKEN, CHAT_API_URL)
            return jsonify({
                route: target_email,
                "status": availability,
                "name": available_name,
                "id": agent_id,
            })
        else:
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
            return jsonify(response)
    else:
        return jsonify({'error': 'Email not found'}), 404


from flask import Flask, request, jsonify
import os
import json
from ct import handle_create_ticket
from conv import handle_ticket_info
from login_user import handle_login_user
from chatHelpers import get_team_structure, handle_team_availability
from main import process_viber_request
from chatwoot import process_chatwoot_payload
import threading
import socket


app = Flask(__name__)

team_structure = get_team_structure()

@app.route('/team', methods=['GET'])
def team():
    return handle_team_availability(request, team_structure)


@app.route('/ct', methods=['POST'])
def create_ticket():
    return handle_create_ticket(request)

@app.route('/conv', methods=['POST'])
def conv():
    return handle_ticket_info(request)

@app.route('/login_user', methods=['POST'])
def login_user():
    return handle_login_user(request)

@app.route('/ping', methods=['POST'])
def ping():
    return "the service is alive"

@app.route('/viber', methods=['POST'])
def viber():
    # Get a copy of the request's JSON data
    request_data = request.get_json()

    # Check if the event is "conversation_started"
    if request_data.get("event") == "conversation_started":
        result = process_viber_request(request_data, app)
        if isinstance(result, tuple):
            response, status_code = result
            return response, status_code
    else:
        # Create a new thread for process_viber_request and start it
        thread = threading.Thread(target=process_viber_request, args=(request_data, app))
        thread.start()

    # Return a 200 OK response immediately
    return jsonify({"status": "success", "message": "Viber message received successfully."}), 200


@app.route('/chatwoot', methods=['POST'])
def chatwoot():
    # Get the JSON payload from the request
    payload = request.json

    # Process the payload using the process_chatwoot_payload function from chatwoot.py
    response = process_chatwoot_payload(payload)

    return response


def generate_filename(base_name, ext):
    count = 1
    file_name = f"{base_name}.{ext}"
    while os.path.exists(file_name):
        file_name = f"{base_name}-{count}.{ext}"
        count += 1
    return file_name

@app.route('/orders', methods=['POST'])
def orders():
    # Get the JSON payload from the request
    payload = request.json

    # Check if the log folder exists, if not, create it
    if not os.path.exists('log'):
        os.makedirs('log')

    # Get the order ID from the first element of the JSON payload list
    order_id = payload[0].get('id')

    # Create the base file name
    base_file_name = os.path.join('log', str(order_id))

    # Generate the unique file name
    file_name = generate_filename(base_file_name, 'json')

    # Save the JSON payload to the file
    with open(file_name, 'w') as f:
        json.dump(payload, f)

    # Return a successful response
    return jsonify({"status": "success", "message": f"Order {order_id} logged successfully."}), 200


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))  # connect to a public IP address
    ip_address = s.getsockname()[0]
    s.close()
    return ip_address

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    data_dir='cert'
    host = get_ip_address()
    app.run(debug=True, host=host, port=port, ssl_context=(os.path.join(data_dir, 'fullchain.pem'), os.path.join(data_dir, 'privkey.pem')))


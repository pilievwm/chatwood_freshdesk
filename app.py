from flask import Flask, request, jsonify
import os
import json
from ct import handle_create_ticket
from conv import handle_ticket_info
from login_user import handle_login_user
from chatHelpers import get_team_structure, handle_team_availability
from main import process_viber_request, send_viber_message


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
    return process_viber_request(request)

@app.route('/chatwoot', methods=['POST'])
def chatwoot():
    # Get the JSON payload from the request
    payload = request.json
    messages = payload.get('conversation', {}).get('messages', [])
    if not messages:

        return jsonify({"status": "success"})
    message = messages[0]
    # Check if the message is outgoing and private and has an open status
    if (message.get('message_type') != 0 and
        not message.get('private') and
        'cw-origin' not in message.get('external_source_ids', {}).get('slack', '')):

        # Extract the required variables from the response
        viberid = payload['conversation']['meta']['sender']['custom_attributes']['viberid']
        conversation_id = payload['conversation']['id']
        message_text = message['content']
        sender = message.get('sender', {})
        sender_name = sender.get('available_name') or sender.get('name')
        sender_avatar = sender.get('avatar_url')

        # Call the send_viber_message function from viber.py to send the message
        send_viber_message(user_id=viberid, message_text=message_text, sender_name=sender_name, sender_avatar=sender_avatar)

    return jsonify({"status": "success"})


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



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port, ssl_context=('fullchain.pem', 'privkey.pem'))

import requests
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()


app = Flask(__name__)

CHAT_API_ACCESS_TOKEN = os.getenv("CHAT_API_ACCESS_TOKEN")
CHAT_API_URL = os.getenv("CHAT_API_URL")
FRESHDESK_API_KEY = os.getenv("FRESHDESK_API_KEY")
FRESHDESK_API_URL = os.getenv("FRESHDESK_API_URL")


def send_private_note(conversation_id, content):
    data = {
        "content": content,
        "message_type": "outgoing",
        "private": True
    }

    response = requests.post(
        CHAT_API_URL.format(conversation_id),
        json=data,
        headers={'api_access_token': CHAT_API_ACCESS_TOKEN}
    )


@app.route('/webhook', methods=['POST'])
def handle_webhook():
    webhook_data = request.get_json()

    # Extract the ID from the webhook data
    conversation_id = webhook_data['id']

    # Make a GET request to the specified endpoint
    response = requests.get(CHAT_API_URL.format(conversation_id),
                            headers={'api_access_token': CHAT_API_ACCESS_TOKEN})

    # Extract the messages and metadata from the response
    payload = response.json()
    messages = payload['payload']
    metadata = payload['meta']

    conversation = []

    for message in messages:
        if 'sender' in message and not message['private']:
            sender = message['sender']
            if sender['type'] == 'contact':
                # Customer message
                content = message['content']
                conversation.append({"type": "customer", "content": content})
            elif sender['type'] == 'user':
                # Support agent message
                content = message['content']
                conversation.append({"type": "support_agent", "content": content})

    # Create the HTML conversation
    html_conversation = ""
    for msg in conversation:
        if msg['type'] == 'customer':
            html_conversation += f"<strong>{metadata['contact']['name']}:</strong> {msg['content']}<br><br>"
        elif msg['type'] == 'support_agent':
            html_conversation += f"<strong>{metadata['assignee']['name']}:</strong> {msg['content']}<br><br>"

    # Extract customer name and email from metadata
    customer_name = metadata['contact']['name']
    customer_email = metadata['contact']['email']

    # Check if the customer email is empty
    if not customer_email:
        message = "Requester email is empty. Skipping ticket creation."
        send_private_note(conversation_id, message)
        return jsonify({"status": "failed", "reason": "empty_email"})

    # Create the Freshdesk ticket
    ticket_data = {
        "email": customer_email,
        "subject": f"Chat conversation with {customer_name}",
        "description": html_conversation,
        "status": 2,  # Open
        "priority": 1,  # Low
        "group_id": 77000011310,
        "type": "General question"
    }

    # Make a POST request to the Freshdesk API
    freshdesk_response = requests.post(
        FRESHDESK_API_URL,
        json=ticket_data,
        auth=(FRESHDESK_API_KEY, "X")
    )

    if freshdesk_response.status_code == 201:
        message = "Ticket created successfully!"
        send_private_note(conversation_id, message)

        # Get the created ticket ID
        created_ticket_id = freshdesk_response.json()["id"]

        # Add a private note to the created ticket with the conversation URL
        note_data = {
            "body": f"Chat conversation URL: https://chat.cloudcart.com/app/accounts/1/conversations/{conversation_id}",
            "private": True
        }

        # Make a POST request to the Freshdesk Conversations API
        freshdesk_note_response = requests.post(
            f"{FRESHDESK_API_URL}/{created_ticket_id}/notes",
            json=note_data,
            auth=(FRESHDESK_API_KEY, "X")
        )

        if freshdesk_note_response.status_code == 201:
            print("Private note added successfully!")
        else:
            print("Failed to add private note. Status code:", freshdesk_note_response.status_code)
            print("Error response:", freshdesk_note_response.text)

    else:
        message = f"Failed to create ticket. Status code: {freshdesk_response.status_code}, {freshdesk_response.text}"
        send_private_note(conversation_id, message)

    return jsonify({"status": "success"})



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

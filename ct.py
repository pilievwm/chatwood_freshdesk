"""
Create a ticket
This script receives a webhook data from a chat application, 
extracts the conversation between a support agent and a customer, and 
creates a ticket in Freshdesk with the conversation as a description.
""" 

import requests
import os
from dotenv import load_dotenv
from flask import jsonify

load_dotenv()

CHAT_API_ACCESS_TOKEN = os.getenv("CHAT_API_ACCESS_TOKEN")
CHAT_API_URL = os.getenv("CHAT_API_URL")
FRESHDESK_API_KEY = os.getenv("FRESHDESK_API_KEY")
FRESHDESK_API_URL = os.getenv("FRESHDESK_API_URL")


def send_private_note(conversation_id, content):
    """
    Sends a private note to the chat application.
    """
    data = {
        "content": content,
        "message_type": "outgoing",
        "private": True
    }

    response = requests.get(f"{CHAT_API_URL}/conversations/{conversation_id}/messages",
        headers={'api_access_token': CHAT_API_ACCESS_TOKEN})


def handle_create_ticket(request):
    """
    Receives a webhook data, extracts the conversation messages and metadata,
    creates an HTML conversation, extracts the customer name and email,
    creates a Freshdesk ticket with the conversation as a description,
    and adds a private note to the ticket with the conversation URL.
    Returns a JSON response with a success or failed status.
    """
    webhook_data = request.json

    # Extract the ID from the webhook data
    conversation_id = webhook_data['id']

    # Make a GET request to the specified endpoint
    response = requests.get(f"{CHAT_API_URL}/conversations/{conversation_id}/messages",
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
        f"{FRESHDESK_API_URL}/tickets",
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
            f"{FRESHDESK_API_URL}/tickets/{created_ticket_id}/notes",
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
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from flask import jsonify, request

load_dotenv()

FRESHDESK_API_KEY = os.getenv("FRESHDESK_API_KEY")
FRESHDESK_API_URL = os.getenv("FRESHDESK_API_URL")
CHAT_API_ACCESS_TOKEN = os.getenv("CHAT_API_ACCESS_TOKEN")
CHAT_API_URL = os.getenv("CHAT_API_URL")

def get_ticket_status_name(status_code):
    status_names = {
        2: "Open",
        3: "Pending",
        4: "Resolved",
        5: "Closed"
    }
    return status_names.get(status_code, "Unknown")

def send_private_note(conversation_id, content):
    data = {
        "content": content,
        "message_type": "outgoing",
        "private": True,
        "content_type": "text"  # Change this line to "markdown"
    }

    response = requests.post(
        CHAT_API_URL.format(conversation_id),
        json=data,
        headers={'api_access_token': CHAT_API_ACCESS_TOKEN}
    )


def get_tickets_by_email(email):
    tickets_url = f"{FRESHDESK_API_URL}/tickets?email={email}"
    response = requests.get(tickets_url, auth=(FRESHDESK_API_KEY, "X"))
    return response

def handle_ticket_info(request):
    webhook_data = request.get_json()
    
    # Extract the email and conversation ID from the webhook data
    email = webhook_data['meta']['sender']['email']
    conversation_id = webhook_data['id']

    # Make a GET request to the Freshdesk API to search for tickets by email
    freshdesk_response = get_tickets_by_email(email)

    # Check the response status code
    if freshdesk_response.status_code == 200:
        tickets = freshdesk_response.json()

        open_and_pending_tickets = []
        for ticket in tickets:
            if ticket['status'] in [2, 3]:
                open_and_pending_tickets.append(ticket)

        if open_and_pending_tickets:
            # Create a single note containing all open and pending tickets
            message = "Open and Pending Tickets:\n\n"
            for ticket in open_and_pending_tickets:
                ticket_id = ticket['id']
                subject = ticket['subject']
                status = get_ticket_status_name(ticket['status'])  # Get the status name
                created_at = datetime.strptime(ticket['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                formatted_created_at = created_at.strftime('%d %b %Y, %H:%M')
                ticket_url = f"https://help.cloudcart.com/a/tickets/{ticket_id}"

                message += f"- **{ticket_id}** | Subject: **{subject}** | Status: **{status}** | Date: **{formatted_created_at}** | " \
                        f"[View ticket]({ticket_url})\n\n"


            # Send the note with the message
            send_private_note(conversation_id, message)
        else:
            send_private_note(conversation_id, "No open or pending tickets found.")
    else:
        print("Failed to get ticket info. Status code:", freshdesk_response.status_code)
        print("Error response:", freshdesk_response.text)
    
    return jsonify({"message": "Success"}), 200
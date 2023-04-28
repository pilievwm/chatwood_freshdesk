from viber_msg import *
from flask import jsonify
from main import update_contact_bot_conversation, create_or_get_latest_conversation
from chatHelpers import chat_message_send

def process_chatwoot_payload(payload):
    event = payload.get('event')
    
    conversation_status = payload.get("status")
    user_id = payload.get('meta', {}).get('sender', {}).get('custom_attributes', {}).get('viberid')
    contact_id = payload.get('meta', {}).get('sender', {}).get('id', {})
    # Get the JSON payload from the request

    
    if event == "conversation_status_changed":
        if conversation_status != "open":
            initiate_new_viber_message(user_id, message_text=f"_info: Чат сесията е затворена. Благодарим ви!_")
            # Update customer attribute Bot conversation to Human
            update_contact_bot_conversation(contact_id, CHAT_API_ACCESS_TOKEN,  bot_conversation="No")
        else:
            conversation_status == "open"
            update_contact_bot_conversation(contact_id, CHAT_API_ACCESS_TOKEN,  bot_conversation="Human")

    elif event == "conversation_updated":
        changed_attributes = payload.get('changed_attributes', [])
        for attr in changed_attributes:
            if 'assignee_id' in attr:
                previous_value = attr['assignee_id']['previous_value']
                current_value = attr['assignee_id']['current_value']

                if previous_value != current_value:
                    assignee = payload.get('meta', {}).get('assignee')
                    if assignee:
                        new_assignee = assignee.get('name')
                        send_viber_message(user_id, f"_info: Вашият чат беше пренасочен към {new_assignee}_")

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
        message_text = message['content']
        sender = message.get('sender', {})
        sender_name = sender.get('available_name') or sender.get('name')
        sender_avatar = sender.get('avatar_url')

        # Check if the message has attachments
        if 'attachments' in message:
            handle_chatwoot_image_message(payload)
        else:
            handle_chatwoot_message(viberid, message_text, sender_name, sender_avatar)

    return jsonify({"status": "success"})


def handle_chatwoot_message(viberid, message_text, sender_name, sender_avatar):
    # Send the message to the Viber user using the send_viber_message function
    send_viber_message(user_id=viberid, message_text=message_text, sender_name=sender_name, sender_avatar=sender_avatar)

def handle_chatwoot_image_message(payload):
    messages = payload.get('conversation', {}).get('messages', [])
    if not messages:
        return

    message = messages[0]

    if 'attachments' in message:
        attachments = message['attachments']
        for attachment in attachments:
            if attachment['file_type'] == 'image':
                data_url = attachment['data_url']

                viberid = payload['conversation']['meta']['sender']['custom_attributes']['viberid']
                conversation_id = payload['conversation']['id']
                sender = message.get('sender', {})
                sender_name = sender.get('available_name') or sender.get('name')
                sender_avatar = sender.get('avatar_url')
                message_text = message['content']
                
                print("Data URL: ", data_url)
                # Call the function to send the image message in Viber
                send_viber_image_message(viberid, data_url, sender_name, sender_avatar, message_text=message_text)


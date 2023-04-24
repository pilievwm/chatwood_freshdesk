from viber_msg import *
from flask import jsonify

def process_chatwoot_payload(payload):
    event = payload.get('event')
    conversation_status = payload.get("status")
    user_id = payload.get('meta', {}).get('sender', {}).get('custom_attributes', {}).get('viberid')

    if event == "conversation_status_changed":
        if conversation_status != "open":
            initiate_new_viber_message(user_id)

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

        # Check if the message has attachments
        if 'attachments' in message:
            handle_chatwoot_image_message(payload)
        else:
            handle_chatwoot_message(viberid, conversation_id, message_text, sender_name, sender_avatar)

    return jsonify({"status": "success"})


def handle_chatwoot_message(viberid, conversation_id, message_text, sender_name, sender_avatar):
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


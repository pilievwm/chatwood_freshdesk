from viber_msg import send_viber_message

def handle_chatwoot_message(viberid, conversation_id, message_text, sender_name, sender_avatar):
    # Send the message to the Viber user using the send_viber_message function
    send_viber_message(user_id=viberid, message_text=message_text, sender_name=sender_name, sender_avatar=sender_avatar)

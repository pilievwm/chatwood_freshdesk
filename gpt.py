import openai
import os
import requests
from viber_msg import *


openai.api_key = os.environ['OPEN_AI']

user_chat_histories = {}
max_conversations = 10  # Add this variable to control the number of conversations

def generate_response_for_bad_pricing_plans(user_id, search_result, message_text, contact_name):
    global user_chat_histories

    # Update the user's chat history with the new message
    if user_id not in user_chat_histories:
        user_chat_histories[user_id] = []
    user_chat_histories[user_id].append({"role": "user", "content": message_text})

    # Limit the number of conversations stored
    if len(user_chat_histories[user_id]) > max_conversations * 2:
        user_chat_histories[user_id] = user_chat_histories[user_id][-max_conversations * 2:]

    conversation_history = [
        {"role": "system", "content": f"Act as CloudCart support agent. Respond in Bulgarian! \n Let\'s think step by step trought the provided question and find the best possible solution for {contact_name} problem or question. Use empaty. \nIf the context is empty, say \"No answer\". If there is a link you must to skip it! \n\nName: {contact_name} translate in Bulgarian and use the first name\n\nContext: {search_result}"}
    ]

    # Add the chat history to the conversation_history
    conversation_history.extend(user_chat_histories[user_id])

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=conversation_history
    )

    gpt = response.choices[0].message['content']

    # Update the user's chat history with the assistant's response
    user_chat_histories[user_id].append({"role": "assistant", "content": gpt})

    # Print the conversation history in the desired format
    conversation_history_list(user_id)

    return gpt


def conversation_history_list(user_id):
    conversation = user_chat_histories[user_id]

    for message in conversation:
        role = message["role"]
        content = message["content"].replace("\n", " ").strip()
        if role == "user":
            print(f"user: {content}")
        elif role == "assistant":
            print(f"assistant: {content}")

def analyze_response(gpt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Analyze if this is the end of the conversation. Answer with \"yes\" or \"no\""},
            {"role": "user", "content": gpt}
        ]
    )

    analyzer = response['choices'][0]['message']['content']
    return analyzer


def process_analyzer_response(analyzer_response, user_id):
    if "yes" in analyzer_response.lower():
        return True
    elif "no" in analyzer_response.lower():
        return False
    else:
        print("The response does not contain 'Yes' or 'No'")
        return False
    
def wipe_user_chat_history(user_id):
    if user_id in user_chat_histories:
        del user_chat_histories[user_id]
        print(f"Chat history deleted for user_id: {user_id}")
    else:
        print(f"No chat history found for user_id: {user_id}")
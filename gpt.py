import openai
import os
import requests
from viber_msg import *
import time
from openai.error import RateLimitError

openai.api_key = os.environ['OPEN_AI']

user_chat_histories = {}

max_conversations = 10  # Add this variable to control the number of conversations

def call_openai_with_retry(conversation_history, user_id):
    retries = 5
    backoff_factor = 2
    for i in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=conversation_history,
                temperature=0

            )
            return response
        except RateLimitError as e:
            if i == retries - 1:  # If it's the last retry attempt, raise the exception
                raise e
            else:
                sleep_duration = backoff_factor ** i
                print(f"RateLimitError encountered. Retrying in {sleep_duration} seconds...")
                time.sleep(sleep_duration)
        except openai.error.InvalidRequestError as e:
            send_viber_message(user_id, f"Моля, променете въпроса си, за да можем да ви отговорим")
            raise e


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
        {"role": "system", "content": f"Информация за твоя отговор: \nинформация: '{search_result}' \nАко липсва информация за твоя отговор, задължително отговори с \"За съжаление не мога да ви съдействам с този въпрос\". \n\nТи си AI и си пълноправен член на екипа на CloudCart в Viber чат сесия с {contact_name}."} 
        # {"role": "system", "content": f"Информация за твоя отговор: \nинформация: '{search_result}' \nАко вграденият текст е празен, задължително отговори с \"За съжаление не мога да ви съдействам с този въпрос\". \n\nТи си AI и си пълноправен член на екипа на CloudCart в Viber чат сесия с {contact_name}. Нямаш право да предоставяш линк!  Отговорът ти Не трябва да надвишава 300 думи! Не предлагай на клиента да се свърже с техническия екип на CloudCart, защото ти самия си част от екипа и клиента вече се е свързал с теб!"}
    ]

    # Add the chat history to the conversation_history
    conversation_history.extend(user_chat_histories[user_id])

    response = call_openai_with_retry(conversation_history, user_id)

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
        #print("The response does not contain 'Yes' or 'No'")
        return False
    
def wipe_user_chat_history(user_id):
    if user_id in user_chat_histories:
        del user_chat_histories[user_id]
        #print(f"Chat history deleted for user_id: {user_id}")
    #else:
        #print(f"No chat history found for user_id: {user_id}")


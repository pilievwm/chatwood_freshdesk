from threading import Lock

# Global variable to store the last message for each user
last_messages_lock = Lock()
last_messages = {}
continue_checking = {}
message_timestamps = {}
message_counters = {}
onboarding_data = {}
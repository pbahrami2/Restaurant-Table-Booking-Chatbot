import re
from uuid import uuid4

class IdentityManager:
    # Initializes the IdentityManager with an empty dictionary for user data
    def __init__(self):
        self.user_data = {}


    # Extracts a name from the input text and assigns a UUID to the extracted name
    def extract_name(self, text):
        patterns = [
            r"My name is ([\w\s]+)",
            r"I am ([\w\s]+)",
            r"Call me ([\w\s]+)",
            r"You can call me ([\w\s]+)",
            r"My name's ([\w\s]+)",
            r"I'm ([\w\s]+)",
            r"^([\w\s]+)$"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                user_name = ' '.join(part.capitalize() for part in match.group(1).split())
                user_id = str(uuid4())
                self.user_data[user_id] = user_name
                return user_id

        return None
    
    # Retrieves the user's name from the stored user data using their unique ID
    def get_user_name(self, user_id):
        return self.user_data.get(user_id, None)

    # Retrieves the user's unique ID from the stored user data using their name
    def get_user_id(self, user_name):
        for id, name in self.user_data.items():
            if name == user_name:
                return id
        return None











import json
import random
import intent_recognition as ir
from restaurant_booking import RestaurantBooking
import re
import datetime

# Class to manage conversation context, holding the state and data of the conversation
class ConversationContext:
    def __init__(self):
        self.state = None
        self.data = {}

    # Sets the state of the conversation
    def set_state(self, state):
        self.state = state
        
    # Updates a specific data key-value pair within the conversation
    def update_data(self, key, value):
        self.data[key] = value

    # Retrieves a specific data value by its key
    def get_data(self, key):
        return self.data.get(key)

    # Resets the conversation context (state and data)
    def reset(self, keys_to_retain=[]):
        # Create a temporary dictionary to store the data to be retained
        retained_data = {key: self.data[key] for key in keys_to_retain if key in self.data}

        # Reset state and data
        self.state = None
        self.data.clear()

        # Restore the retained data back into the context
        self.data.update(retained_data)

# Loads response templates from the intents JSON file
def load_responses(intents_file):
    with open(intents_file) as file:
        intents_data = json.load(file)
        responses = {intent['tag']: intent['responses'] for intent in intents_data['intents']}
    return responses

# Global variables to store the components for intent recognition
vectorizer = None
X = None
labels = None
questions = None
answers = None
restaurant_questions = None  
restaurant_answers = None    

# Setup function to initialize global variables for intent recognition
def setup(vect, mat, lbls, qsts, answs, rest_qsts, rest_answs):
    global vectorizer, X, labels, questions, answers, restaurant_questions, restaurant_answers
    vectorizer = vect
    X = mat
    labels = lbls
    questions = qsts
    answers = answs
    restaurant_questions = rest_qsts  
    restaurant_answers = rest_answs

responses = load_responses('intents.json')


# Processes user input and generates a response based on the current context and booking system
def get_response(user_input, context, booking_system, intents):
    global vectorizer, X, labels, questions, answers, restaurant_questions, restaurant_answers


    # Handle user input based on current conversation state
    if context.state is None:
        # Recognize the type and specific tag of the user's intent
        intent_type, response_tag = ir.recognize_intent(user_input, vectorizer, X, labels, questions + restaurant_questions, answers + restaurant_answers)
        if intent_type == 'intent':
            # Respond based on the recognized intent tag
            if response_tag == 'name_query':
                user_name = context.get_data('user_name')
                # Fetch the response templates for the 'name_query' intent
                response_templates = next((item['responses'] for item in intents if item['tag'] == 'name_query'), [])
                # Choose a random response template
                response_template = random.choice(response_templates) if response_templates else "I'm not sure of your name yet."
                # Replace the placeholder with the actual user name
                response = response_template.replace("{detected_name}", user_name) if user_name else "I'm not sure of your name yet."
                return response, None
            if response_tag == 'how_are_you':
                context.set_state('responded_how_are_you')
                return "I'm a chatbot, so I don't have feelings, but thanks for asking! How are you?", None
            if response_tag == 'view_reservations':
                context.set_state('view_reservations')
                return "Ok, I'm going to need your reservation ID first please.", None          
            if response_tag in ['make_reservation', 'modify_reservation', 'cancel_reservation']:
                context.set_state(response_tag)
                if response_tag == 'make_reservation':
                    return "Wonderful, let's make a reservation. Firstly, could you please tell me the date you'd like to book for?", None
                elif response_tag == 'modify_reservation':
                    return "So you'd like to modify your reservation? Firstly, please provide your reservation ID.", None
                elif response_tag == 'cancel_reservation':
                    return "I'm sorry to hear that you'd like to cancel your reservation. Firstly, please provide your reservation ID", None
            else:
                return random.choice(responses.get(response_tag, ["I'm not sure how to respond to that, could you rephrase that?"])), None
        elif intent_type == 'qa':
            if response_tag in restaurant_answers:
                return response_tag, None
            else:
                return response_tag, None
        elif intent_type == 'unknown':
            return "I'm sorry, I didn't understand that. Could you rephrase or ask something else?", None
    # Handling responses based on the current state of the conversation  
    else:
        # Special handling for empty string in specific states
        if user_input == "":
            if context.state == "make_reservation":
                return "Wonderful, let's make a reservation. Firstly, could you please tell me the date you'd like to book for?", None
            elif context.state == "modify_reservation":
                return "So you'd like to modify your reservation? Firstly, please provide your reservation ID.", None
            elif context.state == "view_reservations":
                return "Ok, I'm going to need your reservation ID first please.", None
            elif context.state == "cancel_reservation":
                return "I'm sorry to hear that you'd like to cancel your reservation. Firstly, please provide your reservation ID.", None

        # Handle state-based response for non-empty input
        state_response = handle_state_based_response(user_input, context, booking_system)
        if state_response is not None:
            return state_response
        else:
            return "I'm sorry, something went wrong. Could you try again?", None



# Handles user input based on the current state in a state-based conversation
def handle_state_based_response(user_input, context, booking_system):
    max_party_size = 12  # Define the maximum party size


    # View reservations state: handle requests to view reservation details
    if context.state == 'view_reservations':
        # Check if the user is responding to the prompt to view another reservation
        if 'prompt_view_another' in context.data:
            if user_input.lower() == 'yes':
                # User wants to view another reservation
                context.data.pop('prompt_view_another', None)  # Remove the flag
                return "Ok, I'm going to need your reservation ID first please.", 'view_reservations'
            elif user_input.lower() == 'no':
                # User is done viewing reservations
                context.set_state(None)
                context.data.pop('prompt_view_another', None)  # Remove the flag
                return "Alright, let me know if there's anything else I can help with.", None
            else:
                # Unrecognized response, prompt again
                return "Would you like to view another reservation? Enter 'yes' to continue or 'no' to exit.", 'view_reservations'
            

        reservation_id = user_input.strip()  # Assuming the user inputs the reservation ID

        if reservation_id.isdigit() and booking_system.reservation_exists(reservation_id):
            reservation = booking_system.get_reservation_by_id(reservation_id)
            if reservation:
                # Format the reservation details
                formatted_reservation = f"Here are your reservation details for your Reservation ID({reservation[0]}): Table: {reservation[2]}, Date: {reservation[3]}, Time: {reservation[4]}, Party Size: {reservation[5]}"
                context.data['prompt_view_another'] = True  # Set a flag indicating a prompt for viewing another reservation is active
                return f"{formatted_reservation}\nWould you like to view another reservation? Enter 'yes' to continue or 'no' to exit.", 'view_reservations'
            else:
                return "Reservation details not found for the provided ID. Please enter a valid reservation ID:", 'view_reservations'
        else:
            return "Invalid reservation ID. Please enter a valid reservation ID:", 'view_reservations'


    # Responded to 'how are you': handle responses to the bot's wellbeing inquiry
    if context.state == 'responded_how_are_you':
        # Look for keywords indicating positive or negative sentiment
        positive_keywords = ['good', 'great', 'well', 'fantastic', 'happy', 'ecstatic']
        negative_keywords = ['bad', 'sad', 'unhappy', 'terrible', 'not well', 'not great', 'not good', 'down']

        # Check for positive sentiment
        if any(word in user_input.lower() for word in positive_keywords):
            response = "That's wonderful to hear!"
        
        # Check for negative sentiment
        elif any(word in user_input.lower() for word in negative_keywords):
            response = "I'm sorry to hear that, hopefully you'll feel better soon."
        
        # Neutral or unclear sentiment
        else:
            response = "Thanks for sharing."

        context.set_state(None)  # Reset state after handling
        return response, None

    # Make reservation state: guide through the reservation making process
    if context.state == 'make_reservation':
        if 'date' not in context.data:
            # Adjust the regular expression to extract date in DD-MM-YYYY format
            match = re.search(r'\b(\d{2}-\d{2}-\d{4})\b', user_input)
            if match:
                date_str = match.group(1)
                try:
                    # Validate/format date (DD-MM-YYYY)
                    entered_date = datetime.datetime.strptime(date_str, '%d-%m-%Y').date()
                    current_date = datetime.datetime.now().date()

                    # Check if the entered date is not in the past
                    if entered_date < current_date:
                        return "Sorry, you cannot book a reservation for a past date. Please enter a future date.", None

                    context.update_data('date', entered_date.strftime('%d-%m-%Y'))
                    return "Next, please enter the time for your reservation.", None
                except ValueError:
                    return "Sorry, that's an invalid date format. Please enter the date in DD-MM-YYYY format.", None
            else:
                return "Sorry, that's an invalid date format. Please enter the date in DD-MM-YYYY format.", None



        elif 'time' not in context.data:
            try:
                # Adjusting for inputs like "12 am" or "12pm"
                if match := re.match(r"(\d{1,2})\s*(am|pm)", user_input, re.IGNORECASE):
                    # Constructing time string with minutes assumed to be "00"
                    hour, meridiem = match.groups()
                    time_str = f"{hour}:00 {meridiem.upper()}"
                    time_obj = datetime.datetime.strptime(time_str, '%I:%M %p')
                else:
                    time_obj = datetime.datetime.strptime(user_input, '%H:%M')

                formatted_time = time_obj.strftime('%H:%M')
                context.update_data('time', formatted_time)
                return "Almost There! How many people will be in your table? Please note that each table can only host 12 people maximum.", None
            except ValueError:
                return "Sorry, that's an invalid time format. Please enter the time in HH:MM or HH:MM am/pm format.", None

        elif 'party_size' not in context.data:
            # Extract the number from the input
            match = re.search(r'(\d+)', user_input)
            if match:
                party_size = int(match.group(1))

                if 0 < party_size <= max_party_size:
                    context.update_data('party_size', party_size)
                    # Check table availability
                    available, tables = booking_system.check_availability(context.data['date'], context.data['time'], party_size)
                    if available:
                        # List only table IDs
                        table_ids = [str(table[0]) for table in tables]
                        context.update_data('available_tables', tables)
                        return f"Here's our available tables: {' ,'.join(table_ids)}. Lastly, please select a table by its ID.", None
                    else:
                        context.reset()
                        return "There are no available tables for the requested time, please try a different time.", None
                else:
                    return f"Sorry, that's an invalid table size. Please enter a number from 1 to {max_party_size}.", None
            else:
                return f"Sorry, that's an invalid table size. Please enter a number from 1 to {max_party_size}.", None

        elif 'selected_table' not in context.data:
            # Adjusting the regular expression to extract table ID from phrases like "Table 2"
            if match := re.match(r"Table\s*(\d+)", user_input, re.IGNORECASE):
                selected_table_id = match.group(1)
            elif user_input.isdigit():
                selected_table_id = user_input
            else:
                selected_table_id = None 

             # Check if the selected table ID is in the list of available tables   
            if selected_table_id.isdigit() and any(table[0] == int(selected_table_id) for table in context.data.get('available_tables', [])):
                context.update_data('selected_table', int(selected_table_id))


                # Check if 'user_id' is present in the context data
                if 'user_id' not in context.data:
                     context.reset()
                     # If 'user_id' is missing, return an appropriate message
                     return "There seems to be an issue with your session. Please start the reservation process again.", None
                
                # Convert 'date' from 'YYYY-MM-DD' to a more readable format
                formatted_date = datetime.datetime.strptime(context.data['date'], '%d-%m-%Y').strftime('%d %B %Y')
                # Add ordinal suffix to the day
                day = formatted_date.split()[0]
                suffix = 'th' if 11 <= int(day) <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(int(day) % 10, 'th')
                formatted_date = f"{day}{suffix} {formatted_date[3:]}"

                success, message, reservation_id = booking_system.make_reservation(
                    context.data['user_id'], 
                    formatted_date,  
                    context.data['time'], 
                    context.data['party_size'], 
                    context.data.get('user_name', ''), 
                    int(selected_table_id)
                )
                if success:
                    # Inform the user of successful reservation and ask if they want to make another one
                    response_message = f"{message} Take care!"
                    # Clear context data for a new transaction, but retain user info
                    user_id = context.get_data('user_id')
                    user_name = context.get_data('user_name')
                    context.reset()
                    context.update_data('user_id', user_id)
                    context.update_data('user_name', user_name)
                    return response_message, None
                else:
                    # Handle unsuccessful reservation attempt
                    return message, None     

            else:
                return "Sorry, we don't have that table. Please choose a valid table ID from the available options.", None
            
            

    # Modify reservation state: handle the process of modifying an existing reservation
    elif context.state == 'modify_reservation':
        if 'reservation_id' not in context.data:
            reservation_id = user_input.strip()
            if reservation_id.isdigit() and booking_system.reservation_exists(reservation_id):
                context.update_data('reservation_id', reservation_id)

                # Fetch and display current reservation details
                current_reservation = booking_system.get_reservation_by_id(reservation_id)
                if current_reservation:
                    # Extract details from the current_reservation
                    _, _, selected_table_id, date, time, party_size = current_reservation
                    details_message = f"I have your current reservation details as follows: Table {selected_table_id} booked for the Date - {date} - at {time}, for {party_size} people."
                else:
                    details_message = "Reservation details not found."

                return f"{details_message} Please provide the new date for your reservation (or say 'skip' to keep the current date).", None
            else:
                return "Sorry that's an invalid reservation ID. Please provide a valid reservation ID.", None
        
        elif 'new_date' not in context.data:
            if user_input.lower() != 'skip':
                # Extract date from the input like "On the 25-12-2023"
                match = re.search(r'\b(\d{2}-\d{2}-\d{4})\b', user_input)
                if match:
                    date_str = match.group(1)
                    try:
                        new_date = datetime.datetime.strptime(date_str, '%d-%m-%Y').date()
                        current_date = datetime.datetime.now().date()
                        
                        # Check if the entered date is not in the past
                        if new_date < current_date:
                            return "Sorry, you cannot book a reservation for a past date. Please enter a future date.", None
                        
                        context.update_data('new_date', new_date.strftime('%d-%m-%Y'))
                    except ValueError:
                        return "Sorry, that's an invalid date format. Please enter the date in DD-MM-YYYY format (or say 'skip' to keep your current date).", None
                else:
                    return "Sorry, I couldn't understand that. Could you provide the date in DD-MM-YYYY format (or say 'skip')?", None
            else:
                current_reservation = booking_system.get_reservation_by_id(context.data['reservation_id'])
                if current_reservation:
                    context.update_data('new_date', current_reservation[3])
                else:
                    return "There was an error retrieving your current reservation details.", None

                

            return "Next, please provide the new time for your reservation (or say 'skip' to keep the current time).", None


        elif 'new_time' not in context.data:
            if user_input.lower() != 'skip':
                # Adjusting for inputs like "2pm" or "11am"
                if match := re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", user_input, re.IGNORECASE):
                    # Extract hour, minute, and period (am/pm)
                    hour, minute, period = match.groups()
                    minute = minute or "00"
                    time_str = f"{hour}:{minute} {period.upper()}"
                    new_time = datetime.datetime.strptime(time_str, '%I:%M %p').strftime('%H:%M')
                else:
                    try:
                        # Validate/format time in 24-hour format
                        new_time = datetime.datetime.strptime(user_input, '%H:%M').strftime('%H:%M')
                    except ValueError:
                        return "Sorry, that's an invalid time format. Please enter the time in HH:MM or HH:MM am/pm format.", None

                context.update_data('new_time', new_time)
            else:
                current_reservation = booking_system.get_reservation_by_id(context.data['reservation_id'])
                if current_reservation:
                    context.update_data('new_time', current_reservation[4])
                else:
                    return "There was an error retrieving your current reservation details.", None


            return "Almost there, please provide the new table size (or say 'skip' to keep the current size).", None
        
        elif 'new_party_size' not in context.data:
            new_party_size = None  # Initialize new_party_size

            if user_input.lower() != 'skip':
                match = re.search(r'(\d+)', user_input)
                if match:
                    party_size = int(match.group(1))
                    if 0 < party_size <= max_party_size:
                        new_party_size = party_size
                    else:
                        return f"Sorry, that's an invalid table size. Please enter a number from 1 to {max_party_size} or say 'skip' to keep your current table size.", None
                else:
                    return f"Sorry, that's an invalid table size. Please enter a number from 1 to {max_party_size} or say 'skip'.", None
            else:
                # Retain existing party size from the current reservation
                current_reservation = booking_system.get_reservation_by_id(context.data['reservation_id'])
                if current_reservation:
                    new_party_size = current_reservation[5]

            # Update context data and check table availability
            if new_party_size is not None:
                context.update_data('new_party_size', new_party_size)
                available, tables = booking_system.check_availability(
                    context.data.get('new_date', context.get_data('date')),
                    context.data.get('new_time', context.get_data('time')),
                    new_party_size
                )
                if available:
                    table_ids = [str(table[0]) for table in tables]
                    context.update_data('available_tables', tables)
                    return f"Here are our available tables: {' ,'.join(table_ids)}. Lastly, please select a new table by its ID (or say 'skip' to keep your current table).", None
                else:
                    return "Sorry, there are no available tables for the requested time, please try a different time.", None

        elif 'new_table_id' not in context.data:
                # Initialize update_needed as False at the start
                update_needed = False

                current_reservation = booking_system.get_reservation_by_id(context.data['reservation_id'])
                if not current_reservation:
                    return "Sorry, there was an error retrieving your current reservation details.", None

                # Use existing reservation details if new values are not provided
                current_date, current_time, current_party_size, current_table_id = current_reservation[3], current_reservation[4], current_reservation[5], current_reservation[2]

                # Handling 'skip' input
                new_date = context.data.get('new_date', current_date)
                new_time = context.data.get('new_time', current_time)
                new_party_size = context.data.get('new_party_size', current_party_size)
                new_table_id = None

                if user_input.lower() != 'skip':
                    if user_input.isdigit():
                        new_table_id = int(user_input)
                        available_tables = context.data.get('available_tables', [])
                        if any(table[0] == new_table_id for table in available_tables):
                            is_available, _ = booking_system.check_availability(new_date, new_time, new_party_size, new_table_id)
                            if not is_available:
                                return "Sorry, the requested table is not available. Please choose a different table ID or say 'skip' to keep your current table.", None
                        else:
                            return "Sorry, that's an invalid table ID. Please enter a valid table ID or say 'skip' to keep your current table.", None
                else:
                    new_table_id = current_table_id

                # Check if any detail is updated
                update_needed = (
                    new_date != current_date or 
                    new_time != current_time or 
                    new_party_size != current_party_size or 
                    new_table_id != current_table_id
                )

                context.update_data('new_date', new_date)
                context.update_data('new_time', new_time)
                context.update_data('new_party_size', new_party_size)
                context.update_data('new_table_id', new_table_id)

                if update_needed:
                    # Perform the update if needed
                    success, message = booking_system.modify_reservation(
                        context.data['reservation_id'],
                        new_date,
                        new_time,
                        new_party_size,
                        new_table_id
                    )

                    user_id = context.get_data('user_id')
                    user_name = context.get_data('user_name')
                    context.reset()
                    context.update_data('user_id', user_id)
                    context.update_data('user_name', user_name)

                    if success:
                        return f"Good job! Your reservation has been updated to the following: Table {new_table_id} for the Date - {new_date} - at time {new_time}, for {new_party_size} people.", None
                    else:
                        return f"Sorry, we were unable to update your reservation: {message}", None
                else:
                    user_id = context.get_data('user_id')
                    user_name = context.get_data('user_name')
                    context.reset()
                    context.update_data('user_id', user_id)
                    context.update_data('user_name', user_name)
                    return "Alright, your reservation remains unchanged.", None
    
                    

    # Cancel reservation state: handle the process of canceling a reservation
    elif context.state == 'cancel_reservation':
          if 'confirm_cancel' not in context.data:
              reservation_id = user_input.strip()  # Assuming the user inputs the reservation ID directly

              # Check if the reservation ID exists in the system
              if reservation_id.isdigit() and booking_system.reservation_exists(reservation_id):
                  # Fetch and display current reservation details
                  current_reservation = booking_system.get_reservation_by_id(reservation_id)
                  if current_reservation:
                      # Extract details from the current_reservation
                      _, _, selected_table_id, date, time, party_size = current_reservation
                      details_message = f"Your current reservation details are for Table {selected_table_id} on the {date} at {time}, for {party_size} people."
                      context.update_data('reservation_id', reservation_id)
                      context.update_data('confirm_cancel', True)  # Flag to confirm cancellation
                      return f"{details_message}\nAre you sure you want to cancel this reservation? (yes/no)", None
                  else:
                      return "Sorry your reservation details could not be found. Please enter a valid reservation ID:", 'cancel_reservation'
              else:
                  # Invalid reservation ID format, prompt for a valid ID again
                  return "Sorry, you entered an invalid reservation ID. Please enter a valid reservation ID:", 'cancel_reservation'
          else:
              # Handle confirmation response
              if user_input.strip().lower() == 'yes':
                  # Proceed with cancellation
                  success, message = booking_system.cancel_reservation(context.data['reservation_id'])
                  context.reset(keys_to_retain=['user_name'])
                  return message, None
              elif user_input.strip().lower() == 'no':
                  context.reset(keys_to_retain=['user_name'])
                  return f"Ok, your reservation has not been cancelled.", None
              else:
                  return "Please respond with 'yes' or 'no':", 'cancel_reservation'

            
    # Fallback return - if none of the conditions are met
    return "I'm not sure how to proceed. Could you try a different request?", None

    

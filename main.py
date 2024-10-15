import conversation
import identity_management as idm
import intent_recognition as ir
from restaurant_booking import RestaurantBooking
from database import Database
import datetime
import json


# Function to return a time-based greeting based on the current hour
def get_time_based_greeting():
    current_hour = datetime.datetime.now().hour
    if 5 <= current_hour < 12:
        return "Good morning"
    elif 12 <= current_hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


# Main function to run the chatbot
def main():

    # Set up for intent recognition
    vectorizer, X, labels, questions, answers, restaurant_questions, restaurant_answers = ir.setup_intent_recognition('intents.json', 'qa_dataset.csv', 'restaurant_info.csv')

    # Initialize the database and the booking system
    db = Database('bookings.db')
    booking_system = RestaurantBooking('bookings.db')

    with open('intents.json') as file:
        intents = json.load(file)['intents']

    # Set up conversation context with intent recognition details
    conversation.setup(vectorizer, X, labels, questions, answers, restaurant_questions, restaurant_answers)
    identity_manager = idm.IdentityManager()


    # Initialize conversation context
    context = conversation.ConversationContext()

    # Get and display time-based greeting
    time_based_greeting = get_time_based_greeting()
    print(f"{time_based_greeting}, welcome to Nottingham Boulevard Dining. Firstly, could I take your name?")

    user_greeted = False   # Flag to check if user has been greeted


    # Main loop to handle user input
    while True:
        user_input = input("You: ").strip()

        # Handle exit commands
        if user_input.lower() == 'quit' or user_input.lower() == 'exit':
            print("Restaurant Bot: Goodbye!")
            break

        # Greet user and extract name only once per session
        if not user_greeted and not context.data.get('user_id'):
            user_id = identity_manager.extract_name(user_input)
            if user_id:
                user_name = identity_manager.get_user_name(user_id)
                context.update_data('user_id', user_id)
                context.update_data('user_name', user_name)
                print(f"Restaurant Bot: Greetings, {user_name}! I'm here to assist with your dining plans. You can ask me any questions or choose from the options below:\n"
                      "  1. Make a Reservation\n"
                      "  2. Modify a Reservation\n"
                      "  3. List Reservations\n"
                      "  4. Cancel a Reservation\n"
                      "Just type the number of the option you'd like to select.")
                user_greeted = True
                continue

        # Menu selection based on user input
        if context.state is None and user_input in ["1", "2", "3", "4"]:
            if user_input == "1":
                context.set_state("make_reservation")
            elif user_input == "2":
                context.set_state("modify_reservation")
            elif user_input == "3":
                context.set_state("view_reservations")
            elif user_input == "4":
                context.set_state("cancel_reservation")
            response, context_state = conversation.get_response("", context, booking_system, intents)
        else:
            response, context_state = conversation.get_response(user_input, context, booking_system, intents)

        # Handle transactional dialogue if context state is set
        if context_state:
            handle_transactional_dialogue(response, context_state, context, booking_system)
        else:
            print(f"Restaurant Bot: {response}")
            if not context.state:
                print("Restaurant Bot: Is there anything else I can help with, or would you like to press 'exit' to leave.")


# Function to handle transactional dialogue based on context state
def handle_transactional_dialogue(response, context_state, context, booking_system):
    while context.state:  
        if isinstance(response, tuple):
            prompt, _ = response
        else:
            prompt = response

        print(f"Restaurant Bot: {prompt}")

        user_input = input("You: ").strip()
        response, _ = conversation.handle_state_based_response(user_input, context, booking_system)

        if not context.state:
            print("Restaurant Bot: Is there anything else I can help with, or would you like to press 'exit' to leave.")
            context.reset(keys_to_retain=['user_name'])

# Run the main function if the script is executed
if __name__ == "__main__":
    main()





















































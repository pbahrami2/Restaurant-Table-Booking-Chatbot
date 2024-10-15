import sqlite3
import datetime

class RestaurantBooking:
    # Constructor to initialize the restaurant booking system with a database connection
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()



    # Method to check the availability of tables for a given date, time, and party size
    def check_availability(self, date, time, party_size, table_id=None, excluding_reservation_id=None):
      # Error handling for missing mandatory parameters
      if date is None or time is None or party_size is None:
          print("Error: Date, time, and party size must be provided.")
          return False, []

      try:
          # Define the SQL query to find tables with enough capacity
          table_query = "SELECT * FROM tables WHERE capacity >= ?"

          # Add a specific table ID condition if provided
          params = [party_size]
          if table_id:
              table_query += " AND id = ?"
              params.append(table_id)

          # Execute the query to find suitable tables
          self.cursor.execute(table_query, params)
          potential_tables = self.cursor.fetchall()

          available_tables = []
          for table in potential_tables:
              # Check for existing reservations for each table
              reservation_query = "SELECT * FROM reservations WHERE table_id = ? AND date = ? AND time = ?"
              reservation_params = [table[0], date, time]

              # Exclude a specific reservation ID if provided
              if excluding_reservation_id:
                  reservation_query += " AND id != ?"
                  reservation_params.append(excluding_reservation_id)

              self.cursor.execute(reservation_query, reservation_params)
              if not self.cursor.fetchone():
                  available_tables.append(table)

          return len(available_tables) > 0, available_tables

      except sqlite3.Error as e:
          print("Database error:", e)
          return False, []



    def make_reservation(self, user_id, formatted_date, time, party_size, user_name, selected_table_id):
    # Insert a new reservation into the database and return confirmation along with the reservation ID
    
        is_available, _ = self.check_availability(formatted_date, time, party_size)
        # Check if the selected table is available
        if is_available:
            try:
                # Use the selected table ID for the reservation
                self.cursor.execute("INSERT INTO reservations (user_id, table_id, date, time, party_size) VALUES (?, ?, ?, ?, ?)", (user_id, selected_table_id, formatted_date, time, party_size))
                self.conn.commit()
                # Fetch the ID of the newly created reservation
                reservation_id = self.cursor.lastrowid
            
                # Output the reservation details, including the formatted date, in the confirmation message
                return True, f"Great, your reservation is confirmed for Table {selected_table_id} for {party_size} people at {time} on the {formatted_date}. Your reservation ID is {reservation_id}. We look forward to seeing you.", reservation_id
            except sqlite3.Error as e:
                print("Database error:", e)
                return False, "Sorry, we failed to make a reservation", None
        else:
            return False, "No available tables for the requested time", None
        
    
    def modify_reservation(self, reservation_id, new_date=None, new_time=None, new_party_size=None, new_table_id=None):
      # Method to modify an existing reservation by updating the user's current reservation details
      try:
          self.cursor.execute("SELECT * FROM reservations WHERE id = ?", (reservation_id,))
          reservation = self.cursor.fetchone()
          if not reservation:
              return False, "Reservation not found", None

          # Use existing reservation details if new values are not provided
          updated_table_id = new_table_id or reservation[2]
          updated_date = new_date or reservation[3]
          updated_time = new_time or reservation[4]
          updated_party_size = new_party_size or reservation[5]

          is_available, _ = self.check_availability(updated_date, updated_time, updated_party_size, updated_table_id, excluding_reservation_id=reservation_id)
          if not is_available:
              return False, "Requested time or table is not available", None

          self.cursor.execute("UPDATE reservations SET date = ?, time = ?, party_size = ?, table_id = ? WHERE id = ?", (updated_date, updated_time, updated_party_size, updated_table_id, reservation_id))
          self.conn.commit()

          return True, "Reservation updated"
      except sqlite3.Error as e:
          print("Database error:", e)
          return False, "Failed to modify reservation", None

        
    def get_reservation_by_id(self, reservation_id):
        # Query the database for a specific reservation using its ID
        try:
            self.cursor.execute("SELECT * FROM reservations WHERE id = ?", (reservation_id,))
            reservation = self.cursor.fetchone()
            return reservation if reservation else None
        except sqlite3.Error as e:
            print("Database error:", e)
            return None   
        
    def reservation_exists(self, reservation_id):
        # Confirm if a reservation ID exists in the database
        try:
            self.cursor.execute("SELECT * FROM reservations WHERE id = ?", (reservation_id,))
            return self.cursor.fetchone() is not None
        except sqlite3.Error as e:
            print("Database error:", e)
            return False
        


    def cancel_reservation(self, reservation_id):
        # Remove a reservation from the database using its ID
        try:
            self.cursor.execute("DELETE FROM reservations WHERE id = ?", (reservation_id,))
            self.conn.commit()
            return True, "Your reservation has been successfully cancelled."
        except sqlite3.Error as e:
            print("Database error:", e)
            return False, "Your reservation has not been cancelled."

    def list_reservations(self, user_id):
        # Retrieve all reservations from the database for a given user
        try:
            self.cursor.execute("SELECT * FROM reservations WHERE user_id = ?", (user_id,))
            reservations = self.cursor.fetchall()
            return True, reservations
        except sqlite3.Error as e:
            print("Database error:", e)
            return False, []

    # Destructor to close the database connection when the object is destroyed
    def __del__(self):
        self.conn.close()



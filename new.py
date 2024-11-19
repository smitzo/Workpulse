import os
import json
import customtkinter as ctk
from tkinter import ttk, StringVar, messagebox
from tkcalendar import DateEntry
from PIL import Image
import pymysql
from datetime import datetime
from login import User
from config import DATABASE_CONFIG

# Path to the clock configuration file
CLOCK_CONFIG_FILE = "clock_config.json"

class NewRecordForm:
    def __init__(self, parent=None):
        self.parent = parent
        self.app = ctk.CTkToplevel() if parent else ctk.CTk()
        self.app.geometry("1400x950")
        self.app.resizable(True, True)
        self.app.title("Form Filling with Time Tracker")
        
        # Initialize clock state from the JSON file
        self.clock_on = self.load_clock_state()
        self.setup_background()
        self.setup_variables()
        self.create_form()

    def setup_background(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        background_image_path = os.path.join(current_dir, "assets", "bg3.png")
        background_image = ctk.CTkImage(Image.open(background_image_path), size=(1400, 950))
        background_label = ctk.CTkLabel(self.app, image=background_image, text="")
        background_label.place(relx=0.5, rely=0.5, anchor="center")

        # Add user details in top right
        user = User.get_instance()
        user_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        user_frame.place(relx=0.95, rely=0.05, anchor="e")
        
        user_name = ctk.CTkLabel(
            user_frame, 
            text=f"Name: {user.get_username()}", 
            font=("Arial", 14, "bold"), 
            text_color="white"
        )
        user_name.pack(anchor="e")

        designation = ctk.CTkLabel(
            user_frame, 
            text=f"Designation: {user.get_designation()}", 
            font=("Arial", 14, "bold"), 
            text_color="white"
        )
        designation.pack(anchor="e")
        
        software_authority = ctk.CTkLabel(
            user_frame, 
            text=f"Software Authority: {user.get_software_authority()}", 
            font=("Arial", 14, "bold"), 
            text_color="white"
        )
        software_authority.pack(anchor="e")

    def setup_variables(self):
        user = User.get_instance()
        self.user_id_var = StringVar(value=user.get_user_id())  # Autofill user ID from login credentials
        self.so_number_var = StringVar()
        self.start_time_var = StringVar(value="09:00")  # Default start time
        self.end_time_var = StringVar(value="17:00")  # Default end time
        self.work_hours_var = StringVar()  # Variable for work hours (auto-calculated or manual)
        self.work_type_var = StringVar()
        self.details_of_work_var = StringVar()
        self.remark_var = StringVar()
        self.work_time_type_var = StringVar()
        self.work_details_options = self.fetch_work_details()
        self.so_number_options = self.fetch_so_numbers()  # Fetch SO numbers

    def fetch_so_numbers(self):
        """Fetch all SO numbers from the so_numbers table."""
        try:
            connection = pymysql.connect(**DATABASE_CONFIG)
            cursor = connection.cursor()
            cursor.execute("SELECT so_number FROM so_numbers")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch SO numbers: {e}")
            return []
        finally:
            if 'connection' in locals() and connection.open:
                connection.close()

    def fetch_work_details(self):
        try:
            connection = pymysql.connect(**DATABASE_CONFIG)
            cursor = connection.cursor()
            cursor.execute("SELECT details_of_work FROM work_details_table")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch work details: {e}")
            return ["Planning", "Execution", "Review"]
        finally:
            if 'connection' in locals() and connection.open:
                connection.close()

    def load_clock_state(self):
        """Load the clock state from the JSON file."""
        try:
            if os.path.exists(CLOCK_CONFIG_FILE):
                with open(CLOCK_CONFIG_FILE, "r") as file:
                    config = json.load(file)
                    return config.get("clock_on", True)  # Default to True if key not found
            else:
                # If the file doesn't exist, create it with the default state (clock on)
                self.save_clock_state(True)
                return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load clock state: {e}")
            return True  # Default to True if an error occurs

    def save_clock_state(self, clock_on):
        """Save the clock state to the JSON file."""
        try:
            with open(CLOCK_CONFIG_FILE, "w") as file:
                json.dump({"clock_on": clock_on}, file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save clock state: {e}")

    def create_form(self):
        header_font = ctk.CTkFont(size=14, weight="bold")
        main_frame = ctk.CTkFrame(self.app, fg_color="midnightblue", corner_radius=0, width=950, height=550)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Add Clock On/Off toggle button (only for Managers or Developers)
        user = User.get_instance()
        if user.get_designation() in ["Manager", "Developer"] or user.get_software_authority() == "Developer":
            self.clock_button = ctk.CTkButton(
                main_frame, 
                text="Clock On" if self.clock_on else "Clock Off", 
                command=self.toggle_clock, 
                fg_color="green" if self.clock_on else "red", 
                hover_color="darkgreen" if self.clock_on else "darkred"
            )
            self.clock_button.grid(row=0, column=2, padx=10, pady=10, sticky="e")

        # Form fields
        self.widgets = [
            ("Date", DateEntry(main_frame, width=30, height=40, background="darkblue", foreground="white", date_pattern="yyyy-mm-dd")),
            ("User ID", ctk.CTkEntry(main_frame, textvariable=self.user_id_var, width=200, height=40, state="readonly")),  # Make User ID read-only
            ("SO Number", ttk.Combobox(main_frame, textvariable=self.so_number_var, values=self.so_number_options, width=30, height=40)),  # Dropdown for SO numbers
            ("Start Time", self.create_time_picker(main_frame, self.start_time_var)),  # Time picker for start time
            ("End Time", self.create_time_picker(main_frame, self.end_time_var)),  # Time picker for end time
            ("Work Hours", ctk.CTkEntry(main_frame, textvariable=self.work_hours_var, width=200, height=40, state="readonly")),  # Read-only field for work hours
            ("Work Type", ttk.Combobox(main_frame, textvariable=self.work_type_var, values=["Standard", "Non-Standard"], width=30, height=40)),
            ("Details of Work", ttk.Combobox(main_frame, textvariable=self.details_of_work_var, values=self.work_details_options, width=30, height=40)),
            ("Remarks", ctk.CTkEntry(main_frame, textvariable=self.remark_var, width=200, height=40)),
            ("Work Time Type", ttk.Combobox(main_frame, textvariable=self.work_time_type_var, values=["Standard Time", "Over Time"], width=30, height=40))
        ]

        for i, (label_text, widget) in enumerate(self.widgets):
            label = ctk.CTkLabel(main_frame, text=label_text, font=header_font, text_color="white")
            label.grid(row=i+1, column=0, padx=10, pady=10, sticky="e")
            if isinstance(widget, tuple):  # Handle time picker widget
                widget[0].grid(row=i+1, column=1, padx=10, pady=10, sticky="w")
            else:
                widget.grid(row=i+1, column=1, padx=10, pady=10)
            if label_text == "Date":
                self.date_selector = widget
            elif label_text == "Work Hours":
                self.work_hours_entry = widget  # Assign the work_hours_entry widget to self.work_hours_entry

        # Buttons
        self.create_buttons(main_frame)

        # Initialize form based on clock state
        self.update_form_fields()

    def toggle_clock(self):
        """Toggle between Clock On and Clock Off states (only for Managers or Developers)."""
        user = User.get_instance()
        if user.get_designation() in ["Manager", "Developer"] or user.get_software_authority() == "Developer":
            self.clock_on = not self.clock_on
            self.save_clock_state(self.clock_on)  # Save the new state to the JSON file
            self.update_form_fields()
            if self.clock_on:
                self.clock_button.configure(text="Clock On", fg_color="green", hover_color="darkgreen")
            else:
                self.clock_button.configure(text="Clock Off", fg_color="red", hover_color="darkred")
        else:
            messagebox.showwarning("Access Denied", "Only Managers or Developers can toggle the clock.")

    def update_form_fields(self):
        """Show/hide fields based on the clock state."""
        if self.clock_on:
            # Show start_time and end_time, hide work_hours
            self.widgets[3][1].grid()  # Start Time
            self.widgets[4][1].grid()  # End Time
            self.widgets[5][1].grid()  # Work Hours (show but keep readonly)
            self.work_hours_entry.configure(state="readonly")  # Keep Work Hours readonly in Clock On mode
        else:
            # Hide start_time and end_time, show work_hours and make it editable
            self.widgets[3][1].grid_remove()  # Start Time
            self.widgets[4][1].grid_remove()  # End Time
            self.widgets[5][1].grid()  # Work Hours
            self.work_hours_entry.configure(state="normal")  # Enable Work Hours for manual input in Clock Off mode

    def create_time_picker(self, parent, time_var):
        """Create a time picker with hours and minutes."""
        time_frame = ctk.CTkFrame(parent, fg_color="transparent")

        # Hours entry
        hours_entry = ctk.CTkEntry(time_frame, width=50, height=30, justify="center")
        hours_entry.insert(0, "")  # Default hours
        hours_entry.configure(validate="key", validatecommand=(parent.register(self.validate_hours), "%P"))

        # Minutes entry
        minutes_entry = ctk.CTkEntry(time_frame, width=50, height=30, justify="center")
        minutes_entry.insert(0, "")  # Default minutes
        minutes_entry.configure(validate="key", validatecommand=(parent.register(self.validate_minutes), "%P"))

        # Colon separator
        colon_label = ctk.CTkLabel(time_frame, text=":", font=("Arial", 14))

        # Pack widgets
        hours_entry.pack(side="left", padx=(0, 5))
        colon_label.pack(side="left")
        minutes_entry.pack(side="left", padx=(5, 0))

        # Bind variables
        hours_entry.bind("<KeyRelease>", lambda event: self.update_time_var(time_var, hours_entry, minutes_entry))
        minutes_entry.bind("<KeyRelease>", lambda event: self.update_time_var(time_var, hours_entry, minutes_entry))

        return time_frame  # Return only the time_frame

    def validate_hours(self, value):
        """Validate hours input (0-23)."""
        if value.isdigit():
            return 0 <= int(value) <= 23
        return False

    def validate_minutes(self, value):
        """Validate minutes input (0-59)."""
        if value.isdigit():
            return 0 <= int(value) <= 59
        return False

    def update_time_var(self, time_var, hours_entry, minutes_entry):
        """Update the time variable when hours or minutes change."""
        hours = hours_entry.get().zfill(2)
        minutes = minutes_entry.get().zfill(2)
        time_var.set(f"{hours}:{minutes}")
        if self.clock_on:
            self.calculate_work_hours()  # Recalculate work hours when time changes

    def calculate_work_hours(self):
        """Calculate work hours based on start_time and end_time."""
        try:
            start_time = datetime.strptime(self.start_time_var.get(), "%H:%M").time()
            end_time = datetime.strptime(self.end_time_var.get(), "%H:%M").time()

            # Calculate work_hours as a float
            start_datetime = datetime.combine(datetime.today(), start_time)
            end_datetime = datetime.combine(datetime.today(), end_time)
            work_hours = (end_datetime - start_datetime).total_seconds() / 3600  # Convert seconds to hours

            if work_hours <= 0:
                messagebox.showerror("Error", "End Time must be after Start Time")
                return

            self.work_hours_var.set(f"{work_hours:.2f}")  # Update work_hours field with 2 decimal places
        except ValueError:
            self.work_hours_var.set("")  # Clear work_hours if time is invalid

    def create_buttons(self, main_frame):
        buttons = [
            ("💾 Submit", self.submit_action, "green", 8),
            ("↻ Reset", self.reset_action, "darkred", 9),
            ("<< Back", self.back_action, None, 10)
        ]

        for text, command, color, row in buttons:
            button = ctk.CTkButton(main_frame, text=text, command=command, fg_color=color, width=200, height=40)
            button.grid(row=row+2, column=1, padx=10, pady=20)

    def submit_action(self):
        # Add validation
        if not self.user_id_var.get():
            messagebox.showerror("Error", "User ID is a required field")
            return

        if self.clock_on:
            # Validate start_time and end_time in Clock On mode
            if not self.start_time_var.get() or not self.end_time_var.get():
                messagebox.showerror("Error", "Start Time and End Time are required in Clock On mode")
                return

            try:
                # Parse start_time and end_time
                start_time = datetime.strptime(self.start_time_var.get(), "%H:%M").time()
                end_time = datetime.strptime(self.end_time_var.get(), "%H:%M").time()

                # Calculate work_hours as a float
                start_datetime = datetime.combine(datetime.today(), start_time)
                end_datetime = datetime.combine(datetime.today(), end_time)
                work_hours = (end_datetime - start_datetime).total_seconds() / 3600  # Convert seconds to hours

                if work_hours <= 0:
                    messagebox.showerror("Error", "End Time must be after Start Time")
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid time format. Please use HH:MM")
                return
        else:
            # Validate work_hours in Clock Off mode
            if not self.work_hours_var.get():
                messagebox.showerror("Error", "Work Hours is a required field in Clock Off mode")
                return

            try:
                work_hours = float(self.work_hours_var.get())
                if work_hours <= 0:
                    messagebox.showerror("Error", "Work Hours must be a positive number")
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid Work Hours. Please enter a valid number")
                return

        try:
            connection = pymysql.connect(**DATABASE_CONFIG)
            cursor = connection.cursor()

            query = """
            INSERT INTO work_logs (user_id, log_date, so_number, start_time, end_time, work_hours, 
                work_category, details_of_work, remarks, time_category)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                self.user_id_var.get(),
                self.date_selector.get(),
                self.so_number_var.get(),
                self.start_time_var.get() if self.clock_on else None,  # Start time is optional in Clock Off mode
                self.end_time_var.get() if self.clock_on else None,    # End time is optional in Clock Off mode
                float(self.work_hours_var.get()),  # Ensure work_hours is stored as a float
                self.work_type_var.get(),
                self.details_of_work_var.get(),
                self.remark_var.get(),
                self.work_time_type_var.get()
            )
            cursor.execute(query, values)
            connection.commit()
            messagebox.showinfo("Success", "Form submitted successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}. You cannot enter data for invalid user IDs.")
        finally:
            if 'connection' in locals() and connection.open:
                connection.close()

    def reset_action(self):
        for var in [self.user_id_var, self.so_number_var, 
                    self.start_time_var, self.end_time_var, 
                    self.work_hours_var, self.work_type_var, 
                    self.details_of_work_var, self.remark_var, 
                    self.work_time_type_var]:
            var.set("")
        self.date_selector.set_date(datetime.now())

    def back_action(self):
        self.app.destroy()
        if self.parent:
            self.parent.deiconify()

    def run(self):
        if self.parent:
            self.parent.withdraw()
        self.app.mainloop()
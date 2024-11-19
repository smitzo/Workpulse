# import json
# import os
# import threading
# from tkinter import messagebox
# import customtkinter as ctk
# import pymysql
# from login import User
# from config import DATABASE_CONFIG

# class EmployeeLimitConfig:
#     DEFAULT_LIMIT = 100

#     @staticmethod
#     def get_config_path():
#         """Get the path to the hidden config file."""
#         if os.name == "nt":  # Windows
#             config_dir = os.path.join(os.getenv("APPDATA"), "EmployeeManagement")  # Hidden in AppData
#         else:  # Linux/macOS
#             config_dir = os.path.expanduser("~/.employeemanagement")  # Hidden in home directory

#         # Create the hidden directory if it doesn't exist
#         os.makedirs(config_dir, exist_ok=True)

#         # Use a non-obvious file name
#         return os.path.join(config_dir, "config.json")

#     @staticmethod
#     def initialize_config():
#         """Initialize the config file with default values if it doesn't exist."""
#         config_path = EmployeeLimitConfig.get_config_path()
#         if not os.path.exists(config_path):
#             default_config = {"employee_limit": EmployeeLimitConfig.DEFAULT_LIMIT}
#             with open(config_path, "w") as f:
#                 json.dump(default_config, f)
#             print(f"Created default config file at: {config_path}")

#     @staticmethod
#     def load_config():
#         """Load the configuration file from the hidden location."""
#         config_path = EmployeeLimitConfig.get_config_path()
#         if not os.path.exists(config_path):
#             # If the file doesn't exist, create it with the default limit
#             default_config = {"employee_limit": EmployeeLimitConfig.DEFAULT_LIMIT}
#             with open(config_path, "w") as f:
#                 json.dump(default_config, f)
#             return default_config

#         try:
#             with open(config_path, "r") as f:
#                 config = json.load(f)
#                 # Validate the config
#                 if not isinstance(config, dict) or "employee_limit" not in config:
#                     raise ValueError("Invalid config file format")
#                 if not isinstance(config["employee_limit"], int) or config["employee_limit"] <= 0:
#                     raise ValueError("Invalid employee limit value")
#                 return config
#         except (json.JSONDecodeError, ValueError, IOError) as e:
#             messagebox.showerror("Config Error", f"Error loading config: {str(e)}\nUsing default limit.")
#             return {"employee_limit": EmployeeLimitConfig.DEFAULT_LIMIT}

#     @staticmethod
#     def save_config(config):
#         """Save the configuration file to the hidden location."""
#         config_path = EmployeeLimitConfig.get_config_path()
#         try:
#             with open(config_path, "w") as f:
#                 json.dump(config, f, indent=4)
#         except (IOError, OSError) as e:
#             messagebox.showerror("Error", f"Failed to save config: {str(e)}")
#             raise

#     @staticmethod
#     def get_employee_limit():
#         """Get the employee limit from the config file."""
#         config = EmployeeLimitConfig.load_config()
#         return config.get("employee_limit", EmployeeLimitConfig.DEFAULT_LIMIT)

# class DeveloperSettings:
#     def __init__(self, parent):
#         self.window = ctk.CTkToplevel(parent)
#         self.window.title("Developer Settings")
#         self.window.geometry("800x400")
#         self.window.resizable(False, False)  # Lock window size
#         self.window.transient(parent)
#         self.window.grab_set()
#         # Store reference to parent
#         self.parent = parent
#         # Bind window close event
#         self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
#         self.setup_ui()

#     def setup_ui(self):
#         # Create main frame with padding
#         main_frame = ctk.CTkFrame(self.window)
#         main_frame.pack(fill="both", expand=True, padx=20, pady=20)

#         # Title
#         title_label = ctk.CTkLabel(
#             main_frame, 
#             text="Developer Settings", 
#             font=("Arial", 20, "bold")
#         )
#         title_label.pack(pady=(0,20))

#         # Current limit display
#         current_limit = EmployeeLimitConfig.get_employee_limit()
#         self.current_limit_label = ctk.CTkLabel(
#             main_frame,
#             text=f"Current Employee Limit: {current_limit}",
#             font=("Arial", 14)
#         )
#         self.current_limit_label.pack(pady=10)

#         # New limit entry
#         limit_frame = ctk.CTkFrame(main_frame)
#         limit_frame.pack(pady=20)

#         limit_label = ctk.CTkLabel(
#             limit_frame,
#             text="New Employee Limit:",
#             font=("Arial", 12)
#         )
#         limit_label.pack(side="left", padx=5)

#         self.limit_entry = ctk.CTkEntry(limit_frame, width=100, justify="center")
#         self.limit_entry.pack(side="left", padx=5)
#         self.limit_entry.insert(0, str(current_limit))

#         # Buttons frame
#         button_frame = ctk.CTkFrame(main_frame)
#         button_frame.pack(pady=20)

#         # Save button
#         save_button = ctk.CTkButton(
#             button_frame,
#             text="Save Limit",
#             command=self.save_limit
#         )
#         save_button.pack(pady=20)

#         # Cancel button
#         cancel_button = ctk.CTkButton(
#             button_frame,
#             text="Cancel",
#             command=self.on_closing,
#             width=100
#         )
#         cancel_button.pack(side="left", padx=5)

#         # Delete Data button
#         delete_data_button = ctk.CTkButton(
#             button_frame,
#             text="Delete Data",
#             command=self.delete_data,
#             fg_color="red",  # Make it red to indicate a dangerous action
#             hover_color="darkred"
#         )
#         delete_data_button.pack(pady=20)

#     def validate_limit(self, limit_str):
#         try:
#             limit = int(limit_str)
#             if limit <= 0:
#                 raise ValueError("Employee limit must be a positive number")
#             if limit > 1000000:  # Add reasonable upper limit
#                 raise ValueError("Employee limit cannot exceed 1,000,000")
#             return limit
#         except ValueError as e:
#             if "invalid literal for int()" in str(e):
#                 raise ValueError("Please enter a valid number")
#             raise

#     def save_limit(self):
#         try:
#             new_limit_str = self.limit_entry.get().strip()
#             if not new_limit_str:
#                 messagebox.showerror("Error", "Please enter a value")
#                 return

#             new_limit = self.validate_limit(new_limit_str)

#             # Confirm if the change is significant
#             current_limit = EmployeeLimitConfig.get_employee_limit()
#             if abs(new_limit - current_limit) > current_limit * 0.5:  # 50% change
#                 if not messagebox.askyesno("Confirm Change", 
#                     f"Are you sure you want to change the employee limit from {current_limit} to {new_limit}?"):
#                     return

#             # Save the new limit to the config file
#             config = EmployeeLimitConfig.load_config()
#             config["employee_limit"] = new_limit
#             EmployeeLimitConfig.save_config(config)

#             self.current_limit_label.configure(
#                 text=f"Current Employee Limit: {new_limit}"
#             )
#             messagebox.showinfo("Success", f"Employee limit updated to {new_limit}")
#             self.window.destroy()

#         except ValueError as e:
#             messagebox.showerror("Error", str(e))
#         except Exception as e:
#             messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

#     def verify_password(self, user_id, password):
#         try:
#             # Connect to the database using pymysql
#             connection = pymysql.connect(**DATABASE_CONFIG)
#             with connection.cursor() as cursor:
#                 # Fetch the password for the given user_id from the employee table
#                 query = "SELECT password FROM employees WHERE user_id = %s"
#                 cursor.execute(query, (user_id,))
#                 result = cursor.fetchone()

#                 if result:
#                     # Compare the fetched password with the entered password
#                     return result[0] == password  # Access the first element of the tuple
#                 else:
#                     messagebox.showerror("Error", "User ID not found in the database.")
#                     return False

#         except pymysql.Error as e:
#             messagebox.showerror("Error", f"Failed to verify password: {str(e)}")
#             return False

#         finally:
#             if connection:
#                 connection.close()

#     def delete_data(self):
#         attempts = 2
#         user_id = User.get_instance().get_user_id()  # Replace this with the actual user ID
#         correct_password_count = 0  # Track how many times the correct password was entered

#         for i in range(attempts):
#             password = ctk.CTkInputDialog(text="Enter password to delete all data:", title="Password Verification").get_input()

#             if password is None:
#                 return  # User canceled the operation

#             if self.verify_password(user_id, password):
#                 correct_password_count += 1
#                 if correct_password_count == attempts:
#                     # If the password is correct 5 times in a row, proceed to delete data
#                     self.confirm_and_delete_database()
#                     return
#                 else:
#                     messagebox.showinfo("Success", f"Password correct. {attempts - correct_password_count} attempts remaining.")
#             else:
#                 messagebox.showerror("Error", "Incorrect password. Process terminated.")
#                 return  # Terminate if the password is incorrect

#         messagebox.showerror("Error", "Failed to verify password. Data deletion aborted.")

#     def confirm_and_delete_database(self):
#         if not messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the entire database? This action cannot be undone."):
#             return

#         # Run the deletion process in a separate thread
#         threading.Thread(target=self._delete_database_thread, daemon=True).start()

#     def _delete_database_thread(self):
#         connection = None
#         try:
#             # Connect to the database using pymysql
#             connection = pymysql.connect(
#                 host=DATABASE_CONFIG["host"],
#                 user=DATABASE_CONFIG["user"],
#                 password=DATABASE_CONFIG["password"]
#             )
#             with connection.cursor() as cursor:
#                 # Drop the database
#                 cursor.execute(f"DROP DATABASE {DATABASE_CONFIG['database']}")
#                 print(f"Deleted database: {DATABASE_CONFIG['database']}")

#                 # Recreate the database
#                 cursor.execute(f"CREATE DATABASE {DATABASE_CONFIG['database']}")
#                 print(f"Recreated database: {DATABASE_CONFIG['database']}")

#                 # Commit the changes
#                 connection.commit()

#             # Show success message (must be done in the main thread)
#             self.window.after(0, lambda: messagebox.showinfo("Success", "Database has been deleted and recreated."))

#         except pymysql.Error as e:
#             # Show error message (must be done in the main thread)
#             self.window.after(0, lambda: messagebox.showerror("Error", f"Failed to delete database: {str(e)}"))

#         finally:
#             if connection:
#                 connection.close()

#     def on_closing(self):
#         self.window.grab_release()
#         self.window.destroy()

import json
import os
import threading
from tkinter import messagebox
import customtkinter as ctk
import pymysql
from login import User
from config import DATABASE_CONFIG

class EmployeeLimitConfig:
    DEFAULT_LIMIT = 100

    @staticmethod
    def get_config_path():
        """Get the path to the hidden config file."""
        if os.name == "nt":  # Windows
            config_dir = os.path.join(os.getenv("APPDATA"), "EmployeeManagement")
        else:  # Linux/macOS
            config_dir = os.expanduser("~/.employeemanagement")

        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "config.json")

    @staticmethod
    def initialize_config():
        """Initialize the config file with default values if it doesn't exist."""
        config_path = EmployeeLimitConfig.get_config_path()
        if not os.path.exists(config_path):
            default_config = {"employee_limit": EmployeeLimitConfig.DEFAULT_LIMIT}
            with open(config_path, "w") as f:
                json.dump(default_config, f)
            print(f"Created default config file at: {config_path}")

    @staticmethod
    def load_config():
        """Load the configuration file from the hidden location."""
        config_path = EmployeeLimitConfig.get_config_path()
        if not os.path.exists(config_path):
            default_config = {"employee_limit": EmployeeLimitConfig.DEFAULT_LIMIT}
            with open(config_path, "w") as f:
                json.dump(default_config, f)
            return default_config

        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                if not isinstance(config, dict) or "employee_limit" not in config:
                    raise ValueError("Invalid config file format")
                if not isinstance(config["employee_limit"], int) or config["employee_limit"] <= 0:
                    raise ValueError("Invalid employee limit value")
                return config
        except (json.JSONDecodeError, ValueError, IOError) as e:
            messagebox.showerror("Config Error", f"Error loading config: {str(e)}\nUsing default limit.")
            return {"employee_limit": EmployeeLimitConfig.DEFAULT_LIMIT}

    @staticmethod
    def save_config(config):
        """Save the configuration file to the hidden location."""
        config_path = EmployeeLimitConfig.get_config_path()
        try:
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)
        except (IOError, OSError) as e:
            messagebox.showerror("Error", f"Failed to save config: {str(e)}")
            raise

    @staticmethod
    def get_employee_limit():
        """Get the employee limit from the config file."""
        config = EmployeeLimitConfig.load_config()
        return config.get("employee_limit", EmployeeLimitConfig.DEFAULT_LIMIT)

class DatabaseConfigManager:
    def __init__(self, parent):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Database Configuration")
        self.window.geometry("600x700")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        self.parent = parent
        self.connection_check_after_id = None
        self.setup_ui()
        self.check_connection()

    def setup_ui(self):
        self.main_frame = ctk.CTkFrame(self.window)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="Database Configuration",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Connection Status
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.pack(fill="x", padx=20, pady=(0, 20))

        status_label = ctk.CTkLabel(
            self.status_frame,
            text="Connection Status:",
            font=("Arial", 14)
        )
        status_label.pack(side="left", padx=(0, 10))

        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=("Arial", 24),
            text_color="gray"
        )
        self.status_indicator.pack(side="left")

        # Configuration Display
        config_display = ctk.CTkFrame(self.main_frame)
        config_display.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            config_display,
            text="Current Configuration",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 10))

        # Config Entry Fields
        self.config_entries = {}
        for key, value in DATABASE_CONFIG.items():
            frame = ctk.CTkFrame(config_display)
            frame.pack(fill="x", pady=5)

            ctk.CTkLabel(
                frame,
                text=f"{key}:",
                font=("Arial", 12),
                width=100
            ).pack(side="left", padx=5)

            entry = ctk.CTkEntry(frame, width=300)
            entry.insert(0, str(value))
            entry.pack(side="left", padx=5)
            self.config_entries[key] = entry

        # Buttons
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(pady=20)

        test_conn_button = ctk.CTkButton(
            button_frame,
            text="Test Connection",
            command=self.test_connection
        )
        test_conn_button.pack(pady=10)

        save_button = ctk.CTkButton(
            button_frame,
            text="Save Configuration",
            command=self.save_configuration
        )
        save_button.pack(pady=10)

        reset_button = ctk.CTkButton(
            button_frame,
            text="Reset to Default",
            command=self.reset_to_default
        )
        reset_button.pack(pady=10)

        close_button = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.on_closing
        )
        close_button.pack(pady=10)

    def check_connection(self):
        """Check database connection and update status indicator"""
        try:
            connection = pymysql.connect(**DATABASE_CONFIG)
            connection.close()
            self.status_indicator.configure(text_color="green")
        except:
            self.status_indicator.configure(text_color="red")
        
        self.connection_check_after_id = self.window.after(5000, self.check_connection)

    def test_connection(self):
        """Test database connection with current configuration"""
        config = {key: entry.get() for key, entry in self.config_entries.items()}
        try:
            connection = pymysql.connect(**config)
            connection.close()
            messagebox.showinfo("Success", "Successfully connected to database!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to database:\n{str(e)}")

    def save_configuration(self):
        """Save the current configuration to config.py"""
        try:
            new_config = {key: entry.get() for key, entry in self.config_entries.items()}
            
            config_str = "# config.py\nDATABASE_CONFIG = {\n"
            for key, value in new_config.items():
                config_str += f"    '{key}': '{value}',\n"
            config_str += "}\n"
            
            with open("config.py", "w") as f:
                f.write(config_str)
            
            messagebox.showinfo("Success", "Configuration saved successfully!")
            
            global DATABASE_CONFIG
            DATABASE_CONFIG.update(new_config)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration:\n{str(e)}")

    def reset_to_default(self):
        """Reset configuration to default values"""
        default_config = {
            'host': '127.0.0.1',
            'user': 'root',
            'password': 'password',
            'database': 'employeedb',
        }
        
        for key, value in default_config.items():
            if key in self.config_entries:
                self.config_entries[key].delete(0, 'end')
                self.config_entries[key].insert(0, value)

    def on_closing(self):
        """Clean up and close the window"""
        if self.connection_check_after_id:
            self.window.after_cancel(self.connection_check_after_id)
        self.window.grab_release()
        self.window.destroy()

class DeveloperSettings:
    def __init__(self, parent):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Developer Settings")
        self.window.geometry("800x600")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        self.parent = parent
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.setup_ui()

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Developer Settings", 
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=(0,20))

        # Employee Limit Section
        limit_section = ctk.CTkFrame(main_frame)
        limit_section.pack(fill="x", padx=20, pady=10)

        limit_title = ctk.CTkLabel(
            limit_section,
            text="Employee Limit Settings",
            font=("Arial", 16, "bold")
        )
        limit_title.pack(pady=(10,20))

        current_limit = EmployeeLimitConfig.get_employee_limit()
        self.current_limit_label = ctk.CTkLabel(
            limit_section,
            text=f"Current Employee Limit: {current_limit}",
            font=("Arial", 14)
        )
        self.current_limit_label.pack(pady=10)

        limit_frame = ctk.CTkFrame(limit_section)
        limit_frame.pack(pady=20)

        limit_label = ctk.CTkLabel(
            limit_frame,
            text="New Employee Limit:",
            font=("Arial", 12)
        )
        limit_label.pack(side="left", padx=5)

        self.limit_entry = ctk.CTkEntry(limit_frame, width=100, justify="center")
        self.limit_entry.pack(side="left", padx=5)
        self.limit_entry.insert(0, str(current_limit))

        # Button Section
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(pady=20)

        # Database Config Button
        db_config_button = ctk.CTkButton(
            button_frame,
            text="Database Configuration",
            command=lambda: DatabaseConfigManager(self.window)
        )
        db_config_button.pack(pady=10)

        # Save Limit Button
        save_button = ctk.CTkButton(
            button_frame,
            text="Save Limit",
            command=self.save_limit
        )
        save_button.pack(pady=10)

        # Delete Data Button
        delete_data_button = ctk.CTkButton(
            button_frame,
            text="Delete Data",
            command=self.delete_data,
            fg_color="red",
            hover_color="darkred"
        )
        delete_data_button.pack(pady=10)

        # Cancel Button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.on_closing
        )
        cancel_button.pack(pady=10)

    def validate_limit(self, limit_str):
        try:
            limit = int(limit_str)
            if limit <= 0:
                raise ValueError("Employee limit must be a positive number")
            if limit > 1000000:
                raise ValueError("Employee limit cannot exceed 1,000,000")
            return limit
        except ValueError as e:
            if "invalid literal for int()" in str(e):
                raise ValueError("Please enter a valid number")
            raise

    def save_limit(self):
        try:
            new_limit_str = self.limit_entry.get().strip()
            if not new_limit_str:
                messagebox.showerror("Error", "Please enter a value")
                return

            new_limit = self.validate_limit(new_limit_str)

            current_limit = EmployeeLimitConfig.get_employee_limit()
            if abs(new_limit - current_limit) > current_limit * 0.5:
                if not messagebox.askyesno("Confirm Change", 
                    f"Are you sure you want to change the employee limit from {current_limit} to {new_limit}?"):
                    return

            config = EmployeeLimitConfig.load_config()
            config["employee_limit"] = new_limit
            EmployeeLimitConfig.save_config(config)

            self.current_limit_label.configure(
                text=f"Current Employee Limit: {new_limit}"
            )
            messagebox.showinfo("Success", f"Employee limit updated to {new_limit}")

        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

    def verify_password(self, user_id, password):
        try:
            connection = pymysql.connect(**DATABASE_CONFIG)
            with connection.cursor() as cursor:
                query = "SELECT password FROM employees WHERE user_id = %s"
                cursor.execute(query, (user_id,))
                result = cursor.fetchone()

                if result:
                    return result[0] == password
                else:
                    messagebox.showerror("Error", "User ID not found in the database.")
                    return False

        except pymysql.Error as e:
            messagebox.showerror("Error", f"Failed to verify password: {str(e)}")
            return False

        finally:
            if connection:
                connection.close()

    def delete_data(self):
        attempts = 2
        user_id = User.get_instance().get_user_id()
        correct_password_count = 0

        for i in range(attempts):
            password = ctk.CTkInputDialog(text="Enter password to delete all data:", title="Password Verification").get_input()

            if password is None:
                return

            if self.verify_password(user_id, password):
                correct_password_count += 1
                if correct_password_count == attempts:
                    self.confirm_and_delete_database()

    def confirm_and_delete_database(self):
        if not messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the entire database? This action cannot be undone."):
            return
        # Run the deletion process in a separate thread
        threading.Thread(target=self._delete_database_thread, daemon=True).start()

    def _delete_database_thread(self):
        connection = None
        try:
            # Connect to the database using pymysql
            connection = pymysql.connect(
                host=DATABASE_CONFIG["host"],
                user=DATABASE_CONFIG["user"],
                password=DATABASE_CONFIG["password"]
            )
            with connection.cursor() as cursor:
                # Drop the database
                cursor.execute(f"DROP DATABASE {DATABASE_CONFIG['database']}")
                print(f"Deleted database: {DATABASE_CONFIG['database']}")

                # Recreate the database
                cursor.execute(f"CREATE DATABASE {DATABASE_CONFIG['database']}")
                print(f"Recreated database: {DATABASE_CONFIG['database']}")

                # Commit the changes
                connection.commit()

            # Show success message (must be done in the main thread)
            self.window.after(0, lambda: messagebox.showinfo("Success", "Database has been deleted and recreated."))

        except pymysql.Error as e:
            # Show error message (must be done in the main thread)
            self.window.after(0, lambda: messagebox.showerror("Error", f"Failed to delete database: {str(e)}"))

        finally:
            if connection:
                connection.close()

    def on_closing(self):
        """Clean up and close the window"""
        self.window.grab_release()
        self.window.destroy()
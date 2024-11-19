#record
import os
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta, time
import pymysql
from PIL import Image
import queue
import threading
import pandas as pd
from login import User
from config import DATABASE_CONFIG

class DatabaseManager:
    def _init_(self):
        pass

    def get_connection(self):
        try:
            connection = pymysql.connect(**DATABASE_CONFIG)
            if connection.open:
                print("Database connection established")
                return connection
            print("Database connection error")
            return None
        except pymysql.Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None
class LoadingScreen(ctk.CTkToplevel):
    def _init_(self, parent):
        super()._init_(parent)
        self.geometry("200x100")
        self.title("Loading...")
        self.configure(fg_color="#2b2b2b")
        self.resizable(False, False)

        # Center the loading screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 200) // 2
        y = (screen_height - 100) // 2
        self.geometry(f"200x100+{x}+{y}")

        self.label = ctk.CTkLabel(self, text="Loading...", font=("Arial", 16))
        self.label.pack(pady=20)

        self.progress = ttk.Progressbar(self, mode='indeterminate')
        self.progress.pack(pady=10, padx=20, fill='x')
        self.progress.start(10)

class RecordViewer(ctk.CTkToplevel):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.db = DatabaseManager()
        self.loading_screen = None  # Initialize loading screen
        self.data_queue = queue.Queue()

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            bg_path = os.path.join(current_dir, "assets", "bg2.png")

            if os.path.exists(bg_path):
                bg_image = Image.open(bg_path)
                self.bg_image = ctk.CTkImage(light_image=bg_image, dark_image=bg_image, size=(1450, 977))
        except Exception as e:
            print(f"Error loading Background image: {e}")

        self.grab_set()
        self.after(100, self.setup_main_window)
        self.after(100, self.setup_ui_components)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.grab_release()
        if self.parent:
            self.parent.deiconify()
        self.destroy()

    def setup_main_window(self):
        self.title("Time Tracker Records")
        self.geometry("1500x1000")
        self.resizable(False, False)

        if hasattr(self, 'bg_image'):
            bg_label = ctk.CTkLabel(self, image=self.bg_image, text="")
            bg_label.place(relwidth=1, relheight=1)
        else:
            self.configure(fg_color="#2b2b2b")

    def setup_ui_components(self):
        self.create_title()
        self.create_record_frame()
        self.create_filter_frame()

        # Back button
        self.back_button = ctk.CTkButton(
            self,
            text="← Back to Main",
            command=self.on_closing,
            width=130,
            height=40,
            font=("Arial", 12),
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        self.back_button.place(relx=0.515, rely=0.88, anchor="w")

        # Delete button
        self.delete_button = ctk.CTkButton(
            self,
            text="🗑 Delete Record",
            command=self.delete_record,
            fg_color="#ff0000",  # Red color for delete button
            hover_color="#cc0000",
            width=120,height=40
        )
        self.delete_button.place(relx=0.6, rely=0.8, anchor="e")

        # Add user details in top right
        user = User.get_instance()
        user_frame = ctk.CTkFrame(self, fg_color="#003057",bg_color="#003057")
        user_frame.place(relx=0.98, rely=0.053, anchor="e")

        user_name = ctk.CTkLabel(
            user_frame,
            text=f"Name: {user.get_username()}",
            font=("Arial", 14, "bold"),
            text_color="#0075C9"
        )
        user_name.pack(anchor="e")

        designation = ctk.CTkLabel(
            user_frame,
            text=f"designation: {user.get_designation()}",
            font=("Arial", 14, "bold"),
            text_color="#0075C9"
        )
        designation.pack(anchor="e")

        software_authority = ctk.CTkLabel(
            user_frame,
            text=f"software_authority: {user.get_software_authority()}",
            font=("Arial", 14, "bold"),
            text_color="#0075C9"
        )
        software_authority.pack(anchor="e")

        # Load initial data
        self.load_records()

        # Load SO Numbers into the dropdown
        self.load_so_numbers()

    def create_title(self):
        title_label = ctk.CTkLabel(
            self,
            text="My Work Records",
            font=("Arial", 24, "bold"),
            text_color="black",bg_color="white"
        )
        title_label.place(relx=0.55, rely=0.098, anchor="center")

    def create_record_frame(self):
        # Main frame for the record view
        self.record_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.record_frame.place(relx=0.5, rely=0.51, anchor="center", relwidth=0.95, relheight=0.5)

        # Define columns for the Treeview
        self.tree = ttk.Treeview(
            self.record_frame,
            columns=("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"),
            show="headings",
            style="Custom.Treeview"
        )

        # Configure column headings
        columns = [
            ("Log ID", 100),      # Column 0: log_id
            ("User Name", 150),   # Column 1: user_name
            ("User ID", 100),     # Column 2: user_id
            ("Date", 100),        # Column 3: date
            ("SO Number", 100),   # Column 4: so_number
            ("Start Time", 100),  # Column 5: start_time
            ("End Time", 100),    # Column 6: end_time
            ("Work Time", 80),    # Column 7: work_time
            ("Work Type", 150),   # Column 8: work_type
            ("Details of Work", 200),  # Column 9: details_of_work
            ("Remarks", 200),     # Column 10: remarks
            ("Work Time Type", 100),  # Column 11: work_time_type
            ("Edit", 50),         # Column 12: Edit button
            ("Delete", 50)        # Column 13: Delete button
        ]

        # Set column headings and widths
        for idx, (col, width) in enumerate(columns):
            self.tree.heading(str(idx), text=col, anchor="w")
            self.tree.column(str(idx), width=width, anchor="w")

        # Add scrollbars
        scrollbar_y = ttk.Scrollbar(self.record_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(self.record_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # Pack everything
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        # Bind double-click event to edit record
        self.tree.bind("<Double-1>", self.edit_record)

        # Bind delete button to delete_record method
        self.tree.bind("<Delete>", self.delete_record)

    def create_filter_frame(self):
        filter_frame = ctk.CTkFrame(self, fg_color="#A6A8AB")
        filter_frame.place(relx=0.5, rely=0.22, anchor="center")

        # Date range filter
        date_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        date_frame.pack(side="left", padx=20)

        ctk.CTkLabel(date_frame, text="Date Range:").pack(side="left", padx=5)
        self.date_var = ctk.CTkOptionMenu(
            date_frame,
            values=["All Time", "Today", "This Week", "This Month", "Last 3 Months"],
            command=self.apply_filters
        )
        self.date_var.pack(side="left", padx=5)

        # Work type filter
        type_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        type_frame.pack(side="left", padx=20)

        ctk.CTkLabel(type_frame, text="Work Type:").pack(side="left", padx=5)
        self.type_var = ctk.CTkOptionMenu(
            type_frame,
            values=["All Types", "Standard",  "Non-Standard"],
            command=self.apply_filters
        )
        self.type_var.pack(side="left", padx=5)

        # Work Time type filter
        type_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        type_frame.pack(side="left", padx=20)

        ctk.CTkLabel(type_frame, text="Work Time Type:").pack(side="left", padx=5)
        self.time_category_var = ctk.CTkOptionMenu(
            type_frame,
            values=["All Types", "Standard Time",  "Over Time"],
            command=self.apply_filters
        )
        self.time_category_var.pack(side="left", padx=5)

        # SO Number filter
        so_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        so_frame.pack(side="left", padx=20)

        ctk.CTkLabel(so_frame, text="SO Number:").pack(side="left", padx=5)
        self.so_number_var = ctk.CTkOptionMenu(
            so_frame,
            values=["All SO Numbers"],  # Initially, only "All SO Numbers" is shown
            command=self.apply_filters
        )
        self.so_number_var.pack(side="left", padx=5)

        # Reset filters button
        self.reset_button = ctk.CTkButton(
            filter_frame,
            text="Reset",
            command=self.reset_filters,
            fg_color="#8B8000",
            hover_color="#14375e"
        )
        self.reset_button.pack(side="left", padx=20)

        # Download Excel button
        self.download_button = ctk.CTkButton(
            filter_frame,
            text="Download Excel",
            command=self.download_excel,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.download_button.pack(side="left", padx=20)

    def show_loading_screen(self):
        # Create a loading screen if it doesn't exist
        if not self.loading_screen:
            self.loading_screen = LoadingScreen(self)
        self.loading_screen.deiconify()  # Show the loading screen

    def hide_loading_screen(self):
        # Hide the loading screen if it exists
        if self.loading_screen:
            self.loading_screen.withdraw()  # Hide the loading screen

    def run(self):
        self.mainloop()  # Start the main loop

    def load_so_numbers(self):
        def fetch_so_numbers():
            conn = self.db.get_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return

            try:
                with conn.cursor() as cursor:
                    # Fetch distinct SO Numbers from the database
                    cursor.execute("SELECT DISTINCT so_number FROM work_logs ORDER BY so_number")
                    so_numbers = [row[0] for row in cursor.fetchall()]

                    # Update the SO Number dropdown
                    self.after(0, lambda: self.update_so_number_dropdown(so_numbers))

            except Exception as e:
                messagebox.showerror("Error", f"Error fetching SO Numbers: {str(e)}")
            finally:
                conn.close()

        # Run the fetch in a separate thread
        thread = threading.Thread(target=fetch_so_numbers)
        thread.daemon = True
        thread.start()

    def update_so_number_dropdown(self, so_numbers):
        # Update the SO Number dropdown with the fetched SO Numbers
        self.so_number_var.configure(values=["All SO Numbers"] + so_numbers)

    def load_records(self):
        def fetch_data():
            conn = self.db.get_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return

            try:
                with conn.cursor() as cursor:
                    # Get the current user's ID and designation from the login system
                    from login import User
                    current_user = User.get_instance()
                    current_user_id = current_user.get_user_id()
                    current_user_designation = current_user.get_designation()

                    # Base query with JOIN to fetch user name, user ID, and log_id
                    query = """
                    SELECT w.log_id, e.name, e.user_id, w.log_date, w.so_number, w.start_time, w.end_time, w.work_hours,
                    w.work_category, w.details_of_work, w.remarks, w.time_category
                    FROM work_logs w
                    JOIN employees e ON w.user_id = e.user_id
                    """

                    # Parameters for the query
                    params = []

                    # If the user is not a Manager or Developer, filter by user_id
                    if current_user_designation.lower() not in ["manager", "developer"]:
                        query += " WHERE w.user_id = %s"
                        params.append(current_user_id)

                    query += " ORDER BY w.log_date DESC"

                    # Execute the query with parameters
                    cursor.execute(query, tuple(params))
                    records = cursor.fetchall()
                    self.data_queue.put(records)

            except Exception as e:
                messagebox.showerror("Error", f"Error fetching records: {str(e)}")
            finally:
                conn.close()
                self.after(0, self.hide_loading_screen)

        self.show_loading_screen()
        thread = threading.Thread(target=fetch_data)
        thread.daemon = True
        thread.start()
        self.after(100, self.process_data)

    def process_data(self):
        try:
            records = self.data_queue.get_nowait()
            self.update_treeview(records)
        except queue.Empty:
            self.after(100, self.process_data)
        except Exception as e:
            messagebox.showerror("Error", f"Error processing data: {str(e)}")
            self.hide_loading_screen()

    def update_treeview(self, records):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        for record in records:
            # Convert timedelta to a readable time format
            start_time = str(record[5]) if isinstance(record[5], timedelta) else (record[5].strftime("%H:%M") if record[5] else "")
            end_time = str(record[6]) if isinstance(record[6], timedelta) else (record[6].strftime("%H:%M") if record[6] else "")

            formatted_record = [
                record[0],  # Log ID
                record[1],  # User Name
                record[2],  # User ID
                record[3].strftime("%Y-%m-%d"),  # Date
                record[4],  # SO Number
                start_time,  # Start Time
                end_time,  # End Time
                str(record[7]) if isinstance(record[7], timedelta) else f"{float(record[7]):.2f}",  # Work Time
                record[8],  # Work Type
                record[9],  # Details
                record[10],  # Remarks
                record[11],  # Time Category
                "Edit",  # Edit button
                "Delete"  # Delete button
            ]
            # Store the log_id in the Treeview item (hidden from the user)
            self.tree.insert("", "end", values=formatted_record, iid=record[0])  # Use log_id as the item ID

    def edit_record(self, event):
        # Get the selected record
        selected_item = self.tree.selection()[0]
        log_id = selected_item  # The item ID is the log_id
        record = self.tree.item(selected_item, "values")

        # Open a new window to edit the record
        self.edit_window = ctk.CTkToplevel(self)
        self.edit_window.title("Edit Record")
        self.edit_window.geometry("400x300")

        # Create entry fields for editing
        ctk.CTkLabel(self.edit_window, text="Date:").grid(row=0, column=0, padx=10, pady=10)
        self.date_entry = ctk.CTkEntry(self.edit_window)
        self.date_entry.grid(row=0, column=1, padx=10, pady=10)
        self.date_entry.insert(0, record[3])

        ctk.CTkLabel(self.edit_window, text="SO Number:").grid(row=1, column=0, padx=10, pady=10)
        self.so_number_entry = ctk.CTkEntry(self.edit_window)
        self.so_number_entry.grid(row=1, column=1, padx=10, pady=10)
        self.so_number_entry.insert(0, record[4])

        ctk.CTkLabel(self.edit_window, text="Start Time:").grid(row=2, column=0, padx=10, pady=10)
        self.start_time_entry = ctk.CTkEntry(self.edit_window)
        self.start_time_entry.grid(row=2, column=1, padx=10, pady=10)
        self.start_time_entry.insert(0, record[5])

        ctk.CTkLabel(self.edit_window, text="End Time:").grid(row=3, column=0, padx=10, pady=10)
        self.end_time_entry = ctk.CTkEntry(self.edit_window)
        self.end_time_entry.grid(row=3, column=1, padx=10, pady=10)
        self.end_time_entry.insert(0, record[6])

        ctk.CTkLabel(self.edit_window, text="Work Type:").grid(row=4, column=0, padx=10, pady=10)
        self.work_type_entry = ctk.CTkEntry(self.edit_window)
        self.work_type_entry.grid(row=4, column=1, padx=10, pady=10)
        self.work_type_entry.insert(0, record[8])

        ctk.CTkLabel(self.edit_window, text="Details of Work:").grid(row=5, column=0, padx=10, pady=10)
        self.details_entry = ctk.CTkEntry(self.edit_window)
        self.details_entry.grid(row=5, column=1, padx=10, pady=10)
        self.details_entry.insert(0, record[9])

        ctk.CTkLabel(self.edit_window, text="Remarks:").grid(row=6, column=0, padx=10, pady=10)
        self.remarks_entry = ctk.CTkEntry(self.edit_window)
        self.remarks_entry.grid(row=6, column=1, padx=10, pady=10)
        self.remarks_entry.insert(0, record[10])

        ctk.CTkLabel(self.edit_window, text="Work Time Type:").grid(row=7, column=0, padx=10, pady=10)
        self.time_category_entry = ctk.CTkEntry(self.edit_window)
        self.time_category_entry.grid(row=7, column=1, padx=10, pady=10)
        self.time_category_entry.insert(0, record[11])

        # Save button
        save_button = ctk.CTkButton(
            self.edit_window,
            text="Save",
            command=lambda: self.save_record(log_id),
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        save_button.grid(row=8, column=0, columnspan=2, pady=10)

    def save_record(self, log_id):
        # Get the updated values from the entry fields
        updated_values = [
            self.date_entry.get(),
            self.so_number_entry.get(),
            self.start_time_entry.get(),
            self.end_time_entry.get(),
            self.work_type_entry.get(),
            self.details_entry.get(),
            self.remarks_entry.get(),
            self.time_category_entry.get()
        ]

        # Update the record in the database
        conn = self.db.get_connection()
        if not conn:
            messagebox.showerror("Error", "Could not connect to database")
            return

        try:
            with conn.cursor() as cursor:
                query = """
                UPDATE work_logs
                SET log_date = %s, so_number = %s, start_time = %s, end_time = %s,
                work_category = %s, details_of_work = %s, remarks = %s, time_category = %s
                WHERE log_id = %s
                """
                cursor.execute(query, (*updated_values, log_id))
                conn.commit()
                messagebox.showinfo("Success", "Record updated successfully")
                self.edit_window.destroy()
                self.load_records()
        except Exception as e:
            messagebox.showerror("Error", f"Error updating record: {str(e)}")
        finally:
            conn.close()

    def delete_record(self, event=None):
        # Get the selected record
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a record to delete.")
            return

        selected_item = selected_items[0]
        log_id = selected_item  # The item ID is the log_id

        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?")
        if not confirm:
            return

        # Delete the record from the database
        conn = self.db.get_connection()
        if not conn:
            messagebox.showerror("Error", "Could not connect to database")
            return

        try:
            with conn.cursor() as cursor:
                query = "DELETE FROM work_logs WHERE log_id = %s"
                cursor.execute(query, (log_id,))
                conn.commit()
                messagebox.showinfo("Success", "Record deleted successfully")
                self.load_records()
        except Exception as e:
            messagebox.showerror("Error", f"Error deleting record: {str(e)}")
        finally:
            conn.close()

    def apply_filters(self, _=None):
        def fetch_data():
            conn = self.db.get_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return

            try:
                with conn.cursor() as cursor:
                    # Get the current user's ID and designation from the login system
                    from login import User
                    current_user = User.get_instance()
                    current_user_id = current_user.get_user_id()
                    current_user_designation = current_user.get_designation()

                    # Base query with JOIN to fetch user name, user ID, and log_id
                    query = """
                    SELECT w.log_id, e.name, e.user_id, w.log_date, w.so_number, w.start_time, w.end_time, w.work_hours,
                    w.work_category, w.details_of_work, w.remarks, w.time_category
                    FROM work_logs w
                    JOIN employees e ON w.user_id = e.user_id
                    """

                    # Parameters for the query
                    params = []

                    # If the user is not a Manager or Developer, filter by user_id
                    if current_user_designation not in ["Manager", "Developer"]:
                        query += " WHERE w.user_id = %s"
                        params.append(current_user_id)

                    # Add date range filter
                    date_range = self.date_var.get()
                    if date_range == "Today":
                        today = datetime.now().date()
                        query += " AND w.log_date = %s" if params else " WHERE w.log_date = %s"
                        params.append(today)
                    elif date_range == "This Week":
                        start_of_week = datetime.now().date() - timedelta(days=datetime.now().weekday())
                        end_of_week = start_of_week + timedelta(days=6)
                        query += " AND w.log_date BETWEEN %s AND %s" if params else " WHERE w.log_date BETWEEN %s AND %s"
                        params.extend([start_of_week, end_of_week])
                    elif date_range == "This Month":
                        start_of_month = datetime.now().date().replace(day=1)
                        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                        query += " AND w.log_date BETWEEN %s AND %s" if params else " WHERE w.log_date BETWEEN %s AND %s"
                        params.extend([start_of_month, end_of_month])
                    elif date_range == "Last 3 Months":
                        start_of_3_months = datetime.now().date() - timedelta(days=90)
                        query += " AND w.log_date >= %s" if params else " WHERE w.log_date >= %s"
                        params.append(start_of_3_months)

                    # Add work type filter
                    work_type = self.type_var.get()
                    if work_type != "All Types":
                        query += " AND w.work_category = %s" if params else " WHERE w.work_category = %s"
                        params.append(work_type)

                    # Add Work Time Type filter
                    time_category = self.time_category_var.get()
                    if time_category != "All Types":
                        query += " AND w.time_category = %s" if params else " WHERE w.time_category = %s"
                        params.append(time_category)

                    # Add SO Number filter
                    so_number = self.so_number_var.get()
                    if so_number != "All SO Numbers":
                        query += " AND w.so_number = %s" if params else " WHERE w.so_number = %s"
                        params.append(so_number)

                    query += " ORDER BY w.log_date DESC"

                    # Execute the query with parameters
                    cursor.execute(query, tuple(params))
                    records = cursor.fetchall()
                    self.data_queue.put(records)

            except Exception as e:
                messagebox.showerror("Error", f"Error fetching records: {str(e)}")
            finally:
                conn.close()
                self.after(0, self.hide_loading_screen)

        self.show_loading_screen()
        thread = threading.Thread(target=fetch_data)
        thread.daemon = True
        thread.start()
        self.after(100, self.process_data)

    def reset_filters(self):
        self.date_var.set("All Time")
        self.type_var.set("All Types")
        self.time_category_var.set("All Types")
        self.so_number_var.set("All SO Numbers")  # Reset SO Number filter
        self.load_records()

    def download_excel(self):
        # Fetch all records from the database
        def fetch_all_records():
            conn = self.db.get_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return

            try:
                with conn.cursor() as cursor:
                    # Get the current user's ID and designation from the login system
                    from login import User
                    current_user = User.get_instance()
                    current_user_id = current_user.get_user_id()
                    current_user_designation = current_user.get_designation()

                    # Base query with JOIN to fetch user name, user ID, and log_id
                    query = """
                    SELECT w.log_id, e.name, e.user_id, w.log_date, w.so_number, w.start_time, w.end_time, w.work_hours,
                    w.work_category, w.details_of_work, w.remarks, w.time_category
                    FROM work_logs w
                    JOIN employees e ON w.user_id = e.user_id
                    """

                    # Parameters for the query
                    params = []

                    # If the user is not a Manager or Developer, filter by user_id
                    if current_user_designation.lower() not in ["manager", "developer"]:
                        query += " WHERE w.user_id = %s"
                        params.append(current_user_id)

                    query += " ORDER BY w.log_date DESC"

                    # Execute the query with parameters
                    cursor.execute(query, tuple(params))
                    records = cursor.fetchall()
                    return records

            except Exception as e:
                messagebox.showerror("Error", f"Error fetching records: {str(e)}")
                return []
            finally:
                conn.close()

        # Fetch records
        records = fetch_all_records()
        if not records:
            messagebox.showinfo("No Data", "No records found to export.")
            return

        # Convert records to a DataFrame
        columns = [
            "Log ID", "User Name", "User ID", "Date", "SO Number", "Start Time", "End Time",
            "Work Time", "Work Type", "Details of Work", "Remarks", "Work Time Type"
        ]
        df = pd.DataFrame(records, columns=columns)

        # Format the "Date" column as a string in the desired format
        df["Date"] = df["Date"].apply(lambda x: x.strftime("%Y-%m-%d") if x else "")

        # Format the "Start Time" and "End Time" columns as strings
        def format_time(value):
            if isinstance(value, timedelta):
                # Convert timedelta to HH:MM:SS format
                total_seconds = int(value.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                return f"{hours:02}:{minutes:02}:{seconds:02}"
            elif isinstance(value, time):  # Use the imported time class
                # Format time objects as HH:MM
                return value.strftime("%H:%M")
            else:
                return ""

        df["Start Time"] = df["Start Time"].apply(format_time)
        df["End Time"] = df["End Time"].apply(format_time)

        # Format the "Work Time" column as a string
        df["Work Time"] = df["Work Time"].apply(lambda x: str(x) if x else "")

        # Ask the user where to save the file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", ".xlsx"), ("All files", ".*")],
            title="Save file as"
        )

        if not file_path:  # If the user cancels the dialog
            return
and                                                                                                     
        # Save DataFrame to Excel
        try:
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Success", f"Records exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file: {str(e)}")

def main():
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = RecordViewer()
    app.mainloop()


if __name__ == "__main__":
    main()

# import os
# import customtkinter as ctk
# import tkinter as tk
# from tkinter import ttk, messagebox, filedialog
# from datetime import datetime, timedelta, time
# import pymysql
# from PIL import Image
# import queue
# import threading
# import pandas as pd
# from login import User
# from config import DATABASE_CONFIG


# class DatabaseManager:
#     def __init__(self):
#         pass

#     def get_connection(self):
#         try:
#             connection = pymysql.connect(**DATABASE_CONFIG)
#             if connection.open:
#                 print("Database connection established")
#                 return connection
#             print("Database connection error")
#             return None
#         except pymysql.Error as e:
#             print(f"Error connecting to MySQL: {e}")
#             return None


# class LoadingScreen(ctk.CTkToplevel):
#     def __init__(self, parent):
#         super().__init__(parent)
#         self.geometry("200x100")
#         self.title("Loading...")
#         self.configure(fg_color="#2b2b2b")
#         self.resizable(False, False)

#         # Center the loading screen
#         screen_width = self.winfo_screenwidth()
#         screen_height = self.winfo_screenheight()
#         x = (screen_width - 200) // 2
#         y = (screen_height - 100) // 2
#         self.geometry(f"200x100+{x}+{y}")

#         self.label = ctk.CTkLabel(self, text="Loading...", font=("Arial", 16))
#         self.label.pack(pady=20)

#         self.progress = ttk.Progressbar(self, mode='indeterminate')
#         self.progress.pack(pady=10, padx=20, fill='x')
#         self.progress.start(10)


# class RecordViewer(ctk.CTkToplevel):
#     def __init__(self, parent=None):
#         super().__init__()
#         self.parent = parent
#         self.db = DatabaseManager()
#         self.loading_screen = None  # Initialize loading screen
#         self.data_queue = queue.Queue()

#         try:
#             current_dir = os.path.dirname(os.path.abspath(__file__))
#             bg_path = os.path.join(current_dir, "assets", "bg2.png")

#             if os.path.exists(bg_path):
#                 bg_image = Image.open(bg_path)
#                 self.bg_image = ctk.CTkImage(light_image=bg_image, dark_image=bg_image, size=(1600, 900))
#         except Exception as e:
#             print(f"Error loading Background image: {e}")

#         self.grab_set()
#         self.after(100, self.setup_main_window)
#         self.after(100, self.setup_ui_components)
#         self.protocol("WM_DELETE_WINDOW", self.on_closing)

#     def on_closing(self):
#         self.grab_release()
#         if self.parent:
#             self.parent.deiconify()
#         self.destroy()

#     def setup_main_window(self):
#         self.title("Time Tracker Records")
#         self.geometry("1400x950")
#         self.resizable(True, True)

#         if hasattr(self, 'bg_image'):
#             bg_label = ctk.CTkLabel(self, image=self.bg_image, text="")
#             bg_label.place(relwidth=1, relheight=1)
#         else:
#             self.configure(fg_color="#2b2b2b")

#     def setup_ui_components(self):
#         self.create_title()
#         self.create_record_frame()
#         self.create_filter_frame()

#         # Back button
#         self.back_button = ctk.CTkButton(
#             self,
#             text="← Back to Main",
#             command=self.on_closing,
#             width=120,
#             height=30,
#             font=("Arial", 12),
#             fg_color="#1f538d",
#             hover_color="#14375e"
#         )
#         self.back_button.place(relx=0.05, rely=0.05, anchor="w")

#         # Delete button
#         self.delete_button = ctk.CTkButton(
#             self,
#             text="Delete Record",
#             command=self.delete_record,
#             fg_color="#ff0000",  # Red color for delete button
#             hover_color="#cc0000"
#         )
#         self.delete_button.place(relx=0.7, rely=0.05, anchor="e")

#         # Add user details in top right
#         user = User.get_instance()
#         user_frame = ctk.CTkFrame(self, fg_color="transparent")
#         user_frame.place(relx=0.95, rely=0.05, anchor="e")

#         user_name = ctk.CTkLabel(
#             user_frame,
#             text=f"Name: {user.get_username()}",
#             font=("Arial", 14, "bold"),
#             text_color="white"
#         )
#         user_name.pack(anchor="e")

#         designation = ctk.CTkLabel(
#             user_frame,
#             text=f"designation: {user.get_designation()}",
#             font=("Arial", 14, "bold"),
#             text_color="white"
#         )
#         designation.pack(anchor="e")

#         software_authority = ctk.CTkLabel(
#             user_frame,
#             text=f"software_authority: {user.get_software_authority()}",
#             font=("Arial", 14, "bold"),
#             text_color="white"
#         )
#         software_authority.pack(anchor="e")

#         # Load initial data
#         self.load_records()

#         # Load SO Numbers into the dropdown
#         self.load_so_numbers()

#     def create_title(self):
#         title_label = ctk.CTkLabel(
#             self,
#             text="My Work Records",
#             font=("Arial", 24, "bold"),
#             text_color="white"
#         )
#         title_label.place(relx=0.5, rely=0.05, anchor="center")

#     def create_record_frame(self):
#         # Main frame for the record view
#         self.record_frame = ctk.CTkFrame(self, fg_color="transparent")
#         self.record_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.7)

#         # Define columns for the Treeview
#         self.tree = ttk.Treeview(
#             self.record_frame,
#             columns=("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"),
#             show="headings",
#             style="Custom.Treeview"
#         )

#         # Configure column headings
#         columns = [
#             ("Log ID", 100),      # Column 0: log_id
#             ("User Name", 150),   # Column 1: user_name
#             ("User ID", 100),     # Column 2: user_id
#             ("Date", 100),        # Column 3: date
#             ("SO Number", 100),   # Column 4: so_number
#             ("Start Time", 100),  # Column 5: start_time
#             ("End Time", 100),    # Column 6: end_time
#             ("Work Time", 80),    # Column 7: work_time
#             ("Work Type", 150),   # Column 8: work_type
#             ("Details of Work", 200),  # Column 9: details_of_work
#             ("Remarks", 200),     # Column 10: remarks
#             ("Work Time Type", 100),  # Column 11: work_time_type
#             ("Edit", 50),         # Column 12: Edit button
#             ("Delete", 50)        # Column 13: Delete button
#         ]

#         # Set column headings and widths
#         for idx, (col, width) in enumerate(columns):
#             self.tree.heading(str(idx), text=col, anchor="w")
#             self.tree.column(str(idx), width=width, anchor="w")

#         # Add scrollbars
#         scrollbar_y = ttk.Scrollbar(self.record_frame, orient="vertical", command=self.tree.yview)
#         scrollbar_x = ttk.Scrollbar(self.record_frame, orient="horizontal", command=self.tree.xview)
#         self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

#         # Pack everything
#         scrollbar_y.pack(side="right", fill="y")
#         scrollbar_x.pack(side="bottom", fill="x")
#         self.tree.pack(side="left", fill="both", expand=True)

#         # Bind double-click event to edit record
#         self.tree.bind("<Double-1>", self.edit_record)

#         # Bind delete button to delete_record method
#         self.tree.bind("<Delete>", self.delete_record)

#     def create_filter_frame(self):
#         filter_frame = ctk.CTkFrame(self, fg_color="transparent")
#         filter_frame.place(relx=0.5, rely=0.12, anchor="center")

#         # Date range filter
#         date_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
#         date_frame.pack(side="left", padx=20)

#         ctk.CTkLabel(date_frame, text="Date Range:").pack(side="left", padx=5)
#         self.date_var = ctk.CTkOptionMenu(
#             date_frame,
#             values=["All Time", "Today", "This Week", "This Month", "Last 3 Months"],
#             command=self.apply_filters
#         )
#         self.date_var.pack(side="left", padx=5)

#         # Work type filter
#         type_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
#         type_frame.pack(side="left", padx=20)

#         ctk.CTkLabel(type_frame, text="Work Type:").pack(side="left", padx=5)
#         self.type_var = ctk.CTkOptionMenu(
#             type_frame,
#             values=["All Types", "Standard",  "Non-Standard"],
#             command=self.apply_filters
#         )
#         self.type_var.pack(side="left", padx=5)

#         # Work Time type filter
#         type_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
#         type_frame.pack(side="left", padx=20)

#         ctk.CTkLabel(type_frame, text="Work Time Type:").pack(side="left", padx=5)
#         self.time_category_var = ctk.CTkOptionMenu(
#             type_frame,
#             values=["All Types", "Standard Time",  "Over Time"],
#             command=self.apply_filters
#         )
#         self.time_category_var.pack(side="left", padx=5)

#         # SO Number filter
#         so_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
#         so_frame.pack(side="left", padx=20)

#         ctk.CTkLabel(so_frame, text="SO Number:").pack(side="left", padx=5)
#         self.so_number_var = ctk.CTkOptionMenu(
#             so_frame,
#             values=["All SO Numbers"],  # Initially, only "All SO Numbers" is shown
#             command=self.apply_filters
#         )
#         self.so_number_var.pack(side="left", padx=5)

#         # Reset filters button
#         self.reset_button = ctk.CTkButton(
#             filter_frame,
#             text="Reset Filters",
#             command=self.reset_filters,
#             fg_color="#1f538d",
#             hover_color="#14375e"
#         )
#         self.reset_button.pack(side="left", padx=20)

#         # Download Excel button
#         self.download_button = ctk.CTkButton(
#             filter_frame,
#             text="Download Excel",
#             command=self.download_excel,
#             fg_color="#1f538d",
#             hover_color="#14375e"
#         )
#         self.download_button.pack(side="left", padx=20)

#     def show_loading_screen(self):
#         # Create a loading screen if it doesn't exist
#         if not self.loading_screen:
#             self.loading_screen = LoadingScreen(self)
#         self.loading_screen.deiconify()  # Show the loading screen

#     def hide_loading_screen(self):
#         # Hide the loading screen if it exists
#         if self.loading_screen:
#             self.loading_screen.withdraw()  # Hide the loading screen

#     def run(self):
#         self.mainloop()  # Start the main loop

#     def load_so_numbers(self):
#         def fetch_so_numbers():
#             conn = self.db.get_connection()
#             if not conn:
#                 messagebox.showerror("Error", "Could not connect to database")
#                 return

#             try:
#                 with conn.cursor() as cursor:
#                     # Fetch distinct SO Numbers from the database
#                     cursor.execute("SELECT DISTINCT so_number FROM work_logs ORDER BY so_number")
#                     so_numbers = [row[0] for row in cursor.fetchall()]
#                     #print("Fetched SO Numbers:", so_numbers)  # Debugging print statement

#                     # Update the SO Number dropdown on the main thread
#                     self.after(0, lambda: self.update_so_number_dropdown(so_numbers))

#             except Exception as e:
#                 messagebox.showerror("Error", f"Error fetching SO Numbers: {str(e)}")
#             finally:
#                 conn.close()

#         # Run the fetch in a separate thread
#         thread = threading.Thread(target=fetch_so_numbers)
#         thread.daemon = True
#         thread.start()

#     def update_so_number_dropdown(self, so_numbers):
#         #print("Updating SO Number dropdown with:", so_numbers)  # Debugging print statement
#         # Update the SO Number dropdown with the fetched SO Numbers
#         self.so_number_var.configure(values=["All SO Numbers"] + so_numbers)

#     def load_records(self):
#         def fetch_data():
#             conn = self.db.get_connection()
#             if not conn:
#                 messagebox.showerror("Error", "Could not connect to database")
#                 return

#             try:
#                 with conn.cursor() as cursor:
#                     # Get the current user's ID and designation from the login system
#                     from login import User
#                     current_user = User.get_instance()
#                     current_user_id = current_user.get_user_id()
#                     current_user_designation = current_user.get_designation()

#                     # Base query with JOIN to fetch user name, user ID, and log_id
#                     query = """
#                     SELECT w.log_id, e.name, e.user_id, w.log_date, w.so_number, w.start_time, w.end_time, w.work_hours,
#                     w.work_category, w.details_of_work, w.remarks, w.time_category
#                     FROM work_logs w
#                     JOIN employees e ON w.user_id = e.user_id
#                     """

#                     # Parameters for the query
#                     params = []

#                     # If the user is not a Manager or Developer, filter by user_id
#                     if current_user_designation.lower() not in ["manager", "developer"]:
#                         query += " WHERE w.user_id = %s"
#                         params.append(current_user_id)

#                     query += " ORDER BY w.log_date DESC"

#                     # Execute the query with parameters
#                     cursor.execute(query, tuple(params))
#                     records = cursor.fetchall()
#                     self.data_queue.put(records)

#             except Exception as e:
#                 messagebox.showerror("Error", f"Error fetching records: {str(e)}")
#             finally:
#                 conn.close()
#                 self.after(0, self.hide_loading_screen)

#         self.show_loading_screen()
#         thread = threading.Thread(target=fetch_data)
#         thread.daemon = True
#         thread.start()
#         self.after(100, self.process_data)

#     def process_data(self):
#         try:
#             records = self.data_queue.get_nowait()
#             self.update_treeview(records)
#         except queue.Empty:
#             self.after(100, self.process_data)
#         except Exception as e:
#             messagebox.showerror("Error", f"Error processing data: {str(e)}")
#             self.hide_loading_screen()

#     def update_treeview(self, records):
#         # Clear existing items
#         for item in self.tree.get_children():
#             self.tree.delete(item)

#         for record in records:
#             # Convert timedelta to a readable time format
#             start_time = str(record[5]) if isinstance(record[5], timedelta) else (record[5].strftime("%H:%M") if record[5] else "")
#             end_time = str(record[6]) if isinstance(record[6], timedelta) else (record[6].strftime("%H:%M") if record[6] else "")

#             formatted_record = [
#                 record[0],  # Log ID
#                 record[1],  # User Name
#                 record[2],  # User ID
#                 record[3].strftime("%Y-%m-%d"),  # Date
#                 record[4],  # SO Number
#                 start_time,  # Start Time
#                 end_time,  # End Time
#                 str(record[7]) if isinstance(record[7], timedelta) else f"{float(record[7]):.2f}",  # Work Time
#                 record[8],  # Work Type
#                 record[9],  # Details
#                 record[10],  # Remarks
#                 record[11],  # Time Category
#                 "Edit",  # Edit button
#                 "Delete"  # Delete button
#             ]
#             # Store the log_id in the Treeview item (hidden from the user)
#             self.tree.insert("", "end", values=formatted_record, iid=record[0])  # Use log_id as the item ID

#     def edit_record(self, event):
#         # Get the selected record
#         selected_item = self.tree.selection()[0]
#         log_id = selected_item  # The item ID is the log_id
#         record = self.tree.item(selected_item, "values")

#         # Open a new window to edit the record
#         self.edit_window = ctk.CTkToplevel(self)
#         self.edit_window.title("Edit Record")
#         self.edit_window.geometry("400x300")

#         # Create entry fields for editing
#         ctk.CTkLabel(self.edit_window, text="Date:").grid(row=0, column=0, padx=10, pady=10)
#         self.date_entry = ctk.CTkEntry(self.edit_window)
#         self.date_entry.grid(row=0, column=1, padx=10, pady=10)
#         self.date_entry.insert(0, record[3])

#         ctk.CTkLabel(self.edit_window, text="SO Number:").grid(row=1, column=0, padx=10, pady=10)
#         self.so_number_entry = ctk.CTkEntry(self.edit_window)
#         self.so_number_entry.grid(row=1, column=1, padx=10, pady=10)
#         self.so_number_entry.insert(0, record[4])

#         ctk.CTkLabel(self.edit_window, text="Start Time:").grid(row=2, column=0, padx=10, pady=10)
#         self.start_time_entry = ctk.CTkEntry(self.edit_window)
#         self.start_time_entry.grid(row=2, column=1, padx=10, pady=10)
#         self.start_time_entry.insert(0, record[5])

#         ctk.CTkLabel(self.edit_window, text="End Time:").grid(row=3, column=0, padx=10, pady=10)
#         self.end_time_entry = ctk.CTkEntry(self.edit_window)
#         self.end_time_entry.grid(row=3, column=1, padx=10, pady=10)
#         self.end_time_entry.insert(0, record[6])

#         ctk.CTkLabel(self.edit_window, text="Work Type:").grid(row=4, column=0, padx=10, pady=10)
#         self.work_type_entry = ctk.CTkEntry(self.edit_window)
#         self.work_type_entry.grid(row=4, column=1, padx=10, pady=10)
#         self.work_type_entry.insert(0, record[8])

#         ctk.CTkLabel(self.edit_window, text="Details of Work:").grid(row=5, column=0, padx=10, pady=10)
#         self.details_entry = ctk.CTkEntry(self.edit_window)
#         self.details_entry.grid(row=5, column=1, padx=10, pady=10)
#         self.details_entry.insert(0, record[9])

#         ctk.CTkLabel(self.edit_window, text="Remarks:").grid(row=6, column=0, padx=10, pady=10)
#         self.remarks_entry = ctk.CTkEntry(self.edit_window)
#         self.remarks_entry.grid(row=6, column=1, padx=10, pady=10)
#         self.remarks_entry.insert(0, record[10])

#         ctk.CTkLabel(self.edit_window, text="Work Time Type:").grid(row=7, column=0, padx=10, pady=10)
#         self.time_category_entry = ctk.CTkEntry(self.edit_window)
#         self.time_category_entry.grid(row=7, column=1, padx=10, pady=10)
#         self.time_category_entry.insert(0, record[11])

#         # Save button
#         save_button = ctk.CTkButton(
#             self.edit_window,
#             text="Save",
#             command=lambda: self.save_record(log_id),
#             fg_color="#1f538d",
#             hover_color="#14375e"
#         )
#         save_button.grid(row=8, column=0, columnspan=2, pady=10)

#     def save_record(self, log_id):
#         # Get the updated values from the entry fields
#         date = self.date_entry.get()
#         so_number = self.so_number_entry.get()
#         start_time_str = self.start_time_entry.get()
#         end_time_str = self.end_time_entry.get()
#         work_type = self.work_type_entry.get()
#         details = self.details_entry.get()
#         remarks = self.remarks_entry.get()
#         time_category = self.time_category_entry.get()

#         # Parse start_time and end_time
#         try:
#             start_time = datetime.strptime(start_time_str, "%H:%M").time()
#             end_time = datetime.strptime(end_time_str, "%H:%M").time()
#         except ValueError:
#             messagebox.showerror("Error", "Invalid time format. Please use HH:MM.")
#             return

#         # Calculate work_hours
#         start_datetime = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), start_time)
#         end_datetime = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), end_time)
#         work_hours = end_datetime - start_datetime

#         # Update the record in the database
#         conn = self.db.get_connection()
#         if not conn:
#             messagebox.showerror("Error", "Could not connect to database")
#             return

#         try:
#             with conn.cursor() as cursor:
#                 query = """
#                 UPDATE work_logs
#                 SET log_date = %s, so_number = %s, start_time = %s, end_time = %s,
#                 work_hours = %s, work_category = %s, details_of_work = %s, remarks = %s, time_category = %s
#                 WHERE log_id = %s
#                 """
#                 cursor.execute(query, (date, so_number, start_time_str, end_time_str, work_hours, work_type, details, remarks, time_category, log_id))
#                 conn.commit()
#                 messagebox.showinfo("Success", "Record updated successfully")
#                 self.edit_window.destroy()
#                 self.load_records()
#         except Exception as e:
#             messagebox.showerror("Error", f"Error updating record: {str(e)}")
#         finally:
#             conn.close()

#     def delete_record(self, event=None):
#         # Get the selected record
#         selected_items = self.tree.selection()
#         if not selected_items:
#             messagebox.showwarning("No Selection", "Please select a record to delete.")
#             return

#         selected_item = selected_items[0]
#         log_id = selected_item  # The item ID is the log_id

#         # Confirm deletion
#         confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?")
#         if not confirm:
#             return

#         # Delete the record from the database
#         conn = self.db.get_connection()
#         if not conn:
#             messagebox.showerror("Error", "Could not connect to database")
#             return

#         try:
#             with conn.cursor() as cursor:
#                 query = "DELETE FROM work_logs WHERE log_id = %s"
#                 cursor.execute(query, (log_id,))
#                 conn.commit()
#                 messagebox.showinfo("Success", "Record deleted successfully")
#                 self.load_records()
#         except Exception as e:
#             messagebox.showerror("Error", f"Error deleting record: {str(e)}")
#         finally:
#             conn.close()

#     def apply_filters(self, _=None):
#         print("Applying filters...")  # Debugging print statement
#         print("SO Number selected:", self.so_number_var.get())  # Debugging print statement

#         def fetch_data():
#             conn = self.db.get_connection()
#             if not conn:
#                 messagebox.showerror("Error", "Could not connect to database")
#                 return

#             try:
#                 with conn.cursor() as cursor:
#                     # Get the current user's ID and designation from the login system
#                     from login import User
#                     current_user = User.get_instance()
#                     current_user_id = current_user.get_user_id()
#                     current_user_software_authority = current_user.get_software_authority().lower()
#                     current_user_designation = current_user.get_designation().lower()

#                     # Base query with JOIN to fetch user name, user ID, and log_id
#                     query = """
#                     SELECT w.log_id, e.name, e.user_id, w.log_date, w.so_number, w.start_time, w.end_time, w.work_hours,
#                     w.work_category, w.details_of_work, w.remarks, w.time_category
#                     FROM work_logs w
#                     JOIN employees e ON w.user_id = e.user_id
#                     """

#                     # Parameters for the query
#                     params = []

#                     # If the user is not a Manager or Developer, filter by user_id
#                     if current_user_designation not in ["manager", "developer","dev"] or current_user_software_authority not in ["manager","developer","dev"]:
#                         query += " WHERE w.user_id = %s"
#                         params.append(current_user_id)

#                     # Add date range filter
#                     date_range = self.date_var.get()
#                     if date_range == "Today":
#                         today = datetime.now().date()
#                         query += " AND w.log_date = %s" if params else " WHERE w.log_date = %s"
#                         params.append(today)
#                     elif date_range == "This Week":
#                         start_of_week = datetime.now().date() - timedelta(days=datetime.now().weekday())
#                         end_of_week = start_of_week + timedelta(days=6)
#                         query += " AND w.log_date BETWEEN %s AND %s" if params else " WHERE w.log_date BETWEEN %s AND %s"
#                         params.extend([start_of_week, end_of_week])
#                     elif date_range == "This Month":
#                         start_of_month = datetime.now().date().replace(day=1)
#                         end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
#                         query += " AND w.log_date BETWEEN %s AND %s" if params else " WHERE w.log_date BETWEEN %s AND %s"
#                         params.extend([start_of_month, end_of_month])
#                     elif date_range == "Last 3 Months":
#                         start_of_3_months = datetime.now().date() - timedelta(days=90)
#                         query += " AND w.log_date >= %s" if params else " WHERE w.log_date >= %s"
#                         params.append(start_of_3_months)

#                     # Add work type filter
#                     work_type = self.type_var.get()
#                     if work_type != "All Types":
#                         query += " AND w.work_category = %s" if params else " WHERE w.work_category = %s"
#                         params.append(work_type)

#                     # Add Work Time Type filter
#                     time_category = self.time_category_var.get()
#                     if time_category != "All Types":
#                         query += " AND w.time_category = %s" if params else " WHERE w.time_category = %s"
#                         params.append(time_category)

#                     # Add SO Number filter
#                     so_number = self.so_number_var.get()
#                     if so_number != "All SO Numbers":
#                         query += " AND w.so_number = %s" if params else " WHERE w.so_number = %s"
#                         params.append(so_number)

#                     query += " ORDER BY w.log_date DESC"

#                     print("Executing query:", query)  # Debugging print statement
#                     print("With parameters:", params)  # Debugging print statement

#                     # Execute the query with parameters
#                     cursor.execute(query, tuple(params))
#                     records = cursor.fetchall()
#                     self.data_queue.put(records)

#             except Exception as e:
#                 messagebox.showerror("Error", f"Error fetching records: {str(e)}")
#             finally:
#                 conn.close()
#                 self.after(0, self.hide_loading_screen)

#         self.show_loading_screen()
#         thread = threading.Thread(target=fetch_data)
#         thread.daemon = True
#         thread.start()
#         self.after(100, self.process_data)

#     def reset_filters(self):
#         self.date_var.set("All Time")
#         self.type_var.set("All Types")
#         self.time_category_var.set("All Types")
#         self.so_number_var.set("All SO Numbers")  # Reset SO Number filter
#         self.load_records()

#     def download_excel(self):
#         # Fetch all records from the database
#         def fetch_all_records():
#             conn = self.db.get_connection()
#             if not conn:
#                 messagebox.showerror("Error", "Could not connect to database")
#                 return

#             try:
#                 with conn.cursor() as cursor:
#                     # Get the current user's ID and designation from the login system
#                     from login import User
#                     current_user = User.get_instance()
#                     current_user_id = current_user.get_user_id()
#                     current_user_designation = current_user.get_designation()

#                     # Base query with JOIN to fetch user name, user ID, and log_id
#                     query = """
#                     SELECT w.log_id, e.name, e.user_id, w.log_date, w.so_number, w.start_time, w.end_time, w.work_hours,
#                     w.work_category, w.details_of_work, w.remarks, w.time_category
#                     FROM work_logs w
#                     JOIN employees e ON w.user_id = e.user_id
#                     """

#                     # Parameters for the query
#                     params = []

#                     # If the user is not a Manager or Developer, filter by user_id
#                     if current_user_designation.lower() not in ["manager", "developer"]:
#                         query += " WHERE w.user_id = %s"
#                         params.append(current_user_id)

#                     query += " ORDER BY w.log_date DESC"

#                     # Execute the query with parameters
#                     cursor.execute(query, tuple(params))
#                     records = cursor.fetchall()
#                     return records

#             except Exception as e:
#                 messagebox.showerror("Error", f"Error fetching records: {str(e)}")
#                 return []
#             finally:
#                 conn.close()

#         # Fetch records
#         records = fetch_all_records()
#         if not records:
#             messagebox.showinfo("No Data", "No records found to export.")
#             return

#         # Convert records to a DataFrame
#         columns = [
#             "Log ID", "User Name", "User ID", "Date", "SO Number", "Start Time", "End Time",
#             "Work Time", "Work Type", "Details of Work", "Remarks", "Work Time Type"
#         ]
#         df = pd.DataFrame(records, columns=columns)

#         # Format the "Date" column as a string in the desired format
#         df["Date"] = df["Date"].apply(lambda x: x.strftime("%Y-%m-%d") if x else "")

#         # Format the "Start Time" and "End Time" columns as strings
#         def format_time(value):
#             if isinstance(value, timedelta):
#                 # Convert timedelta to HH:MM:SS format
#                 total_seconds = int(value.total_seconds())
#                 hours, remainder = divmod(total_seconds, 3600)
#                 minutes, seconds = divmod(remainder, 60)
#                 return f"{hours:02}:{minutes:02}:{seconds:02}"
#             elif isinstance(value, time):  # Use the imported time class
#                 # Format time objects as HH:MM
#                 return value.strftime("%H:%M")
#             else:
#                 return ""

#         df["Start Time"] = df["Start Time"].apply(format_time)
#         df["End Time"] = df["End Time"].apply(format_time)

#         # Format the "Work Time" column as a string
#         df["Work Time"] = df["Work Time"].apply(lambda x: str(x) if x else "")

#         # Ask the user where to save the file
#         file_path = filedialog.asksaveasfilename(
#             defaultextension=".xlsx",
#             filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
#             title="Save file as"
#         )

#         if not file_path:  # If the user cancels the dialog
#             return

#         # Save DataFrame to Excel
#         try:
#             df.to_excel(file_path, index=False)
#             messagebox.showinfo("Success", f"Records exported to {file_path}")
#         except Exception as e:
#             messagebox.showerror("Error", f"Error saving file: {str(e)}")

# def main():
#     ctk.set_appearance_mode("System")
#     ctk.set_default_color_theme("blue")
#     app = RecordViewer()
#     app.mainloop()


# if __name__ == "__main__":
#     main()
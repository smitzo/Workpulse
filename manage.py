import os
import json
import pandas as pd
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from PIL import Image
import pymysql
from mysql.connector import Error
from dbutils.pooled_db import PooledDB
from login import User
from datetime import datetime
from developer_mode import EmployeeLimitConfig
from config import DATABASE_CONFIG
from tkinter import colorchooser
from new import NewRecordForm

# Path to the clock configuration file
CLOCK_CONFIG_FILE = "clock_config.json"

class DatabaseManager:
    _instance = None
    _pool = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance
    
    def __init__(self):
        self._pool = PooledDB (
            creator=pymysql,
            maxconnections=6,
            host=DATABASE_CONFIG['host'],
            database=DATABASE_CONFIG['database'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password'],
            charset='utf8mb4'
            )
        
        self._init_tables()
    
    def get_connection(self):
        try:
            return self._pool.connection()
        except Error as e:
            messagebox.showerror("Connection Error", str(e))
            return None
    
    def _init_tables(self):
        with self.get_connection() as conn:
            with conn.cursor() as c:
                c.execute("""CREATE TABLE IF NOT EXISTS employees(
                    row_id INT AUTO_INCREMENT,
                    name VARCHAR(100) NOT NULL,
                    user_id VARCHAR(100) PRIMARY KEY,
                    password VARCHAR(100) NOT NULL,
                    designation VARCHAR(100) NOT NULL,
                    software_authority VARCHAR(100) NOT NULL,
                    UNIQUE (row_id)
                )""")
                
                c.execute("""CREATE TABLE IF NOT EXISTS designations(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    designation VARCHAR(100) UNIQUE NOT NULL
                )""")

                c.execute("""CREATE TABLE IF NOT EXISTS software_authority(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    software_authority VARCHAR(100) UNIQUE NOT NULL
                )""")

                c.execute(""" 
                    CREATE TABLE IF NOT EXISTS work_logs(
                        log_id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id VARCHAR(100) NOT NULL,
                        log_date DATE NOT NULL,
                        so_number VARCHAR(100) NOT NULL,
                        work_category VARCHAR(100) NOT NULL,
                        details_of_work VARCHAR(100) NOT NULL,
                        remarks VARCHAR(255)    ,
                        time_category VARCHAR(100) NOT NULL,
                        work_hours FLOAT(10,2) NOT NULL,
                        start_time TIME,
                        end_time TIME,
                        FOREIGN KEY (user_id) REFERENCES employees(user_id)
                        )
                    """)
                
                c.execute (""" CREATE TABLE IF NOT EXISTS work_details_table(
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        details_of_work VARCHAR(255) UNIQUE,
                        ideal_time FLOAT(10,2))   
                    """)
                
                c.execute("""CREATE TABLE IF NOT EXISTS work_groups(
                        group_id INT AUTO_INCREMENT PRIMARY KEY,
                        group_name VARCHAR(100) NOT NULL,
                        color_code VARCHAR(10) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
                c.execute("""CREATE TABLE IF NOT EXISTS work_group_items(
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        group_id INT NOT NULL,
                        work_item VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (group_id) REFERENCES work_groups(group_id) ON DELETE CASCADE,
                        UNIQUE KEY unique_group_item (group_id, work_item)
                    )
                """)

                    # Add the new SO numbers table
                c.execute("""CREATE TABLE IF NOT EXISTS so_numbers(
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        so_number VARCHAR(100) UNIQUE NOT NULL      
                )""")

            conn.commit()
    
    def insert_ideal_time(self, details_of_work , ideal_time ):
        with self.get_connection() as conn:
            with conn.cursor() as c:
                try:
                    c.execute("""
                    INSERT INTO work_details_table (details_of_work, ideal_time) 
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE ideal_time = VALUES(ideal_time)
                    """, (details_of_work,ideal_time))
                    conn.commit()
                except Error as e:
                    messagebox.showerror("Database Error", f"Failed to insert into work_details_table: {str(e)}")
                    conn.rollback()

    def get_available_work_items(self):
        with self.get_connection() as conn:
            with conn.cursor() as c:
                c.execute("SELECT details_of_work FROM work_details_table")
                return [row[0] for row in c.fetchall()]

    def create_work_group(self, group_name, items, color_code):
        try:
            with self.get_connection() as conn:
                with conn.cursor() as c:
                    c.execute("SELECT COUNT(*) FROM work_groups WHERE group_name = %s", (group_name,))
                    if c.fetchone()[0] > 0:
                        raise ValueError("Group name already exists")
                    
                    try:
                        c.execute("BEGIN")
                        c.execute("""
                            INSERT INTO work_groups (group_name, color_code) 
                            VALUES (%s, %s)
                        """, (group_name, color_code))
                        group_id = c.lastrowid
                        for item in items:
                            c.execute("""
                                INSERT INTO work_group_items (group_id, work_item)
                                VALUES (%s, %s)
                            """, (group_id, item))
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        raise e
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to create work group: {str(e)}")
            raise

    def get_work_groups(self):
        try:
            with self.get_connection() as conn:
                with conn.cursor() as c:
                    c.execute("""
                        SELECT g.group_name, gi.work_item, g.color_code
                        FROM work_groups g 
                        LEFT JOIN work_group_items gi ON g.group_id = gi.group_id
                        ORDER BY g.group_name, gi.work_item
                    """)
                    groups = {}
                    for group_name, work_item, color_code in c.fetchall():
                        if group_name not in groups:
                            groups[group_name] = {
                                'items': [],
                                'color': color_code or '#000000'
                            }
                        if work_item:
                            groups[group_name]['items'].append(work_item)
                    return groups
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch work groups: {str(e)}")
            return {}

    def delete_work_group(self, group_name):
        try:
            with self.get_connection() as conn:
                with conn.cursor() as c:
                    try:
                        c.execute("BEGIN")
                        c.execute("SELECT group_id FROM work_groups WHERE group_name = %s", (group_name,))
                        result = c.fetchone()
                        if not result:
                            raise ValueError("Group not found")
                        group_id = result[0]
                        c.execute("DELETE FROM work_group_items WHERE group_id = %s", (group_id,))
                        c.execute("DELETE FROM work_groups WHERE group_id = %s", (group_id,))
                        c.execute("COMMIT")
                    except Exception as e:
                        c.execute("ROLLBACK")
                        raise e
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to delete work group: {str(e)}")
            raise

    def add_so_number(self, so_number):
        """Add a new SO number to the database."""
        with self.get_connection() as conn:
            with conn.cursor() as c:
                try:
                    c.execute("INSERT INTO so_numbers (so_number) VALUES (%s)", (so_number,))
                    conn.commit()
                except Error as e:
                    messagebox.showerror("Database Error", f"Failed to add SO number: {str(e)}")
                    conn.rollback()

    def get_so_numbers(self):
        """Fetch all SO numbers from the database."""
        with self.get_connection() as conn:
            with conn.cursor() as c:
                c.execute("SELECT so_number FROM so_numbers")
                return [row[0] for row in c.fetchall()]

    def delete_so_number(self, so_number):
        """Delete an SO number from the database."""
        with self.get_connection() as conn:
            with conn.cursor() as c:
                try:
                    c.execute("DELETE FROM so_numbers WHERE so_number = %s", (so_number,))
                    conn.commit()
                except Error as e:
                    messagebox.showerror("Database Error", f"Failed to delete SO number: {str(e)}")
                    conn.rollback()

class ManagementApp:
    def __init__(self, parent=None):
        self.db = DatabaseManager.get_instance()
        self.parent = parent
        self.setup_ui(parent)
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)

    def run(self):
        if self.parent:
            self.window.protocol("WM_DELETE_WINDOW", self.close_app)
            self.window.mainloop()
        else:
            self.window.mainloop()

    def close_app(self):
        try:
            if self.parent:
                if hasattr(self, 'db'):
                    self.db._pool.close()
                self.window.destroy()
                self.parent.deiconify()
        except Exception as e:
            print(f"Error closing application: {e}")
            if self.parent:
                self.parent.deiconify()
    
    def setup_ui(self, parent):
        if parent:
            self.window = ctk.CTkFrame(parent)
            self.window.pack(expand=True, fill='both', padx=20, pady=20)
        else:
            self.window = ctk.CTk()
            self.window.geometry("1600x900")
            self.window.resizable(True, True)
            self.window.title("Employee Management")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            background_image = ctk.CTkImage(Image.open(os.path.join(current_dir, "assets", "bg2.png")), size=(1600, 900))
            background_label = ctk.CTkLabel(self.window, image=background_image, text="")
            background_label.place(relx=0.5, rely=0.5, anchor="center")
            self.background_image = background_image
        except FileNotFoundError:
            messagebox.showerror("Error", "Background image not found")

        user = User.get_instance()
        user_frame = ctk.CTkFrame(self.window, fg_color="transparent")
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
            text=f"Name: {user.get_designation()}", 
            font=("Arial", 14, "bold"), 
            text_color="white"
        )
        designation.pack(anchor="e")
        
        user_role = ctk.CTkLabel(
            user_frame, 
            text=f"Software_authority: {user.get_software_authority()}", 
            font=("Arial", 14, "bold"), 
            text_color="white"
        )
        user_role.pack(anchor="e")

        self.main_frame = ctk.CTkFrame(self.window)
        self.main_frame.pack(padx=20, pady=20)
        self.show_main_menu()
    
    def show_main_menu(self):
        self.clear_frame()
        buttons = [
            ("❇ Add Employee", self.show_add_employee),
            ("👁 View Employees", self.show_employees),
            ("⚙ Add designations & authority", self.show_settings_menu),
            ("Add Work Details", self.show_work_details_menu),
            ("👥 Manage Work Groups", self.show_work_groups_manager),
            ("📊 Show employee SO mapping", self.show_employee_so_mapping),
            ("Toggle clock",self.toggle_clock)
        ]

        # Add the toggle clock button only for Managers or Developers
        user = User.get_instance()
        if user.get_designation() in ["Manager", "Developer"] or user.get_software_authority() == "Developer":
            ctk.CTkButton(
                self.main_frame,
                text="⏰ Toggle Clock",
                command=self.toggle_clock,
                width=200,
                height=40
            ).pack(pady=10)

        for text, command in buttons:
            ctk.CTkButton(self.main_frame, text=text, command=command, 
                        width=200, height=40).pack(pady=10)

        ctk.CTkButton(
            self.main_frame,
            text="🔙 Back",
            width=200,
            height=40,
            command=self.go_back
        ).pack(pady=20)

    # def open_new_record_form(self):
    #     self.new_record_form = NewRecordForm(parent=self.window)
    #     self.new_record_form.run()

    def get_clock_state(self):
        """Read the clock state from the JSON file."""
        try:
            with open("clock_config.json", "r") as file:
                config = json.load(file)
                return config.get("clock_on", True)  # Default to True if key not found
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read clock state: {e}")
            return True  # Default to True if an error occurs

    def set_clock_state(self, clock_on):
        """Write the clock state to the JSON file."""
        try:
            with open("clock_config.json", "w") as file:
                json.dump({"clock_on": clock_on}, file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save clock state: {e}")

    def toggle_clock(self):
        """Toggle the clock state in the JSON file."""
        try:
            # Get the current clock state
            current_state = self.get_clock_state()
            
            # Toggle the state
            new_state = not current_state
            
            # Save the new state to the JSON file
            self.set_clock_state(new_state)
            
            # Show a success message
            messagebox.showinfo("Success", f"Clock is now {'On' if new_state else 'Off'}!")
            
            # If the NewRecordForm is open, update its clock state
            if hasattr(self, 'new_record_form'):
                self.new_record_form.set_clock_state(new_state)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle clock: {str(e)}")

    def show_employee_so_mapping(self):
        """Open the RecordViewer window with employee and SO Number filters"""
        self.clear_frame()

        # Create a frame for the filters and Treeview
        records_frame = ctk.CTkFrame(self.main_frame)
        records_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Add a filter frame for SO Number
        filter_frame = ctk.CTkFrame(records_frame)
        filter_frame.pack(fill='x', padx=10, pady=10)

        # SO Number Filter (Multi-Select)
        ctk.CTkLabel(filter_frame, text="Filter by SO Number:").pack(side=tk.LEFT, padx=5)
        self.so_number_filter_var = ctk.StringVar(value="All SO Numbers")
        self.so_number_filter = tk.Listbox(filter_frame, selectmode=tk.MULTIPLE, height=5)
        self.so_number_filter.pack(side=tk.LEFT, padx=5, fill='x', expand=True)

        # Populate the SO Number filter with available SO numbers
        so_numbers = self.get_so_numbers()
        for so_number in so_numbers:
            self.so_number_filter.insert(tk.END, so_number)

        # Add a "Download Excel" button
        download_button = ctk.CTkButton(
            filter_frame,
            text="📥 Download Excel for Selected SO Numbers",
            command=self.download_so_number_excel,
            width=300,
            height=30
        )
        download_button.pack(side=tk.LEFT, padx=10)

        # Create Treeview to display records
        self.tree = ttk.Treeview(
            records_frame,
            columns=("Employee", "SO Number", "Details of Work", "Hours"),
            show="headings"
        )
        self.tree.heading("Employee", text="Employee")
        self.tree.heading("SO Number", text="SO Number")
        self.tree.heading("Details of Work", text="Details of Work")
        self.tree.heading("Hours", text="Hours")
        self.tree.pack(expand=True, fill='both', padx=10, pady=10)

        # Load initial records
        self.apply_filters()

        # Add a "Back" button to return to the main menu
        back_button = ctk.CTkButton(
            self.main_frame,
            text="🔙 Back",
            command=self.show_main_menu,
            width=200,
            height=40
        )
        back_button.pack(pady=20)


    def download_so_number_excel(self):
        """Download Excel files for all selected SO numbers in one go"""
        selected_indices = self.so_number_filter.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one SO number.")
            return

        selected_so_numbers = [self.so_number_filter.get(i) for i in selected_indices]

        # Ask the user to select a folder to save all Excel files
        folder_path = tk.filedialog.askdirectory(title="Select Folder to Save Excel Files")
        if not folder_path:
            return  # User canceled folder selection

        try:
            for so_number in selected_so_numbers:
                # Fetch data for the selected SO number
                with self.db.get_connection() as conn:
                    with conn.cursor() as c:
                        query = """
                            SELECT e.name, w.so_number, w.details_of_work, SUM(w.work_hours) as total_hours
                            FROM work_logs w
                            JOIN employees e ON w.user_id = e.user_id
                            WHERE w.so_number = %s
                            GROUP BY e.name, w.so_number, w.details_of_work
                        """
                        c.execute(query, (so_number,))
                        records = c.fetchall()

                # Convert records to a DataFrame
                df = pd.DataFrame(records, columns=["Employee", "SO Number", "Details of Work", "Total Hours"])

                # Save to Excel in the selected folder
                file_name = f"SO_{so_number}_data.xlsx"
                file_path = os.path.join(folder_path, file_name)
                df.to_excel(file_path, index=False)

            messagebox.showinfo("Success", f"All files saved successfully in:\n{folder_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def get_so_numbers(self):
        """Fetch all unique SO Numbers from the database"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as c:
                    c.execute("SELECT DISTINCT so_number FROM work_logs")
                    return [row[0] for row in c.fetchall()]
        except Error as e:
            messagebox.showerror("Error", f"Failed to fetch SO Numbers: {str(e)}")
            return []

    def apply_filters(self, _=None):
        """Fetch and display records based on the selected SO Number filter"""
        selected_so_number = self.so_number_filter_var.get()

        # Base query with GROUP BY and SUM
        query = """
            SELECT e.name, w.so_number, w.details_of_work, SUM(w.work_hours) as total_hours
            FROM work_logs w
            JOIN employees e ON w.user_id = e.user_id
            WHERE 1=1
        """

        # Add SO Number filter if selected
        if selected_so_number != "All SO Numbers":
            query += f" AND w.so_number = '{selected_so_number}'"

        # Group by Employee, SO Number, and Details of Work
        query += " GROUP BY e.name, w.so_number, w.details_of_work"

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as c:
                    c.execute(query)
                    records = c.fetchall()

                    # Clear existing items in the Treeview
                    for item in self.tree.get_children():
                        self.tree.delete(item)

                    # Insert new records
                    for record in records:
                        self.tree.insert("", tk.END, values=record)
        except Error as e:
            messagebox.showerror("Error", f"Failed to fetch records: {str(e)}")

    # def get_employee_names(self):
    #     """Fetch all employee names from the database"""
    #     try:
    #         with self.db.get_connection() as conn:
    #             with conn.cursor() as c:
    #                 c.execute("SELECT name FROM employees")
    #                 return [row[0] for row in c.fetchall()]
    #     except Error as e:
    #         messagebox.showerror("Error", f"Failed to fetch employee names: {str(e)}")
    #         return []

    def apply_employee_filter(self, _=None):
        """Fetch and display records based on the selected employee filter"""
        selected_employee = self.employee_filter_var.get()
        query = """
            SELECT e.name, w.so_number, w.details_of_work, w.work_hours
            FROM work_logs w
            JOIN employees e ON w.user_id = e.user_id
        """
        if selected_employee != "All Employees":
            query += f" WHERE e.name = '{selected_employee}'"

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as c:
                    c.execute(query)
                    records = c.fetchall()

                    # Clear existing items in the Treeview
                    for item in self.tree.get_children():
                        self.tree.delete(item)

                    # Insert new records
                    for record in records:
                        self.tree.insert("", tk.END, values=record)
        except Error as e:
            messagebox.showerror("Error", f"Failed to fetch records: {str(e)}")

    def go_back(self):
        if self.parent:
            self.window.destroy()
            self.parent.deiconify()

    def show_settings_menu(self):
        self.clear_frame()
        ctk.CTkButton(self.main_frame, text="<< Back", 
                    command=self.show_main_menu).pack(pady=10)
        
        ctk.CTkButton(self.main_frame, text="Manage Designations", 
                    command=lambda: self.manage_options('designation')).pack(pady=10)
        ctk.CTkButton(self.main_frame, text="Manage Authorities", 
                    command=lambda: self.manage_options('software_authority')).pack(pady=10)

    def manage_options(self, option_type):
        settings_window = ctk.CTkToplevel()
        settings_window.title(f"Manage {option_type.capitalize()}")
        settings_window.geometry("300x400")
        
        listbox = tk.Listbox(settings_window)
        listbox.pack(pady=10)
        
        # Fetch options from the database based on the selected type
        options = self.get_options(option_type)
        for option in options:
            listbox.insert(tk.END, option)
        
        entry = ctk.CTkEntry(settings_window)
        entry.pack(pady=5)
        
        # Add "Add" and "Delete" buttons
        button_frame = ctk.CTkFrame(settings_window)
        button_frame.pack(pady=5)
        
        ctk.CTkButton(
            button_frame,
            text="Add",
            command=lambda: self.add_option(option_type, entry, listbox)
        ).pack(side=tk.LEFT, padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Delete",
            command=lambda: self.delete_option(option_type, listbox)
        ).pack(side=tk.LEFT, padx=5)

    def add_option(self, option_type, entry, listbox):
        value = entry.get().strip()
        if value:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as c:
                        if option_type == 'designation':
                            # Check if the designation already exists
                            c.execute("SELECT COUNT(*) FROM designations WHERE designation = %s", (value,))
                            if c.fetchone()[0] > 0:
                                messagebox.showwarning("Warning", f"Designation '{value}' already exists!")
                                return
                            
                            # Insert the new designation
                            c.execute("INSERT INTO designations (designation) VALUES (%s)", (value,))
                        elif option_type == 'software_authority':
                            # Check if the software authority already exists
                            c.execute("SELECT COUNT(*) FROM software_authority WHERE software_authority = %s", (value,))
                            if c.fetchone()[0] > 0:
                                messagebox.showwarning("Warning", f"Software Authority '{value}' already exists!")
                                return
                            
                            # Insert the new software authority
                            c.execute("INSERT INTO software_authority (software_authority) VALUES (%s)", (value,))
                        conn.commit()
                    listbox.insert(tk.END, value)
                    entry.delete(0, tk.END)
            except Error as e:
                messagebox.showerror("Error", str(e))

    def delete_option(self, option_type, listbox):
        selection = listbox.curselection()
        if selection:
            value = listbox.get(selection)
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as c:
                        if option_type == 'designation':
                            c.execute("DELETE FROM designations WHERE designation = %s", (value,))
                        elif option_type == 'software_authority':
                            c.execute("DELETE FROM software_authority WHERE software_authority = %s", (value,))
                    conn.commit()
                listbox.delete(selection)
            except Error as e:
                messagebox.showerror("Error", str(e))

    def show_add_employee(self):
        self.clear_frame()
        fields = [
            ("Employee Name", "name"),
            ("User ID", "user_id"),
            ("Password", "password")
        ]
        self.entries = {}
        
        # Back Button
        ctk.CTkButton(self.main_frame, text="<< Back", 
                    command=self.show_main_menu).pack(pady=10)
        
        # Add fields for manual employee entry
        for label, key in fields:
            frame = ctk.CTkFrame(self.main_frame)
            frame.pack(pady=5)
            ctk.CTkLabel(frame, text=label).pack(side=tk.LEFT, padx=5)
            self.entries[key] = ctk.CTkEntry(frame, width=400)
            self.entries[key].pack(side=tk.LEFT, padx=5)
        
        self.entries['designation'] = self.add_combobox("Designation", 'designation')
        self.entries['authority'] = self.add_combobox("Software Authority", 
                                                    'software_authority')
        
        # Save Button for manual entry
        ctk.CTkButton(self.main_frame, text="💾 Save", 
                    command=self.add_employee).pack(pady=10)
        
        # Add "Upload Excel" Button
        ctk.CTkButton(
            self.main_frame,
            text="📤 Upload Excel File",
            command=self.upload_employee_excel,
            width=200,
            height=40
        ).pack(pady=20)

    def upload_employee_excel(self):
        file_path = tk.filedialog.askopenfilename(
            filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        if not file_path:
            return

        try:
            data = pd.read_excel(file_path)
            expected_columns = ['Row ID', 'Name', 'User ID', 'Designation', 'Authority', 'password']
            
            if not all(column in data.columns for column in expected_columns):
                messagebox.showerror("Error", "Invalid Excel format. Columns should be like 'name', 'user_id', 'password', 'designation', 'software_authority'")
                return

            if data.isnull().values.any():
                messagebox.showerror("Error", "Excel file contains empty cells. Please fill all fields.")
                return

            with self.db.get_connection() as conn:
                with conn.cursor() as c:
                    # Check current employee count
                    c.execute("SELECT COUNT(*) FROM employees")
                    current_count = c.fetchone()[0]
                    employee_limit = EmployeeLimitConfig.get_employee_limit()

                    # Check if adding new employees will exceed the limit
                    if current_count + len(data) > employee_limit:
                        messagebox.showerror("Error", f"Cannot add employees. Employee limit ({employee_limit}) will be exceeded.")
                        return

                    for _, row in data.iterrows():
                        print(f"Processing User ID: {row['User ID']}")  # Debugging
                        c.execute("SELECT COUNT(*) FROM employees WHERE user_id = %s", (row['User ID'],))
                        if c.fetchone()[0] > 0:
                            messagebox.showwarning("Warning", f"Employee with User ID {row['User ID']} already exists. Skipping.")
                            continue

                        c.execute("""
                            INSERT INTO employees (name, user_id, password, designation, software_authority)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            row['Name'], row['User ID'], row['password'],
                            row['Designation'], row['Authority']
                        ))
                    conn.commit()

            messagebox.showinfo("Success", "Employee details uploaded successfully!")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload employee details: {str(e)}")

    def show_work_details_menu(self):
        self.clear_frame()
        self.entries = {}

        main_container = ctk.CTkFrame(self.main_frame)
        main_container.pack(expand=True, fill='both', padx=20, pady=20)

        ctk.CTkLabel(
            main_container,
            text="Work Details Management",
            font=("Arial", 20, "bold")
        ).pack(pady=(0, 20))

        ctk.CTkButton(
            main_container,
            text="<< Back",
            command=self.show_main_menu,
            width=120
        ).pack(pady=(0, 20))

        left_frame = ctk.CTkFrame(main_container)
        left_frame.pack(side=tk.LEFT, fill='both', expand=True, padx=(0, 10))
        
        right_frame = ctk.CTkFrame(main_container)
        right_frame.pack(side=tk.RIGHT, fill='both', expand=True, padx=(10, 0))

        ctk.CTkLabel(
            left_frame,
            text="Add New Work Type",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        existing_works_frame = ctk.CTkFrame(left_frame)
        existing_works_frame.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkLabel(existing_works_frame, text="See Existing Works:").pack(side=tk.LEFT, padx=5)
        
        existing_works = self.fetch_work_details()
        
        self.existing_works_combo = ctk.CTkComboBox(
            existing_works_frame, 
            values=existing_works if existing_works else ["No existing works"],
            width=300
        )
        self.existing_works_combo.pack(side=tk.LEFT, fill='x', expand=True, padx=5)

        work_type_frame = ctk.CTkFrame(left_frame)
        work_type_frame.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkLabel(work_type_frame, text="New Work Type:").pack(side=tk.LEFT, padx=5)
        self.entries['work type'] = ctk.CTkEntry(work_type_frame, width=300)
        self.entries['work type'].pack(side=tk.LEFT, fill='x', expand=True, padx=5)

        ideal_time_frame = ctk.CTkFrame(left_frame)
        ideal_time_frame.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkLabel(ideal_time_frame, text="Ideal Time (hours):").pack(side=tk.LEFT, padx=5)
        self.entries['ideal time'] = ctk.CTkEntry(ideal_time_frame, width=300)
        self.entries['ideal time'].pack(side=tk.LEFT, fill='x', expand=True, padx=5)
        self.entries['ideal time'].insert(0, "0")  # Default value

        # Save Button
        ctk.CTkButton(
            left_frame,
            text="💾 Save Work Type",
            command=self.save_work_details,
            width=200
        ).pack(pady=20)

        # Add SO Number Button
        ctk.CTkButton(
            left_frame,
            text="➕ Add New SO Number",
            command=self.show_so_number_manager,
            width=200
        ).pack(pady=20)

        # Right Frame - Excel Upload
        ctk.CTkLabel(
            right_frame,
            text="Bulk Upload Work Logs",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # Upload Button
        ctk.CTkButton(
            right_frame,
            text="📤 Upload Excel File",
            command=self.upload_work_logs_excel,
            width=200
        ).pack(pady=20)

    def show_so_number_manager(self):
        """Show a window to manage SO numbers."""
        so_window = ctk.CTkToplevel()
        so_window.title("Manage SO Numbers")
        so_window.geometry("400x300")

        # Listbox to display SO numbers
        listbox_frame = ctk.CTkFrame(so_window)
        listbox_frame.pack(fill='both', expand=True, padx=10, pady=10)

        listbox = tk.Listbox(listbox_frame)
        listbox.pack(fill='both', expand=True, padx=5, pady=5)

        # Populate listbox with existing SO numbers
        so_numbers = self.db.get_so_numbers()
        for so_number in so_numbers:
            listbox.insert(tk.END, so_number)

        # Entry for new SO number
        entry_frame = ctk.CTkFrame(so_window)
        entry_frame.pack(fill='x', padx=10, pady=5)

        so_entry = ctk.CTkEntry(entry_frame)
        so_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5)

        def add_so_number():
            so_number = so_entry.get().strip()
            if so_number:
                try:
                    self.db.add_so_number(so_number)
                    listbox.insert(tk.END, so_number)
                    so_entry.delete(0, tk.END)
                except Error as e:
                    messagebox.showerror("Error", str(e))

        def delete_so_number():
            selection = listbox.curselection()
            if selection:
                so_number = listbox.get(selection)
                try:
                    self.db.delete_so_number(so_number)
                    listbox.delete(selection)
                except Error as e:
                    messagebox.showerror("Error", str(e))

        # Add and Delete buttons
        button_frame = ctk.CTkFrame(so_window)
        button_frame.pack(fill='x', padx=10, pady=5)

        ctk.CTkButton(
            button_frame,
            text="Add",
            command=add_so_number
        ).pack(side=tk.LEFT, expand=True, padx=5)

        ctk.CTkButton(
            button_frame,
            text="Delete",
            command=delete_so_number
        ).pack(side=tk.LEFT, expand=True, padx=5)

    def fetch_work_details(self):
        """Fetch existing work details from the database"""
        db_manager = DatabaseManager.get_instance()
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    try:
                        cursor.execute("SELECT DISTINCT details_of_work FROM work_details_table ORDER BY details_of_work")
                        work_details = [row[0] for row in cursor.fetchall()]
                    except Error:
                        cursor.execute("SELECT DISTINCT details_of_work FROM work_logs ORDER BY details_of_work")
                        work_details = [row[0] for row in cursor.fetchall()]
                    return work_details if work_details else []
        except Exception as e:
            print(f"Error fetching work details: {e}")
        return []

    def save_work_details(self):
        details_of_work = self.entries['work type'].get().strip().lower()
        ideal_time = self.entries['ideal time'].get().strip()

        try:
            ideal_time = float(ideal_time)
            if ideal_time < 0:
                messagebox.showerror("Input Error", "Ideal time cannot be negative!")
                return
        except ValueError:
            messagebox.showerror("Input Error", "Ideal time must be a valid number!")
            return

        if not details_of_work:
            messagebox.showerror("Input Error", "Please enter a work type!")
            return

        try:
            db = DatabaseManager.get_instance()
            db.insert_ideal_time(details_of_work, ideal_time)
            self.entries['work type'].delete(0, tk.END)
            self.entries['ideal time'].delete(0, tk.END)
            self.entries['ideal time'].insert(0, "0")
            messagebox.showinfo("Success", "Work type saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save work details: {str(e)}")

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_work_groups_manager(self):
        self.clear_frame()
        
        # Back Button
        ctk.CTkButton(
            self.main_frame, 
            text="<< Back", 
            command=self.show_main_menu
        ).pack(pady=10)
        
        # Main title
        ctk.CTkLabel(
            self.main_frame, 
            text="Work Groups Manager", 
            font=("Arial", 20, "bold")
        ).pack(pady=(0, 20))
        
        # Create main container
        container = ctk.CTkFrame(self.main_frame)
        container.pack(expand=True, fill='both', padx=20, pady=10)
        
        # Split into left and right panels
        left_panel = ctk.CTkFrame(container)
        left_panel.pack(side=tk.LEFT, fill='both', expand=True, padx=(0, 10))
        
        right_panel = ctk.CTkFrame(container)
        right_panel.pack(side=tk.RIGHT, fill='both', expand=True, padx=(10, 0))
        
        # Left Panel - Create New Group
        ctk.CTkLabel(
            left_panel, 
            text="Create New Work Group", 
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Group name entry
        name_frame = ctk.CTkFrame(left_panel)
        name_frame.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkLabel(name_frame, text="Group Name:").pack(side=tk.LEFT, padx=5)
        group_name_entry = ctk.CTkEntry(name_frame)
        group_name_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5)
        
        # Color picker frame
        color_frame = ctk.CTkFrame(left_panel)
        color_frame.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkLabel(color_frame, text="Group Color:").pack(side=tk.LEFT, padx=5)
        
        # Variable to store the selected color
        color_var = tk.StringVar(value="#000000")
        
        # Create color button before defining choose_color
        color_button = ctk.CTkButton(
            color_frame,
            text="Pick Color",
            width=100
        )

        def choose_color():
            """Color picker with proper error handling"""
            try:
                result = colorchooser.askcolor(title="Choose Group Color")
                if result and result[1]:
                    color = result[1]
                    color_var.set(color)
                    color_button.configure(fg_color=color)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to set color: {str(e)}")

        # Configure color button command after defining choose_color
        color_button.configure(command=choose_color)
        color_button.pack(side=tk.LEFT, padx=5)
        
        # Available work items
        ctk.CTkLabel(
            left_panel, 
            text="Available Work Items", 
            font=("Arial", 14)
        ).pack(pady=10)
        
        # Create a frame for the listbox and scrollbar
        listbox_frame = ctk.CTkFrame(left_panel)
        listbox_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create scrollbar
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        
        # Create listbox with multiple selection enabled
        work_items_listbox = tk.Listbox(
            listbox_frame, 
            selectmode=tk.MULTIPLE,
            yscrollcommand=scrollbar.set
        )
        work_items_listbox.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.config(command=work_items_listbox.yview)
        
        # Populate listbox with available work items
        available_items = self.db.get_available_work_items()
        for item in available_items:
            work_items_listbox.insert(tk.END, item)
        
        # Right Panel - Existing Groups
        ctk.CTkLabel(
            right_panel, 
            text="See Existing Groups", 
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Create text widget for displaying groups
        groups_text = tk.Text(right_panel, wrap=tk.WORD)
        groups_text.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Add a scrollbar for the Text widget
        scrollbar = tk.Scrollbar(right_panel, command=groups_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        groups_text.config(yscrollcommand=scrollbar.set)
        
        def update_groups_display():
            """Update the display of existing groups"""
            try:
                # Save current scroll position
                current_pos = groups_text.yview()
                
                # Update content
                groups_text.configure(state='normal')
                groups_text.delete('1.0', tk.END)
                
                groups = self.db.get_work_groups()
                if not groups:
                    groups_text.insert('1.0', "No work groups defined yet.")
                    return
                
                for group_name, group_data in groups.items():
                    color = group_data.get('color', '#000000')
                    tag_name = f"group_{group_name}"
                    groups_text.tag_configure(tag_name, foreground=color)
                    
                    groups_text.insert('end', f"\n📌 {group_name}:\n", tag_name)
                    
                    for item in group_data['items']:
                        groups_text.insert('end', f"   • {item}\n", tag_name)
                    groups_text.insert('end', "\n")
                
                # Restore scroll position
                groups_text.yview_moveto(current_pos[0])
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update groups display: {str(e)}")
            finally:
                groups_text.configure(state='disabled')
        
        def create_group():
            """Handle group creation"""
            group_name = group_name_entry.get().strip()
            if not group_name:
                messagebox.showwarning("Warning", "Please enter a group name")
                return
            
            selected_indices = work_items_listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("Warning", "Please select at least one work item")
                return
            
            selected_items = [work_items_listbox.get(idx) for idx in selected_indices]
            selected_color = color_var.get()
            
            try:
                self.db.create_work_group(group_name, selected_items, selected_color)
                messagebox.showinfo("Success", f"Work group '{group_name}' created successfully")
                
                # Clear selections and entry
                group_name_entry.delete(0, tk.END)
                work_items_listbox.selection_clear(0, tk.END)
                color_var.set("#000000")
                color_button.configure(fg_color=("#3B8ED0", "#1F6AA5"))
                
                # Update display
                update_groups_display()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create work group: {str(e)}")

        def delete_selected_group():
            """Delete the currently selected group"""
            text_content = groups_text.get('1.0', tk.END)
            cursor_pos = groups_text.index(tk.INSERT)
            
            # Find the current group name based on cursor position
            lines = text_content.split('\n')
            current_line = int(float(cursor_pos.split('.')[0]))
            
            group_name = None
            for i in range(current_line, 0, -1):
                if i <= len(lines) and lines[i-1].startswith('📌'):
                    group_name = lines[i-1].replace('📌', '').strip(':').strip()
                    break
            
            if group_name:
                if messagebox.askyesno("Confirm Delete", f"Delete group '{group_name}'?"):
                    try:
                        self.db.delete_work_group(group_name)
                        messagebox.showinfo("Success", f"Group '{group_name}' deleted")
                        update_groups_display()
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to delete group: {str(e)}")
            else:
                messagebox.showwarning("Warning", "Please select a group to delete")
        
        # Button frame
        button_frame = ctk.CTkFrame(left_panel)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame, 
            text="Create Group",
            command=create_group
        ).pack(side=tk.LEFT, expand=True, padx=5)
        
        ctk.CTkButton(
            button_frame, 
            text="Delete Selected Group",
            command=delete_selected_group,
            fg_color="red",
            hover_color="#8B0000"
        ).pack(side=tk.LEFT, expand=True, padx=5)
        
        # Initialize groups display
        update_groups_display()

    def add_employee(self):
        values = {k: v.get().strip() for k, v in self.entries.items()}
        
        if not all(values.values()):
            messagebox.showerror("Error", "All fields are required")
            return
        
        for field, value in values.items():
            if len(value) > 100:
                messagebox.showerror("Error", f"{field} must be less than 100 characters")
                return
        
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as c:
                    c.execute("SELECT COUNT(*) FROM employees")
                    current_count=c.fetchone()[0]
                    employee_limit=EmployeeLimitConfig.get_employee_limit()
                    if current_count>=employee_limit:
                        messagebox.showerror("Error", f"Employee limit ({employee_limit}) reached. Cannot add more employees. Please contact your administrator to increase the limit.")
                        return
                    else:
                        c.execute("""INSERT INTO employees 
                                (name, user_id, password, designation, software_authority)
                                VALUES (%s, %s, %s, %s, %s)""", 
                                (values['name'], values['user_id'], values['password'],
                                values['designation'], values['authority']))
                conn.commit()
            messagebox.showinfo("Success", "Employee added successfully")
            self.show_main_menu()
        except pymysql.err.IntegrityError:
            messagebox.showerror("Error", "User ID already exists")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    
    def show_employees(self):
        self.clear_frame()
        ctk.CTkButton(self.main_frame, text="<< Back", 
                    command=self.show_main_menu).pack(pady=10)
        
        # Get the current user's authority
        user = User.get_instance()
        is_developer = user.get_software_authority().lower() == "developer"

        # Create frame for the treeview
        tree_frame = ctk.CTkFrame(self.main_frame)
        tree_frame.pack(pady=10, fill='both', expand=True)
        
        # Define columns based on user authority
        if is_developer:
            columns = ("Row ID", "Name", "User ID", "Password", "Designation", "Authority")
        else:
            columns = ("Row ID", "Name", "User ID", "Designation", "Authority")
        
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as c:
                    if is_developer:
                        # Fetch all columns including password for developers
                        c.execute("""SELECT row_id, name, user_id, password, 
                                    designation, software_authority FROM employees 
                                    WHERE designation != 'Developer' 
                                    ORDER BY row_id""")
                    else:
                        # Fetch all columns except password for non-developers
                        c.execute("""SELECT row_id, name, user_id, 
                                    designation, software_authority FROM employees 
                                    WHERE designation != 'Developer' 
                                    ORDER BY row_id""")
                    for row in c.fetchall():
                        tree.insert("", tk.END, values=row)
        except Error as e:
            messagebox.showerror("Error", str(e))
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        x_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        y_scrollbar.pack(side='right', fill='y')
        x_scrollbar.pack(side='bottom', fill='x')
        tree.pack(fill='both', expand=True)
        
        # Button frame
        btn_frame = ctk.CTkFrame(self.main_frame)
        btn_frame.pack(pady=10)
        
        # Add "Delete" button
        ctk.CTkButton(btn_frame, text="Delete", 
                    command=lambda: self.delete_employee(tree)).pack(side=tk.LEFT, padx=5)
        
        # Add "Edit" button
        ctk.CTkButton(btn_frame, text="Edit", 
                    command=lambda: self.edit_employee(tree)).pack(side=tk.LEFT, padx=5)
        
        # Add "Download Excel" button
        ctk.CTkButton(btn_frame, text="📥 Download Excel", 
                    command=self.download_employee_excel).pack(side=tk.LEFT, padx=5)
            
    def delete_employee(self, tree):
        if User.get_instance().get_software_authority().lower() not in ["developer","dev"]:
            messagebox.showerror("Error, Manager cannot delete data" )
            return False
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an employee")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected employee?"):
            try:
                user_id = tree.item(selection[0])['values'][2]
                with self.db.get_connection() as conn:
                    with conn.cursor() as c:
                        c.execute("DELETE FROM employees WHERE user_id = %s", (user_id,))
                    conn.commit()
                tree.delete(selection[0])
                messagebox.showinfo("Success", "Employee deleted")
            except Error as e:
                messagebox.showerror("Error", str(e))
                    
    def edit_employee(self, tree):
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an employee")
            return
        
        values = tree.item(selection[0])['values']
        #print("Values from Treeview:", values)  # Debugging line
        self.show_edit_form(values)

    def download_employee_excel(self):
        try:
            # Check if the current user is a developer
            user = User.get_instance()
            is_developer = user.get_software_authority().lower() == "developer" 

            # If the user is a developer, prompt for password
            include_passwords = False
            if is_developer:
                include_passwords = True


            # Fetch employee data from the database
            with self.db.get_connection() as conn:
                with conn.cursor() as c:
                    if include_passwords:
                        # Fetch all columns including passwords
                        c.execute("""
                            SELECT row_id, name, user_id, password, designation, software_authority 
                            FROM employees 
                            WHERE software_authority != 'Developer'
                            ORDER BY row_id
                        """)
                        columns = ["Row ID", "Name", "User ID", "Password", "Designation", "Authority"]
                    else:
                        # Fetch all columns except passwords
                        c.execute("""
                            SELECT row_id, name, user_id, designation, software_authority 
                            FROM employees 
                            WHERE software_authority != 'Developer'
                            ORDER BY row_id
                        """)
                        columns = ["Row ID", "Name", "User ID", "Designation", "Authority"]

                    records = c.fetchall()

            # Convert records to a DataFrame
            df = pd.DataFrame(records, columns=columns)

            # Save to Excel
            file_path = tk.filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")]
            )
            if file_path:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Success", "Employee data exported to Excel successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export employee data: {str(e)}")

    def upload_work_logs_excel(self):

        try:
            print("[DEBUG] Opening file dialog...")
            file_path = tk.filedialog.askopenfilename(
                filetypes=[("Excel Files", "*.xlsx *.xls")]
            )
            print(f"[DEBUG] Selected file: {file_path}")
            if not file_path:
                print("[DEBUG] No file selected.")
                return

            try:
                print("[DEBUG] Reading Excel file...")
                data = pd.read_excel(file_path)
                print("[DEBUG] Excel file read successfully.")
                print(f"[DEBUG] First few rows of data:\n{data.head()}")  # Print first few rows for debugging
            except Exception as e:
                print(f"[DEBUG] Error reading Excel file: {str(e)}")
                messagebox.showerror("Error", f"Failed to read Excel file: {str(e)}")
                return

            # Validate columns
            expected_columns = ['User Name', 'User ID', 'Date', 'SO Number', 'Start Time', 'End Time', 'Work Time', 'Work Type', 'Details of Work', 'Remarks', 'Work Time Type']
            if not all(column in data.columns for column in expected_columns):
                print("[DEBUG] Invalid Excel format. Columns do not match the schema.")
                print(f"[DEBUG] Columns found: {data.columns.tolist()}")
                messagebox.showerror("Error", "Invalid Excel format. Columns do not match the schema.")
                return
            
            print("[DEBUG] Replacing NaN values with None...")
            data = data.where(pd.notnull(data), None)  # Replace NaN with None
            print(f"[DEBUG] Data after replacing NaN:\n{data.head()}")  # Print first few rows after replacing NaN

            # Check for missing user_ids
            missing_user_ids = []
            print("[DEBUG] Checking for missing user_ids in the employees table...")
            with self.db.get_connection() as conn:
                with conn.cursor() as c:
                    for index, row in data.iterrows():
                        user_id = row['User ID']
                        print(f"[DEBUG] Checking user_id: {user_id} (Row {index + 1})")
                        c.execute("SELECT COUNT(*) FROM employees WHERE user_id = %s", (user_id,))
                        if c.fetchone()[0] == 0:
                            print(f"[DEBUG] Missing user_id: {user_id}")
                            missing_user_ids.append(user_id)

            if missing_user_ids:
                print(f"[DEBUG] Missing user_ids: {missing_user_ids}")
                messagebox.showerror("Error", f"The following user_ids are missing in the employees table: {', '.join(missing_user_ids)}")
                return

            # Process the file
            print("[DEBUG] Processing the file and inserting data into the work_logs table...")
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as c:
                        for index, row in data.iterrows():
                            print(f"[DEBUG] Processing row {index + 1}...")
                            # Map Excel columns to work_logs table fields
                            log_data = {
                                'user_id': row['User ID'],
                                'log_date': row['Date'].date() if isinstance(row['Date'], pd.Timestamp) else row['Date'],
                                'so_number': row['SO Number'],
                                'work_category': row['Work Type'],
                                'details_of_work': row['Details of Work'],
                                'remarks': row['Remarks'],
                                'time_category': row['Work Time Type'],
                                'work_hours': float(row['Work Time']),
                                'start_time': row['Start Time'].time() if isinstance(row['Start Time'], pd.Timestamp) else row['Start Time'],
                                'end_time': row['End Time'].time() if isinstance(row['End Time'], pd.Timestamp) else row['End Time']
                            }

                            print(f"[DEBUG] Inserting data for user_id: {log_data['user_id']}")
                            print(f"[DEBUG] Data to insert: {log_data}")
                            # Insert the data into the work_logs table
                            c.execute("""
                                INSERT INTO work_logs (user_id, log_date, so_number, work_category, details_of_work, remarks, time_category, work_hours, start_time, end_time)
                                VALUES (%(user_id)s, %(log_date)s, %(so_number)s, %(work_category)s, %(details_of_work)s, %(remarks)s, %(time_category)s, %(work_hours)s, %(start_time)s, %(end_time)s)
                            """, log_data)
                        print("[DEBUG] Committing changes to the database...")
                        conn.commit()
                print("[DEBUG] Data uploaded successfully!")
                messagebox.showinfo("Success", "Data uploaded successfully!")
            except Exception as e:
                print(f"[DEBUG] Database error: {str(e)}")
                messagebox.showerror("Error", f"Database error: {str(e)}")
                conn.rollback()
        except Exception as e:
            print(f"[DEBUG] Unexpected error: {str(e)}")
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")

    def show_edit_form(self, values):
        self.clear_frame()
        if len(values) < 5:  # Ensure there are at least 5 elements (row_id, name, user_id, designation, authority)
            messagebox.showerror("Error", "Insufficient data to edit employee.")
            return

        # Get the current user's authority
        user = User.get_instance()
        is_developer = user.get_software_authority().lower() == "developer"

        # Fetch the existing password from the database if the user is a developer
        existing_password = ""
        if is_developer:
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as c:
                        c.execute("SELECT password FROM employees WHERE user_id = %s", (values[2],))  # user_id is at index 2
                        result = c.fetchone()
                        if result:
                            existing_password = result[0]
            except Exception as e:
                messagebox.showerror("Error", f"Failed to fetch password: {str(e)}")

        fields = [
            ("Name", "name", values[1]),  # Name is at index 1
            ("User ID", "user_id", values[2]),  # User ID is at index 2
        ]

        # Add password field only if the current user is a Developer
        if is_developer:
            fields.append(("Password", "password", existing_password))  # Populate with existing password

        self.edit_entries = {}
        
        # Back Button
        ctk.CTkButton(self.main_frame, text="<< Back", 
                    command=self.show_employees).pack(pady=10)
        
        # Add fields for editing employee details
        for label, key, value in fields:
            frame = ctk.CTkFrame(self.main_frame)
            frame.pack(pady=5, fill='x', padx=20)
            ctk.CTkLabel(frame, text=label).pack(side=tk.LEFT, padx=5)
            self.edit_entries[key] = ctk.CTkEntry(frame, width=400)
            self.edit_entries[key].insert(0, value)
            self.edit_entries[key].pack(side=tk.LEFT, padx=5, fill='x', expand=True)
            if key == "user_id":
                self.edit_entries[key].configure(state="disabled")  # Disable editing of user_id
        
        # Add comboboxes for designation and authority
        self.edit_entries['designation'] = self.add_combobox("Designation", 
                                                            'designation', values[3])  # Designation is at index 3
        self.edit_entries['authority'] = self.add_combobox("Software Authority", 
                                                            'software_authority', 
                                                            values[4])  # Authority is at index 4
        
        # Save Button
        save_button_frame = ctk.CTkFrame(self.main_frame)
        save_button_frame.pack(pady=20, fill='x', padx=20)
        ctk.CTkButton(
            save_button_frame,
            text="💾 Save Changes",
            command=lambda: self.save_changes(values[2]),  # Pass user_id to save_changes
            width=200,
            height=40
        ).pack()


    def save_changes(self, user_id):
        values = {k: v.get().strip() for k, v in self.edit_entries.items()}
        
        if not all(values.values()):
            messagebox.showerror("Error", "All fields are required")
            return
        
        for field, value in values.items():
            if len(value) > 100:
                messagebox.showerror("Error", f"{field} must be less than 100 characters")
                return
        
        # Get the current user's authority
        user = User.get_instance()
        is_developer = user.get_software_authority().lower() == "developer"

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as c:
                    if is_developer:
                        # Update all fields, including password (only if provided)
                        if values['password']:  # Only update password if it's not empty
                            c.execute("""UPDATE employees 
                                    SET name = %s, password = %s, 
                                    designation = %s, software_authority = %s
                                    WHERE user_id = %s AND
                                    designation != 'Developer' """ , 
                                    (values['name'], values['password'],
                                    values['designation'], values['authority'],
                                    user_id))
                        else:
                            # Update all fields except password
                            c.execute("""UPDATE employees 
                                    SET name = %s, 
                                    designation = %s, software_authority = %s
                                    WHERE user_id = %s AND
                                    designation != 'Developer' """ , 
                                    (values['name'],
                                    values['designation'], values['authority'],
                                    user_id))
                    else:
                        # Update all fields except password
                        c.execute("""UPDATE employees 
                                SET name = %s, 
                                designation = %s, software_authority = %s
                                WHERE user_id = %s AND
                                designation != 'Developer' """ , 
                                (values['name'],
                                values['designation'], values['authority'],
                                user_id))
                    conn.commit()
            messagebox.showinfo("Success", "Changes saved successfully")
            self.show_employees()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def add_combobox(self, label, option_type, default_value=None):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(pady=5)
        ctk.CTkLabel(frame, text=label).pack(side=tk.LEFT, padx=5)
        combo = ctk.CTkComboBox(frame, values=self.get_options(option_type), 
                               width=400)
        if default_value:
            combo.set(default_value)
        combo.pack(side=tk.LEFT, padx=5)
        return combo
    
    def get_options(self, option_type):
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as c:
                    if option_type == 'designation':
                        c.execute("SELECT designation FROM designations")
                    elif option_type == 'software_authority':
                        c.execute("SELECT software_authority FROM software_authority")  # Corrected table name
                    return [row[0] for row in c.fetchall()]
        except Error as e:
            messagebox.showerror("Error", f"Failed to fetch options: {str(e)}")
            return []
    
    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def run(self):
        if isinstance(self.window, ctk.CTk):
            self.window.mainloop()

def manageFunction():
    app = ManagementApp()
    app.run()

if __name__ == "__main__":
    manageFunction()


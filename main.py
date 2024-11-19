#main
import os
import customtkinter as ctk
from PIL import Image
import subprocess
from tkinter import messagebox
from login import LoginApp, User
from new import NewRecordForm
from developer_mode import EmployeeLimitConfig, DeveloperSettings
import config

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class MainWindow:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.geometry("1400x950")
        self.app.resizable(True, True)
        self.app.title("TIME TRACKER - MIXION")
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.images = {}
        self.button_images = {}
        self.setup_ui()

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.app.destroy()
            self.app.quit()

    def logout(self):
        if messagebox.askokcancel("Logout", "Are you sure you want to logout?"):
            self.app.destroy()
            login_app = LoginApp(run_main_app)
            login_app.mainloop()

    def setup_ui(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Background
        try:
            self.images['background'] = ctk.CTkImage(
                light_image=Image.open(os.path.join(current_dir, "assets", "bg1.png")),
                dark_image=Image.open(os.path.join(current_dir, "assets", "bg1.png")),
                size=(1380, 930)
            )
            background_label = ctk.CTkLabel(self.app, image=self.images['background'], text="")
            background_label.place(relx=0.5, rely=0.5, anchor="center")
        except FileNotFoundError:
            messagebox.showerror("Error", "Background image not found")

        # Title
        title_label = ctk.CTkLabel(self.app, text="TIME TRACKER", font=("Arial", 20, "bold"), text_color="#0075C9",bg_color="white")
        title_label.place(relx=0.45, rely=0.15, anchor="center")

        title2_label = ctk.CTkLabel(self.app, text="-MIXION", font=("Arial", 20, "bold"), text_color="#194E83",bg_color="white")
        title2_label.place(relx=0.55, rely=0.15, anchor="center")

        # Add user details in top right
        user = User.get_instance()
        user_frame = ctk.CTkFrame(self.app, fg_color="#003057",bg_color="#003057")
        user_frame.place(relx=0.99, rely=0.0748, anchor="e")

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
            text=f"authority: {user.get_software_authority()}",
            font=("Arial", 14, "bold"),
            text_color="#0075C9"
        )
        software_authority.pack(anchor="e")
        logout_frame = ctk.CTkFrame(user_frame, fg_color="transparent")
        logout_frame.pack(anchor="e", pady=(10, 0))

        logout_button = ctk.CTkButton(
            logout_frame,

        # Logout button
            text="Logout",
            font=("Arial", 12),
            fg_color="red",
            hover_color="darkred",
            width=80,
            command=self.logout
        )
        logout_button.pack()

        # Developer Mode Button (Top Left)
        developer_button = ctk.CTkButton(
            self.app,
            text="D",
            font=("Arial", 12),
            fg_color="#194E83",
            bg_color="#0075C9",
            hover_color="gray",
            width=10,
            command=self.developer_function
        )
        developer_button.place(relx=0.009, rely=0.97, anchor="w")

        # Buttons (Main Functionality)
        button_configs = [
            ("NEW", "assets/new.png", "#0075C9", 0.25, self.new_function),
            ("RECORD", "assets/view.png", "#0075C9", 0.45, self.record_function),
            ("ANALYTICS", "assets/ana.png", "#003057", 0.65, self.analytics_function),
            ("MANAGE", "assets/Set.png", "#003057", 0.85, self.manage_function),
        ]

        for text, img_name, color, y_pos, command in button_configs:
            self.create_button(text, img_name, color, y_pos, command)

        # Info Button (Bottom Right)
        info_button = ctk.CTkButton(
            self.app,
            text="i",
            font=("Arial", 12),
             fg_color="#194E83",
            bg_color="#0075C9",
            hover_color="gray",
            width=10,
            command=self.toggle_info_section
        )
        info_button.place(relx=0.03, rely=0.97, anchor="w")

        # Info Section Frame (Initially Hidden)
        self.info_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        self.info_frame.place(relx=0.95, rely=0.85, anchor="se")  # Adjust rely to position above the button
        self.info_frame.place_forget()  # Hide the frame initially

        self.info_text = ctk.CTkTextbox(self.info_frame, width=300, height=100, wrap="word")
        self.info_text.pack()

        self.load_info_text()

        # Close Button (Always Visible)
        close_button = ctk.CTkButton(
            self.info_frame,
            text="Close",
            font=("Arial", 12),
            fg_color="red",
            hover_color="darkred",
            width=80,
            command=self.toggle_info_section
        )
        close_button.pack(pady=(10, 0))

        if self.check_developer():
            save_button = ctk.CTkButton(
                self.info_frame,
                text="Save",
                font=("Arial", 12),
                fg_color="green",
                hover_color="darkgreen",
                width=80,
                command=self.save_info_text
            )
            save_button.pack(pady=(10, 0))

    def create_button(self, text, image_name, color, y_pos, command):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.button_images[text] = ctk.CTkImage(Image.open(os.path.join(current_dir, image_name)), size=(100, 100))

        button = ctk.CTkButton(
            self.app,
            image=self.button_images[text],
            text="",
            width=100,
            height=100,
            border_width=4,
            border_color=color,
            fg_color="black",
            hover_color="WHITE",
            corner_radius=6,
            command=command
        )
        button.place(relx=0.45, rely=y_pos, anchor="center")

        label = ctk.CTkLabel(self.app, text=text, font=("Arial", 16, "bold"), text_color=color)
        label.place(relx=0.52, rely=y_pos, anchor="w")

    def check_authorization(self):
        if User.get_instance().get_user_id() == config.MasterId:
            return True

        software_authority = User.get_instance().get_software_authority().lower()
        designation = User.get_instance().get_designation().lower()

        required_designations = {'manager', 'administrator', 'manager', 'developer', 'dev'}
        required_software_authority = {'admin', 'developer', 'dev'}

        print(f"software_authority : {software_authority}")
        print(f"designation : {designation}")
        if software_authority not in required_software_authority or designation not in required_designations:
            messagebox.showerror("Access Denied", "You don't have permission to access this feature. Contact Manager")
            return False
        else:
            return True

    def check_developer(self):
        software_authority = User.get_instance().get_software_authority().lower()
        return software_authority in {'developer', 'dev'}

    def toggle_info_section(self):
        if self.info_frame.winfo_ismapped():
            self.info_frame.place_forget()  # Hide the info section
        else:
            self.info_frame.place(relx=0.95, rely=0.85, anchor="se")  # Show the info section

    def load_info_text(self):
        try:
            with open("info.txt", "r") as file:
                content = file.read()
                self.info_text.delete("1.0", "end")  # Clear existing text
                self.info_text.insert("1.0", content)
        except FileNotFoundError:
            self.info_text.insert("1.0", "No info available.")

        if not self.check_developer():
            self.info_text.configure(state="disabled")  # Make it read-only for non-developers

    def save_info_text(self):
        content = self.info_text.get("1.0", "end-1c")
        with open("info.txt", "w") as file:
            file.write(content)
        messagebox.showinfo("Info Saved", "The info has been saved successfully.")

    def new_function(self):
        new_record_app = NewRecordForm(parent=self.app)
        new_record_app.run()

    def record_function(self):
        from record import RecordViewer
        record_app = RecordViewer(parent=self.app)
        record_app.run()

    def analytics_function(self):
        if self.check_authorization():
            from analytics import TimeTrackerAnalytics

            analytics_app = TimeTrackerAnalytics(parent=self.app)
            analytics_app.run()

    def manage_function(self):
        if self.check_authorization():
            from manage import ManagementApp
            # manageFunction()
            self.app.withdraw()  # Hide the main window
            manage_app = ManagementApp(parent=self.app)
            manage_app.run()
            self.app.deiconify()  # Restore the main window after closing manage

    def developer_function(self):
        from developer_mode import DeveloperSettings
        if self.check_authorization():
            software_authority = User.get_instance().get_software_authority().lower()
            developer_software_authority = {'developer', 'dev'}
            if software_authority not in developer_software_authority:
                messagebox.showerror("Access Denied", "Only developers can access this feature")
                return
            dev_settings = DeveloperSettings(self.app)

    def run(self):
        self.app.mainloop()

def run_main_app():
    main_window = MainWindow()
    main_window.run()

# Call this before your main application starts
EmployeeLimitConfig.initialize_config()

if __name__ == "__main__":
    login_app = LoginApp(run_main_app)
    login_app.mainloop()

# Call this after your main application ends. this made for the time calcuating the time is taken to the employess to do perticuler work


# import os
# import customtkinter as ctk
# from PIL import Image
# import subprocess
# from tkinter import messagebox
# from login import LoginApp, User
# from new import NewRecordForm
# from developer_mode import EmployeeLimitConfig, DeveloperSettings
# import config

# ctk.set_appearance_mode("System")
# ctk.set_default_color_theme("blue")

# class MainWindow:
#     def __init__(self):
#         self.app = ctk.CTk()
#         self.app.geometry("1400x950")
#         self.app.resizable(True,True)
#         self.app.title("TIME TRACKER - MIXION")
#         self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
#         self.images = {}
#         self.button_images = {}
#         self.setup_ui()

#     def on_closing(self):
#         if messagebox.askokcancel("Quit", "Do you want to quit?"):
#             self.app.destroy()
#             self.app.quit()

#     def logout(self):
#         if messagebox.askokcancel("Logout", "Are you sure you want to logout?"):
#             self.app.destroy()
#             login_app = LoginApp(run_main_app)
#             login_app.mainloop()

#     def setup_ui(self):
#         current_dir = os.path.dirname(os.path.abspath(__file__))

#         # Background
#         try:
#             self.images['background'] = ctk.CTkImage(
#                 light_image=Image.open(os.path.join(current_dir, "assets", "bg1.png")),
#                 dark_image=Image.open(os.path.join(current_dir, "assets", "bg1.png")),
#                 size=(1380, 930)
#             )
#             background_label = ctk.CTkLabel(self.app, image=self.images['background'], text="")
#             background_label.place(relx=0.5, rely=0.5, anchor="center")
#         except FileNotFoundError:
#             messagebox.showerror("Error", "Background image not found")

#         # Title
#         title_label = ctk.CTkLabel(self.app, text="TIME TRACKER", font=("Arial", 20, "bold"), text_color="#0075C9",bg_color="white")
#         title_label.place(relx=0.45, rely=0.15, anchor="center")

#         title2_label = ctk.CTkLabel(self.app, text="-MIXION", font=("Arial", 20, "bold"), text_color="#194E83",bg_color="white")
#         title2_label.place(relx=0.55, rely=0.15, anchor="center")

#         # Add user details in top right
#         user = User.get_instance()
#         user_frame = ctk.CTkFrame(self.app, fg_color="#003057",bg_color="#003057")
#         user_frame.place(relx=0.99, rely=0.0748, anchor="e")

#         user_name = ctk.CTkLabel(
#             user_frame,
#             text=f"Name: {user.get_username()}",
#             font=("Arial", 14, "bold"),
#             text_color="#0075C9"
#         )
#         user_name.pack(anchor="e")

#         designation = ctk.CTkLabel(
#             user_frame,
#             text=f"designation: {user.get_designation()}",
#             font=("Arial", 14, "bold"),
#             text_color="#0075C9"
#         )
#         designation.pack(anchor="e")

#         software_authority = ctk.CTkLabel(
#             user_frame,
#             text=f"authority: {user.get_software_authority()}",
#             font=("Arial", 14, "bold"),
#             text_color="#0075C9"
#         )
#         software_authority.pack(anchor="e")
#         logout_frame = ctk.CTkFrame(user_frame, fg_color="transparent")
#         logout_frame.pack(anchor="e", pady=(10, 0))

#         logout_button = ctk.CTkButton(
#             logout_frame,

#         # Logout button
#             text="Logout",
#             font=("Arial", 12),
#             fg_color="red",
#             hover_color="darkred",
#             width=80,
#             command=self.logout
#         )
#         logout_button.pack()

#         # Developer Mode Button (Top Left)
#         developer_button = ctk.CTkButton(
#             self.app,
#             text="D",
#             font=("Arial", 12),
#             fg_color="#194E83",
#             bg_color="#0075C9",
#             hover_color="gray",
#             width=10,
#             command=self.developer_function
#         )
#         developer_button.place(relx=0.009, rely=0.97, anchor="w")

#         # Buttons (Main Functionality)
#         button_configs = [
#             ("NEW", "assets/new.png", "#0075C9", 0.25, self.new_function),
#             ("RECORD", "assets/view.png", "#0075C9", 0.45, self.record_function),
#             ("ANALYTICS", "assets/ana.png", "#003057", 0.65, self.analytics_function),
#             ("MANAGE", "assets/Set.png", "#003057", 0.85, self.manage_function),
#         ]

#         for text, img_name, color, y_pos, command in button_configs:
#             self.create_button(text, img_name, color, y_pos, command)

#         # Info Button (Bottom Right)
#         info_button = ctk.CTkButton(
#             self.app,
#             text="i",
#             font=("Arial", 12),
#              fg_color="#194E83",
#             bg_color="#0075C9",
#             hover_color="gray",
#             width=10,
#             command=self.toggle_info_section
#         )
#         info_button.place(relx=0.03, rely=0.97, anchor="w")

#         # Info Section Frame (Initially Hidden)
#         self.info_frame = ctk.CTkFrame(self.app, fg_color="transparent")
#         self.info_frame.place(relx=0.95, rely=0.85, anchor="se")  # Adjust rely to position above the button
#         self.info_frame.place_forget()  # Hide the frame initially

#         self.info_text = ctk.CTkTextbox(self.info_frame, width=300, height=100, wrap="word")
#         self.info_text.pack()

#         self.load_info_text()

#         # Close Button (Always Visible)
#         close_button = ctk.CTkButton(
#             self.info_frame,
#             text="Close",
#             font=("Arial", 12),
#             fg_color="red",
#             hover_color="darkred",
#             width=80,
#             command=self.toggle_info_section
#         )
#         close_button.pack(pady=(10, 0))

#         if self.check_developer():
#             save_button = ctk.CTkButton(
#                 self.info_frame,
#                 text="Save",
#                 font=("Arial", 12),
#                 fg_color="green",
#                 hover_color="darkgreen",
#                 width=80,
#                 command=self.save_info_text
#             )
#             save_button.pack(pady=(10, 0))

#     def create_button(self, text, image_name, color, y_pos, command):
#         current_dir = os.path.dirname(os.path.abspath(__file__))
#         self.button_images[text] = ctk.CTkImage(Image.open(os.path.join(current_dir, image_name)), size=(100, 100))

#         button = ctk.CTkButton(
#             self.app,
#             image=self.button_images[text],
#             text="",
#             width=100,
#             height=100,
#             border_width=4,
#             border_color=color,
#             fg_color="black",
#             hover_color="WHITE",
#             corner_radius=6,
#             command=command
#         )
#         button.place(relx=0.45, rely=y_pos, anchor="center")

#         label = ctk.CTkLabel(self.app, text=text, font=("Arial", 16, "bold"), text_color=color)
#         label.place(relx=0.52, rely=y_pos, anchor="w")

#     def check_authorization(self):
#         if User.get_instance().get_user_id() == config.MasterId:
#             return True

#         software_authority = User.get_instance().get_software_authority().lower()
#         designation = User.get_instance().get_designation().lower()

#         required_designations = {'manager', 'administrator', 'admin', 'developer', 'dev'}
#         required_software_authority = {'manager', 'administrator', 'admin', 'developer', 'dev'}

#         print(f"software_authority : {software_authority}")
#         print(f"designation : {designation}")
#         if software_authority in required_software_authority or designation in required_designations:
#             return True
#         else:
#             messagebox.showerror("Access Denied", "You don't have permission to access this feature. Contact Manager")
#             return False

#     def check_developer(self):
#         software_authority = User.get_instance().get_software_authority().lower()
#         return software_authority in {'developer', 'dev'}

#     def toggle_info_section(self):
#         if self.info_frame.winfo_ismapped():
#             self.info_frame.place_forget()  # Hide the info section
#         else:
#             self.info_frame.place(relx=0.95, rely=0.85, anchor="se")  # Show the info section

#     def load_info_text(self):
#         try:
#             with open("info.txt", "r") as file:
#                 content = file.read()
#                 self.info_text.delete("1.0", "end")  # Clear existing text
#                 self.info_text.insert("1.0", content)
#         except FileNotFoundError:
#             self.info_text.insert("1.0", "No info available.")

#         if not self.check_developer():
#             self.info_text.configure(state="disabled")  # Make it read-only for non-developers

#     def save_info_text(self):
#         content = self.info_text.get("1.0", "end-1c")
#         with open("info.txt", "w") as file:
#             file.write(content)
#         messagebox.showinfo("Info Saved", "The info has been saved successfully.")

#     def new_function(self):
#         new_record_app = NewRecordForm(parent=self.app)
#         new_record_app.run()

#     def record_function(self):
#         from record import RecordViewer
#         record_app = RecordViewer(parent=self.app)
#         record_app.run()

#     def analytics_function(self):
#         if self.check_authorization():
#             from analytics import TimeTrackerAnalytics

#             analytics_app = TimeTrackerAnalytics(parent=self.app)
#             analytics_app.run()

#     def manage_function(self):
#         if self.check_authorization():
#             from manage import ManagementApp
#             # manageFunction()
#             self.app.withdraw()  # Hide the main window
#             manage_app = ManagementApp(parent=self.app)
#             manage_app.run()
#             self.app.deiconify()  # Restore the main window after closing manage

#     def developer_function(self):
#         from developer_mode import DeveloperSettings
#         if self.check_authorization():
#             software_authority = User.get_instance().get_software_authority().lower()
#             developer_software_authority = {'developer', 'dev'}
#             if software_authority not in developer_software_authority:
#                 messagebox.showerror("Access Denied", "Only developers can access this feature")
#                 return
#             dev_settings = DeveloperSettings(self.app)

#     def run(self):
#         self.app.mainloop()

# def run_main_app():
#     main_window = MainWindow()
#     main_window.run()

# # Call this before your main application starts
# EmployeeLimitConfig.initialize_config()

# if __name__ == "__main__":
#     login_app = LoginApp(run_main_app)
#     login_app.mainloop()

# # Call this after your main application ends. this made for the time calcuating the time is taken to the employess to do perticuler work
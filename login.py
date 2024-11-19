import os
import customtkinter as ctk
from PIL import Image, ImageTk
import pymysql
from tkinter import messagebox
from config import DATABASE_CONFIG
import config

class User:
    _instance = None
    
    def __init__(self):
        self.user_id = None
        self.user_name=None
        self.software_authority = None
        self.designation=None
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = User()
        return cls._instance
    
    def set_user(self, user_id, user_name,software_authority,designation):
        self.user_id = user_id
        self.user_name=user_name
        # self.password=password
        self.software_authority = software_authority
        self.designation=designation
        
    def get_software_authority(self):
        return self.software_authority
    
    def get_designation(self):
        return self.designation
        
    def get_user_id(self):
        return self.user_id
    
    def get_username(self):  # New method to get username
        return self.user_name
    
    # def get_password(self):  # New method to get password
    #     return self.password
    
    def clear(self):
        self.user_id = None
        self.username = None
        self.software_authority = None


class Database:
    @staticmethod
    def get_connection():
        try:
            return pymysql.connect( **DATABASE_CONFIG)
            
        except pymysql.Error as e:
            messagebox.showerror("Database Error", f"Could not connect to database: {str(e)}")
            return None

class LoginApp(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        
        self.title("Login - Time Tracker")
        self.geometry("1600x900")
        self.resizable(True, True)
        
        self.setup_ui()
        
    def setup_ui(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            # Load images
            bg_image = Image.open(os.path.join(script_dir,"assets", "lp.png"))
            # logo_image = Image.open(os.path.join(script_dir,"assets", "LOGO.png"))
        
        except FileNotFoundError as e:
            messagebox.showerror("Error", f"Required image files not found: str(e)")

        bg_photo = ImageTk.PhotoImage(bg_image.resize((1600, 900)))
        # logo_photo = ImageTk.PhotoImage(logo_image.resize((50, 50)))
        
        # Place images
        self.bg_label = ctk.CTkLabel(self, image=bg_photo, text="")
        self.bg_label.place(x=5, y=5)
        self.bg_label.image = bg_photo
        
        # self.logo_label = ctk.CTkLabel(self, image=logo_photo, text="")
        # self.logo_label.place(x=410, y=315)
        # self.logo_label.image = logo_photo
        
        # Login form
        self.title_label = ctk.CTkLabel(self, text="TIME TRACKER LOGIN", font=("Arial", 18, "bold"))
        self.title_label.pack(pady=20)
        
        self.user_id_entry = ctk.CTkEntry(self, placeholder_text="User ID")
        self.user_id_entry.pack(pady=10)
        
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10)
        
        self.login_button = ctk.CTkButton(self, text="Login", command=self.handle_login)
        self.login_button.pack(pady=20)
        
        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.pack()
        
    def handle_login(self):
        user_id = self.user_id_entry.get()
        password = self.password_entry.get()

        if user_id == config.MasterId and password == config.MasterPassword:
            User.get_instance().set_user(user_id, "Master-Developer", "Developer", "Developer")
            self.destroy()
            self.on_login_success()
            return

        
        conn = Database.get_connection()
        if not conn:
            return
            
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT name, password, software_authority, designation FROM employees WHERE user_id = %s', (user_id,))
            result = cursor.fetchone()
            
            user_name=result[0]
            software_authority=result[2]
            designation=result[3]

            if result and result[1] == password:
                User.get_instance().set_user(user_id, user_name, software_authority, designation)
                self.destroy()
                self.on_login_success()
            else:
                self.error_label.configure(text="Invalid credentials")
                
        except Exception as e:
            self.error_label.configure(text=f"Login error: {str(e)}")
        finally:
            conn.close()

if __name__ == "__main__":
    def dummy_callback():
        print("Login successful")
    
    app = LoginApp(dummy_callback)
    app.mainloop()
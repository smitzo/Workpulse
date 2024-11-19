
import os
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
from fpdf import FPDF
from PIL import Image, ImageTk
from datetime import datetime, timedelta
import pymysql
import matplotlib
matplotlib.use('Agg')  # Use Agg backend for thread safety
import matplotlib.pyplot as plt
from io import BytesIO
import numpy as np
import queue
import threading
import pandas as pd
import plotly.express as px
import tempfile
import webbrowser
from config import DATABASE_CONFIG

# def analyticsFunction():
print("inside analytics function")

class DatabaseManager:
    def __init__(self):
        pass
        # self.connection_params = {
        #     'host': '127.0.0.1',
        #     'database': 'employeedb',
        #     'user': 'root',
        #     'password': 'smit2812'
        # }

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
        
    # def get_ideal_times(self):
    #     try:
    #         connection=self.get_connection()
    #         if not connection:
    #             return{}
            
    #         with connection.cursor() as cursor:
    #             cursor.execute("SELECT details_of_work, ideal_time FROM ideal_time_table")
    #             results=cursor.fetchall()
    #             return {row[0]:float( row[1]) for row in results} 
            
    #     except Exception as e:
    #         print (f"Error fetching ideal time:{e}")
    #         return {}
        
    #     finally:
    #         if  connection:
    #             connection.close()
        

class LoadingScreen(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.geometry("200x100")
        self.title("")
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

class GraphGenerator:
    @staticmethod
    def create_pie_chart(data, title):
        plt.figure(figsize=(6, 6))
        labels = list(data.keys())
        sizes = list(data.values())
        plt.pie(sizes, labels=[f"{label}\n{size:.1f} hrs" for label, size in zip(labels, sizes)], 
                autopct="%1.1f%%", startangle=140)
        plt.title(title, fontsize=12)
        
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=100)
        buffer.seek(0)
        plt.close()
        return buffer

    @staticmethod    
    def create_bar_chart(x, y, xlabel, ylabel, title):
        plt.figure(figsize=(10, 6))
        bars=plt.bar(x, y, color="skyblue")
        plt.xlabel(xlabel, fontsize=10)
        plt.ylabel(ylabel, fontsize=10)
        plt.title(title, fontsize=12)
        plt.xticks(rotation=45, fontsize=8)
        plt.yticks(fontsize=8)

        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{height:.1f} hrs',
                    ha='center', va='bottom', fontsize=8)
        
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        return buffer

    @staticmethod
    def create_multi_bar_chart(x, y_series, labels, xlabel, ylabel, title):
        plt.figure(figsize=(10, 6))
        bar_width = 0.35
        index = range(len(x))
        
        for i, (y, label) in enumerate(zip(y_series, labels)):
            plt.bar([xi + i * bar_width for xi in index], y, bar_width, label=label)
        
        plt.xlabel(xlabel, fontsize=10)
        plt.ylabel(ylabel, fontsize=10)
        plt.title(title, fontsize=12)
        plt.xticks([xi + bar_width/2 for xi in index], x, rotation=45, fontsize=8)
        plt.yticks(fontsize=8)
        plt.legend()
        
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        return buffer
    
    # @staticmethod
    # def create_comparison_bar_chart(x, actual_y, ideal_y, xlabel, ylabel, title):
    #     plt.figure(figsize=(12, 6))
        
    #     # Set width of bars and positions of the bars
    #     bar_width = 0.35
    #     x_indices = np.arange(len(x))
        
    #     # Create bars
    #     plt.bar(x_indices - bar_width/2, actual_y, bar_width, label='Actual Time', color='skyblue')
    #     plt.bar(x_indices + bar_width/2, ideal_y, bar_width, label='Ideal Time', color='lightgreen')
        
    #     # Customize the plot
    #     plt.xlabel(xlabel, fontsize=10)
    #     plt.ylabel(ylabel, fontsize=10)
    #     plt.title(title, fontsize=12)
    #     plt.xticks(x_indices, x, rotation=45, ha='right', fontsize=8)
    #     plt.yticks(fontsize=8)
    #     plt.legend()
        
    #     # Add value labels on top of bars
    #     for i, v in enumerate(actual_y):
    #         plt.text(i - bar_width/2, v, f'{v:.1f}', ha='center', va='bottom')
    #     for i, v in enumerate(ideal_y):
    #         plt.text(i + bar_width/2, v, f'{v:.1f}', ha='center', va='bottom')
        
    #     # Adjust layout
    #     plt.tight_layout()
        
    #     buffer = BytesIO()
    #     plt.savefig(buffer, format="png", dpi=100, bbox_inches='tight')
    #     buffer.seek(0)
    #     plt.close()
    #     return buffer


    @staticmethod
    def create_stacked_chart(x, y_dict, xlabel, ylabel, title):
        plt.figure(figsize=(10, 6))
        bottom = np.zeros(len(x))
        
        for label, values in y_dict.items():
            bars=plt.bar(x, values, bottom=bottom, label=label)
            bottom += np.array(values)

            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2., bar.get_y() + height / 2,
                        f'{height:.1f} hrs',
                        ha='center', va='center', fontsize=8, color='white')
        
        plt.xlabel(xlabel, fontsize=10)
        plt.ylabel(ylabel, fontsize=10)
        plt.title(title, fontsize=12)
        plt.xticks(rotation=45, fontsize=8)
        plt.yticks(fontsize=8)
        plt.legend()
        
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        return buffer

    @staticmethod
    def create_line_chart(x, y_series, labels, xlabel, ylabel, title):
        plt.figure(figsize=(10, 6))
        
        for y, label in zip(y_series, labels):
            plt.plot(x, y, marker='o', label=label)
        
        plt.xlabel(xlabel, fontsize=10)
        plt.ylabel(ylabel, fontsize=10)
        plt.title(title, fontsize=12)
        plt.xticks(rotation=45, fontsize=8)
        plt.yticks(fontsize=8)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        return buffer

class TimeTrackerAnalytics(ctk.CTkToplevel):
    def __init__(self,parent=None):
        super().__init__()
        self.parent=parent
        self.db = DatabaseManager()
        self.images={}
        self.graph_buffers=[]
        self.loading_screen=None
        self.plot_queue=queue.Queue()

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            bg_path = os.path.join(current_dir, "bg2.png")

            if os.path.exists(bg_path):
                bg_image=Image.open(bg_path)
                self.bg_image= ctk.CTkImage(light_image=bg_image,dark_image=bg_image, size=(1600, 900))
        except Exception as e:
            print(f"Error loading Background image:{e}")

        self.grab_set()  
        self.after(100,self.setup_main_window())
        self.after(100,self.setup_ui_components())
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Handle window closing"""
        self.cleanup_plots()
        self.grab_release()
        if self.parent:
            self.parent.deiconify()  # Show the main window
        self.destroy()
        
    def run(self):
        self.focus_force()
        # """Start the analytics window"""
        # if self.parent:
        #     self.parent.withdraw()  # Hide the main window
        # self.mainloop()
        
    def setup_main_window(self):
        self.title("Time Tracker Analytics")
        self.geometry("1400x950")
        self.resizable(True, True)
        
        if hasattr (self,'bg_image'):
            bg_label = ctk.CTkLabel(self, image=self.bg_image, text="")
            bg_label.place(relwidth=1, relheight=1)

        else :  
            self.configure(fg_color="#2b2b2b")
    
    def setup_ui_components(self):
        self.create_title()
        self.create_result_frame()
        self.create_button_frame()

        # Add back button
        self.back_button = ctk.CTkButton(
            self,
            text="← Back to Main",
            command=self.on_closing,
            width=120,
            height=30,
            font=("Arial", 12),
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        self.back_button.place(relx=0.05, rely=0.05, anchor="w")
        
        self.selection_label = ctk.CTkLabel(
            self, 
            text="", 
            font=("Arial", 12),
            text_color="white"
        )
        self.selection_label.place(relx=0.5, rely=0.85, anchor="center")
        
        self.custom_date_frame = None

    def show_loading_screen(self):
        self.loading_screen = LoadingScreen(self)
        self.loading_screen.grab_set()

    def hide_loading_screen(self):
        if self.loading_screen:
            self.loading_screen.grab_release()
            self.loading_screen.destroy()
            self.loading_screen = None

    def create_title(self):
        title_label = ctk.CTkLabel(
            self, 
            text="Time Tracker Analytics",
            font=("Arial", 24, "bold"),
            text_color="white"
        )
        title_label.place(relx=0.5, rely=0.04, anchor="center")

    def create_result_frame(self):
        self.result_frame = ctk.CTkFrame(self, width=595 * 1.7, height=842 * 0.8,fg_color="transparent")
        self.result_frame.place(relx=0.6, rely=0.5, anchor="center")
        
        self.text_box = ctk.CTkTextbox(
            self.result_frame,
            wrap="none",
            fg_color="white",
            width=595 * 1.7,
            height=842 * 0.8
        )
        self.text_box.pack(expand=True, fill="both", padx=5, pady=5)
        
        self.add_scrollbars()

    def add_scrollbars(self):
        scroll_x = ttk.Scrollbar(self.result_frame, orient="horizontal", command=self.text_box.xview)
        scroll_x.pack(side="bottom", fill="x")
        
        scroll_y = ttk.Scrollbar(self.result_frame, orient="vertical", command=self.text_box.yview)
        scroll_y.pack(side="right", fill="y")
        
        self.text_box.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

    def create_button_frame(self):
        button_frame = ctk.CTkFrame(self, width=300, height=500, fg_color="transparent")
        button_frame.place(relx=0.1, rely=0.5, anchor="center")
        
        time_periods = [
            ("Last 1 Day", self.display_last_1_day),
            ("Last 1 Week", self.display_last_1_week),
            ("Last 1 Month", self.display_last_1_month),
            ("Last 3 Months", self.display_last_3_months),
            ("Last 6 Months", self.display_last_6_months),
            ("View Sunburst Charts", self.display_sunburst_charts),
        ]
        
        for label, command in time_periods:
            btn = ctk.CTkButton(
                button_frame, 
                text=label, 
                command=command, 
                width=250,
                height=30,
                font=("Arial", 12),
                fg_color="#1f538d",
                hover_color="#14375e"
            )
            btn.pack(pady=10)
        
        self.create_utility_buttons(button_frame)

    def create_utility_buttons(self, parent):
        utility_buttons = [
            ("⏲Custom Date", self.show_custom_date, "goldenrod"),
            ("⏬ Download PDF", self.generate_pdf, "green"),
            ("↻ Reset", self.reset_display, "darkred")
        ]
        
        for label, command, color in utility_buttons:
            btn = ctk.CTkButton(
                parent,
                text=label,
                command=command,
                fg_color=color,
                hover_color=self.darken_color(color),
                width=250,
                height=50,
                font=("Arial", 12)
            )
            btn.pack(pady=10)

    @staticmethod
    def darken_color(hex_color):
        """Darken a hex color by 20%"""
        pass
        # Convert hex to RGB
        # hex_color = hex_color.lstrip('#')
        # rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        # # Darken each component by 20%
        # darkened = tuple(int(c * 0.8) for c in rgb)
        # # Convert back to hex
        # return f'#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}'

    def display_analysis(self, data):
        for widget in self.result_frame.winfo_children():
            widget.destroy()
            
        # graph_frame = ctk.CTkFrame(self.result_frame)
        # graph_frame.pack(expand=True, fill="both")
        
        canvas = tk.Canvas(self.result_frame, width=1200, height=800,bg='#2b2b2b')
        scrollbar_y = ttk.Scrollbar(self.result_frame, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(self.result_frame, orient="horizontal", command=canvas.xview)
        
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)
        
        inner_frame = tk.Frame(canvas,bg='#2b2b2b')
        canvas_window= canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        def on_mousewheel(event):
            canvas.yview_scroll(-1 * int(event.delta/120), "units")

        def on_shift_mousewheel(event):
            canvas.xview_scroll(-1 * int(event.delta/120), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)
        canvas.bind_all("<Shift-MouseWheel>", on_shift_mousewheel)
    
        # Update scroll region when inner frame changes
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        inner_frame.bind("<Configure>", configure_scroll_region)
        
        self.display_pie_charts(inner_frame, data)
        self.display_bar_charts(inner_frame, data)
        self.display_stacked_charts(inner_frame, data)
        self.display_trend_charts(inner_frame, data)
        self.display_employee_pie_charts(inner_frame,data)
        
        inner_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def display_pie_charts(self, parent_frame, data):
        pie_charts = [
            (data['work_category_counts'], "Work Category Distribution"),
            (data['details_of_work_counts'], "Details of Work Distribution"),
            (data['time_by_so_number'], "Time by SO Number"),
            (data['time_category_distribution'], "Time Category Distribution"),
            (data['user_work_distribution'], "User Work Distribution"),
            (data['work_category_by_time'], "Work Category vs Time Type")
        ]
        
        for idx, (chart_data, title) in enumerate(pie_charts):
            if chart_data:
                row = idx // 3
                col = idx % 3
                buffer = GraphGenerator.create_pie_chart(chart_data, title)
                self.display_graph_from_buffer(buffer, parent_frame, row, col)

    def display_bar_charts(self, parent_frame, data):
        start_row = 3  # Start after pie charts

    #     # Create comparison bar chart for work details
    #     details = list(data['details_work_comparison'].keys())
    #     actual_times = [data['details_work_comparison'][d]['actual_time'] for d in details]
    #     ideal_times = [data['details_work_comparison'][d]['ideal_time'] for d in details]

    #     buffer = GraphGenerator.create_comparison_bar_chart(
    #         details,
    #         actual_times,
    #         ideal_times,
    #         "Work Details",
    #         "Hours",
    #         "Actual vs Ideal Time by Work Detail"
    #         )
    #     self.display_graph_from_buffer(buffer, parent_frame, start_row, 0)   

        # Daily hours worked
        dates = list(data['hours_by_day'].keys())
        hours = list(data['hours_by_day'].values())
        buffer = GraphGenerator.create_bar_chart(
            dates,
            hours,
            "Date", "Hours",
            "Hours Worked by Day"
        )
        self.display_graph_from_buffer(buffer, parent_frame, start_row, 0)
        
        # Daily overtime vs standard
        dates = sorted(data['daily_overtime_standard'].keys())
        standard_hours = [data['daily_overtime_standard'][d]['standard'] for d in dates]
        overtime_hours = [data['daily_overtime_standard'][d]['overtime'] for d in dates]
        buffer = GraphGenerator.create_multi_bar_chart(
            dates,
            [standard_hours, overtime_hours],
            ["Standard", "Overtime"],
            "Date", "Hours",
            "Daily Standard vs Overtime Hours"
        )
        self.display_graph_from_buffer(buffer, parent_frame, start_row, 1)
        
        # User performance
        users = list(data['user_performance'].keys())
        total_hours = [data['user_performance'][u]['total'] for u in users]
        buffer = GraphGenerator.create_bar_chart(
            users,
            total_hours,
            "User ID", "Total Hours",
            "User Performance"
        )
        self.display_graph_from_buffer(buffer, parent_frame, start_row, 2)

        # Details of Work Distribution
        details_of_work = list(data['details_of_work_counts'].keys())
        hours_by_details = list(data['details_of_work_counts'].values())
        buffer = GraphGenerator.create_bar_chart(
            details_of_work,
            hours_by_details,
            "Details of Work", "Hours",
            "Details of Work Distribution"
        )
        self.display_graph_from_buffer(buffer, parent_frame, start_row + 1, 0)


    def display_stacked_charts(self, parent_frame, data):
        start_row = 6  # Start after bar charts
        
        # Stacked category by date
        dates = sorted(data['stacked_category_by_date'].keys())
        categories = list(set(cat for d in data['stacked_category_by_date'].values() for cat in d.keys()))
        values_by_category = {
            cat: [data['stacked_category_by_date'][d].get(cat, 0) for d in dates]
            for cat in categories
        }
        
        buffer = GraphGenerator.create_stacked_chart(
            dates,
            values_by_category,
            "Date", "Hours",
            "Work Categories Over Time"
        )
        self.display_graph_from_buffer(buffer, parent_frame, start_row, 0)
        
        # Stacked details by date
        dates = sorted(data['stacked_details_by_date'].keys())
        details = list(set(detail for d in data['stacked_details_by_date'].values() for detail in d.keys()))
        values_by_detail = {
            detail: [data['stacked_details_by_date'][d].get(detail, 0) for d in dates]
            for detail in details
        }
        
        buffer = GraphGenerator.create_stacked_chart(
            dates,
            values_by_detail,
            "Date", "Hours",
            "Work Details Over Time"
        )
        self.display_graph_from_buffer(buffer, parent_frame, start_row, 1)

    def display_trend_charts(self, parent_frame, data):

        start_row = 9  # Start after stacked charts
        
        # Monthly overtime trend
        months = sorted(data['monthly_overtime'].keys())
        standard_hours = [data['monthly_overtime'][m]['standard'] for m in months]
        overtime_hours = [data['monthly_overtime'][m]['overtime'] for m in months]
        
        buffer = GraphGenerator.create_line_chart(
            months,
            [standard_hours, overtime_hours],
            ["Standard", "Overtime"],
            "Month", "Hours",
            "Monthly Overtime Trends"
        )
        self.display_graph_from_buffer(buffer, parent_frame, start_row, 0)
        
        # Weekly category trends
        weeks = sorted(data['weekly_category_trends'].keys())
        categories = list(set(cat for w in data['weekly_category_trends'].values() for cat in w.keys()))
        values_by_category = {
            cat: [data['weekly_category_trends'][w].get(cat, 0) for w in weeks]
            for cat in categories
        }
        
        buffer = GraphGenerator.create_line_chart(
            weeks,
            [values_by_category[cat] for cat in categories],
            categories,
            "Week", "Hours",
            "Weekly Category Trends"
        )
        self.display_graph_from_buffer(buffer, parent_frame, start_row, 1)

    def display_graph_from_buffer(self, buffer, parent_frame, row, col):
        try:
            buffer.seek(0)
            img = Image.open(buffer)
            photo = ImageTk.PhotoImage(img)
            
            label = tk.Label(parent_frame, image=photo)
            label.image = photo
            label.grid(row=row, column=col, padx=10, pady=10)

            # Store buffer for PDF generation
            new_buffer=BytesIO(buffer.getvalue())
            self.graph_buffers.append(new_buffer)

        except Exception as e:
            print(f"Error displaying graph: {e}")

        finally:
            buffer.close()

    def get_date_range(self, days=1):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    def display_graphs(self, start_date, end_date, period_name):
        def process_data():
            self.graph_buffers=[]
            conn = self.db.get_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return
                
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT log_id, user_id, log_date, so_number, work_hours, work_category, details_of_work, remarks, time_category  FROM work_logs WHERE log_date BETWEEN %s AND %s",
                        (start_date, end_date)
                    )
                    records = cursor.fetchall()
                    
                if not records:
                    messagebox.showinfo("No Data", f"No records found for {period_name}")
                    return
                
                try:
                    self.update_selection_label(period_name, f"{start_date} to {end_date}")
                    data = self.process_work_data(records)
                    self.plot_queue.put(data)
                    self.after(0,self.process_plots)
                    #self.display_analysis(data)
                except Exception as e:
                    messagebox.showerror("Error", f"Error processing data: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Error querying database: {str(e)}")
            finally:
                conn.close()
                self.after(0, self.hide_loading_screen)

        self.show_loading_screen()
        self.graph_buffers.clear()
        thread = threading.Thread(target=process_data)
        thread.daemon = True
        thread.start()

    def process_plots(self):
        try:
            data = self.plot_queue.get_nowait()
            self.display_analysis(data)
        except queue.Empty:
            pass
        except Exception as e:
            messagebox.showerror("Error", f"Error generating plots: {str(e)}")

    

    def process_work_data(self, records):
        # ideal_times = self.db.get_ideal_times()
        data = {
            'work_category_counts': {},
            'details_of_work_counts': {},
            'time_by_so_number': {},
            'hours_by_day': {},
            'time_category_distribution': {},
            'user_work_distribution': {},
            'work_category_by_time': {},
            'daily_overtime_standard': {},
            'user_performance': {},
            'weekly_category_trends': {},
            'so_number_timeline': {},
            'work_type_by_user': {},
            'avg_daily_by_category': {},
            'monthly_overtime': {},
            'peak_hours': {},
            'stacked_category_by_date': {},
            'stacked_details_by_date': {},
            'overtime_standard_by_date': {},
            'user_workload_timeline': {},
            'employee_metrics':{},
            # 'details_work_comparison': {},  # New dictionary for actual vs ideal comparison
            # 'ideal_times': ideal_times  # Store ideal times

        }

            # Initialize employee metrics structure
        unique_employees = set(record[1] for record in records)  # user_id is at index 1
        for employee in unique_employees:
            data['employee_metrics'][employee] = {
                'work_categories': {},
                'details_of_work': {},
                'so_numbers': {},
                'time_categories': {},
                'daily_hours': {},
                'overtime_vs_standard': {'overtime': 0, 'standard': 0},
                'weekly_hours': {},
                'monthly_hours': {},
                'task_completion_time': {}
            }
        
        for record in records:
            _, user_id, log_date, so_number, time_taken, work_category, details_of_work, remarks, time_category = record


            # Normalize time category to handle different cases
            normalized_time_category = time_category.lower().strip()
            if 'over time' in normalized_time_category:
                normalized_time_category = 'overtime'
            elif 'standard' in normalized_time_category:
                normalized_time_category = 'standard'

            log_day = log_date.strftime("%Y-%m-%d")
            week_num = log_date.strftime("%Y-W%W")
            month = log_date.strftime("%Y-%m")
            
            # Basic metrics
            data['work_category_counts'][work_category] = data['work_category_counts'].get(work_category, 0) + time_taken
            data['details_of_work_counts'][details_of_work] = data['details_of_work_counts'].get(details_of_work, 0) + time_taken
            data['time_by_so_number'][so_number] = data['time_by_so_number'].get(so_number, 0) + time_taken
            data['hours_by_day'][log_day] = data['hours_by_day'].get(log_day, 0) + time_taken
            data['time_category_distribution'][time_category] = data['time_category_distribution'].get(time_category, 0) + time_taken
            data['user_work_distribution'][user_id] = data['user_work_distribution'].get(user_id, 0) + time_taken
            
            # Work category by time type
            key = f"{work_category}_{time_category}"
            data['work_category_by_time'][key] = data['work_category_by_time'].get(key, 0) + time_taken
            
            # Daily overtime vs standard
            if log_day not in data['daily_overtime_standard']:
                data['daily_overtime_standard'][log_day] = {'standard': 0, 'overtime': 0}
            data['daily_overtime_standard'][log_day][normalized_time_category] += time_taken

            # Populate details_of_work_counts
            data['details_of_work_counts'][details_of_work] = data['details_of_work_counts'].get(details_of_work, 0) + time_taken
            
            # # Add to details_work_comparison
            # if details_of_work not in data['details_work_comparison']:
            #     data['details_work_comparison'][details_of_work] = {
            #         'actual_time': 0,
            #         'ideal_time': ideal_times.get(details_of_work, 0),
            #         'count': 0
            #     }

            # data['details_work_comparison'][details_of_work]['actual_time'] += time_taken
            # data['details_work_comparison'][details_of_work]['count'] += 1
            

            # User performance tracking
            if user_id not in data['user_performance']:
                data['user_performance'][user_id] = {'total': 0, 'standard': 0, 'overtime': 0}
            data['user_performance'][user_id]['total'] += time_taken
            data['user_performance'][user_id][normalized_time_category] += time_taken
            
            # Weekly category trends
            if week_num not in data['weekly_category_trends']:
                data['weekly_category_trends'][week_num] = {}
            data['weekly_category_trends'][week_num][work_category] = \
                data['weekly_category_trends'][week_num].get(work_category, 0) + time_taken
            
            # Stacked metrics
            if log_day not in data['stacked_category_by_date']:
                data['stacked_category_by_date'][log_day] = {}
            data['stacked_category_by_date'][log_day][work_category] = \
                data['stacked_category_by_date'][log_day].get(work_category, 0) + time_taken
            
            if log_day not in data['stacked_details_by_date']:
                data['stacked_details_by_date'][log_day] = {}
            data['stacked_details_by_date'][log_day][details_of_work] = \
                data['stacked_details_by_date'][log_day].get(details_of_work, 0) + time_taken
            
            # Monthly overtime
            if month not in data['monthly_overtime']:
                data['monthly_overtime'][month] = {'standard': 0, 'overtime': 0}
            data['monthly_overtime'][month][normalized_time_category] += time_taken


            # Update employee-specific metrics
            emp_metrics = data['employee_metrics'][user_id]
            
            # Work categories for employee
            emp_metrics['work_categories'][work_category] = emp_metrics['work_categories'].get(work_category, 0) + time_taken
            
            # Details of work for employee
            emp_metrics['details_of_work'][details_of_work] = emp_metrics['details_of_work'].get(details_of_work, 0) + time_taken
            
            # SO numbers for employee
            emp_metrics['so_numbers'][so_number] = emp_metrics['so_numbers'].get(so_number, 0) + time_taken
            
            # Time categories for employee
            emp_metrics['time_categories'][time_category] = emp_metrics['time_categories'].get(time_category, 0) + time_taken
            
            # Daily hours for employee
            emp_metrics['daily_hours'][log_day] = emp_metrics['daily_hours'].get(log_day, 0) + time_taken
            
            # Overtime vs standard hours
            emp_metrics['overtime_vs_standard'][normalized_time_category] += time_taken
            
            # Weekly hours
            if week_num not in emp_metrics['weekly_hours']:
                emp_metrics['weekly_hours'][week_num] = 0
            emp_metrics['weekly_hours'][week_num] += time_taken
            
            # Monthly hours
            if month not in emp_metrics['monthly_hours']:
                emp_metrics['monthly_hours'][month] = 0
            emp_metrics['monthly_hours'][month] += time_taken
            
            # Task completion time
            task_key = f"{work_category}-{details_of_work}"
            if task_key not in emp_metrics['task_completion_time']:
                emp_metrics['task_completion_time'][task_key] = []
            emp_metrics['task_completion_time'][task_key].append(time_taken)


            # # Calculate averages for actual times
            # for detail in data['details_work_comparison']:
            #     count = data['details_work_comparison'][detail]['count']
            #     if count > 0:
            #         data['details_work_comparison'][detail]['actual_time'] /= count  

        return data
    
    def display_employee_pie_charts(self, parent_frame, data, row_offset=12):
        """Display pie charts for each employee's metrics"""
        employee_metrics = data['employee_metrics']
        
        for emp_idx, (employee_id, metrics) in enumerate(employee_metrics.items()):
            # Create employee section title
            title_label = tk.Label(
                parent_frame,
                text=f"Employee ID: {employee_id} - Detailed Metrics",
                font=("Arial", 14, "bold")
            )
            title_label.grid(row=row_offset + emp_idx * 4, column=0, columnspan=3, pady=20)
            
            # Create pie charts for each metric type
            metric_charts = [
                (metrics['work_categories'], f"Work Categories - Employee {employee_id}"),
                (metrics['details_of_work'], f"Work Details - Employee {employee_id}"),
                (metrics['so_numbers'], f"SO Numbers - Employee {employee_id}"),
                (metrics['time_categories'], f"Time Categories - Employee {employee_id}"),
                ({'Standard': metrics['overtime_vs_standard']['standard'], 
                'Overtime': metrics['overtime_vs_standard']['overtime']}, 
                f"Standard vs Overtime - Employee {employee_id}")
            ]
            
            for chart_idx, (chart_data, title) in enumerate(metric_charts):
                if chart_data:
                    row = row_offset + emp_idx * 4 + 1 + (chart_idx // 3)
                    col = chart_idx % 3
                    buffer = GraphGenerator.create_pie_chart(chart_data, title)
                    self.display_graph_from_buffer(buffer, parent_frame, row, col)

    def display_last_1_day(self):
        start_date, end_date = self.get_date_range(1)
        self.display_graphs(start_date, end_date, "Last 1 Day")

    def display_last_1_week(self):
        start_date, end_date = self.get_date_range(7)
        self.display_graphs(start_date, end_date, "Last 1 Week")

    def display_last_1_month(self):
        start_date, end_date = self.get_date_range(30)
        self.display_graphs(start_date, end_date, "Last 1 Month")

    def display_last_3_months(self):
        start_date, end_date = self.get_date_range(90)
        self.display_graphs(start_date, end_date, "Last 3 Months")

    def display_last_6_months(self):
        start_date, end_date = self.get_date_range(180)
        self.display_graphs(start_date, end_date, "Last 6 Months")



    def display_sunburst_charts(self):
        # Clear existing content
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        # Create a frame for sunburst controls
        sunburst_control_frame = ctk.CTkFrame(self.result_frame, fg_color="transparent")
        sunburst_control_frame.pack(pady=20, padx=20, fill="x")
        
        # Add label
        label = ctk.CTkLabel(
            sunburst_control_frame,
            text="Select SO Number:",
            font=("Arial", 14)
        )
        label.pack(side='left', padx=10)
        
        # Get SO numbers
        so_numbers = self.get_so_numbers()
        if not so_numbers:
            messagebox.showinfo("No Data", "No SO numbers found in the database")
            return
        
        # Create dropdown
        so_var = ctk.StringVar()
        so_dropdown = ctk.CTkComboBox(
            sunburst_control_frame,
            values=so_numbers,
            variable=so_var,
            width=200
        )
        so_dropdown.pack(side='left', padx=10)
        so_dropdown.set(so_numbers[0])  # Set default value
        
        # Create generate button
        generate_btn = ctk.CTkButton(
            sunburst_control_frame,
            text="Generate Chart",
            command=lambda: self.process_sunburst_data(so_var.get()),
            width=150,
            font=("Arial", 12),
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        generate_btn.pack(side='left', padx=10)

    def get_so_numbers(self):
        """Fetch unique SO numbers from the database"""
        try:
            conn = self.db.get_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return []
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT DISTINCT so_number FROM work_logs ORDER BY so_number")
                so_numbers = [str(row[0]) for row in cursor.fetchall()]
            return so_numbers
        
        except Exception as e:
            messagebox.showerror("Error", f"Error fetching SO numbers: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()




    def process_sunburst_data(self, so_number):
        """Process data and generate 4-layer sunburst chart"""
        try:
            # Show loading screen if it exists
            if hasattr(self, 'show_loading_screen'):
                self.show_loading_screen()
            
            conn = self.db.get_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return
            
            try:
                # First, get all work logs for the SO number
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT wl.details_of_work, wl.time_category, wl.work_hours,
                            wg.group_name
                        FROM work_logs wl
                        LEFT JOIN work_group_items wgi ON wl.details_of_work = wgi.work_item
                        LEFT JOIN work_groups wg ON wgi.group_id = wg.group_id
                        WHERE wl.so_number = %s
                        ORDER BY wl.log_date DESC
                    """, (so_number,))
                    records = cursor.fetchall()

                if not records:
                    messagebox.showinfo("No Data", f"No records found for SO number {so_number}")
                    return

                # Process data for sunburst chart
                data = {
                    'level1': [],  # "Total Work"
                    'level2': [],  # Work Groups
                    'level3': [],  # details_of_work
                    'level4': [],  # time_category
                    'value': []    # work_hours
                }

                total_hours = sum(float(record[2]) for record in records)

                # Process each record
                for record in records:
                    details_of_work, time_category, work_hours, group_name = record
                    
                    # If no group assigned, mark as "Ungrouped"
                    if group_name is None:
                        group_name = "Ungrouped"
                    
                    data['level1'].append("Total Work")
                    data['level2'].append(group_name)
                    data['level3'].append(details_of_work)
                    data['level4'].append(time_category)
                    data['value'].append(float(work_hours))

                # Convert to pandas DataFrame for better handling
                df = pd.DataFrame(data)

                # Create summary text for title
                group_summary = df.groupby('level2')['value'].sum().round(2)
                summary_text = "\n".join([
                    f"{group}: {hours} hours" 
                    for group, hours in group_summary.items()
                ])

                # Create sunburst chart
                fig = px.sunburst(
                    df,
                    path=['level1', 'level2', 'level3', 'level4'],
                    values='value',
                    color='level2',  # Color by work groups
                    color_discrete_sequence=[
                        '#e3342f', '#f6993f', '#38c172', '#4dc0b5', '#3490dc',
                        '#6574cd', '#9561e2', '#f66d9b', '#895129', '#ffed4a'
                    ],
                    width=1200,
                    height=1200,
                    title=f'Work Distribution for SO Number: {so_number}<br>Total Hours: {total_hours:.2f}<br><br>{summary_text}'
                )

                # Update trace information and layout
                fig.update_traces(
                    textinfo='label+value+percent entry',
                    hovertemplate="""
                        Path: %{id}<br>
                        Hours: %{value:.2f}<br>
                        Percentage: %{percentEntry:.1%}
                    """
                )

                fig.update_layout(
                    title_x=0.5,
                    title_y=0.95,
                    margin=dict(t=200),  # Increased top margin for title
                    uniformtext=dict(minsize=10, mode='hide'),
                )

                # Create save dialog
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".html",
                    filetypes=[("HTML files", "*.html")],
                    title="Save Sunburst Chart",
                    initialfile=f"work_distribution_SO_{so_number}.html"
                )

                if save_path:
                    # Save and open the chart
                    fig.write_html(
                        save_path,
                        full_html=True,
                        include_plotlyjs='cdn',
                        config={'displayModeBar': True}
                    )
                    webbrowser.open('file://' + os.path.abspath(save_path))

            finally:
                conn.close()

        except Exception as e:
            messagebox.showerror("Error", f"Error generating sunburst chart: {str(e)}")
            
        finally:
            # Hide loading screen if it exists
            if hasattr(self, 'after') and hasattr(self, 'hide_loading_screen'):
                self.after(0, self.hide_loading_screen)

    # Helper function to get work groups (if needed independently)
    def get_work_groups(self):
        """Retrieve work groups mapping from database"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT wg.group_name, wgi.work_item
                        FROM work_groups wg
                        JOIN work_group_items wgi ON wg.group_id = wgi.group_id
                    """)
                    results = cursor.fetchall()
                    
                    groups = {}
                    for group_name, work_item in results:
                        if group_name not in groups:
                            groups[group_name] = []
                        groups[group_name].append(work_item)
                    return groups
        except Exception as e:
            messagebox.showerror("Error", f"Error retrieving work groups: {str(e)}")
            return {}

    


    def show_custom_date(self):
        if self.custom_date_frame:
            self.custom_date_frame.destroy()
            
        self.custom_date_frame = ctk.CTkFrame(self, width=300, height=500, fg_color="transparent")
        self.custom_date_frame.place(relx=0.1, rely=0.5, anchor="center")
        
        # Style configuration for date entries
        style = ttk.Style()
        style.configure(
            'Custom.DateEntry',
            fieldbackground='#1f538d',
            background='#1f538d',
            foreground='white',
            arrowcolor='white'
        )

        self.setup_date_entries()
        self.setup_custom_date_buttons()

    def setup_date_entries(self):
        for label_text, variable_name in [("Start Date:", "start_date"), ("End Date:", "end_date")]:
            label = ctk.CTkLabel(
                self.custom_date_frame, 
                text=label_text,
                font=("Arial", 12),
                text_color="white"
            )
            label.pack(pady=5)

            date_frame = ttk.Frame(self.custom_date_frame)
            date_frame.pack(pady=5)

            
            date_entry = DateEntry(
                # self.custom_date_frame,
                date_frame,
                width=12,
                background="darkblue",
                foreground="white",
                font=("Arial", 10)
            )
            date_entry.pack(pady=5)
            setattr(self, variable_name, date_entry)

    def setup_custom_date_buttons(self):
        for label, command in [("Confirm", self.confirm_custom_date), ("Back", self.show_main_buttons)]:
            btn = ctk.CTkButton(
                self.custom_date_frame,
                text=label,
                command=command,
                width=250,
                height=30,
                font=("Arial", 12),
                # hover_color=self.darken_color()
            )
            btn.pack(pady=5)

    def confirm_custom_date(self):
        start = self.start_date.get()
        end = self.end_date.get()
        self.display_graphs(start, end, "Custom Date")
        self.show_main_buttons()

    def show_main_buttons(self):
        if self.custom_date_frame:
            self.custom_date_frame.destroy()

    def cleanup_plots(self):
        plt.close('all')
        for buffer in self.graph_buffers:
            buffer.close()
        self.graph_buffers.clear()

    def reset_display(self):
        # self.text_box.delete("1.0", "end")
        # self.selection_label.configure(text="")
        # self.cleanup_plots()
                # Clear the canvas
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        # Reset selection label
        self.selection_label.configure(text="")
        
        # Clear graph buffers
        self.graph_buffers.clear()
        
        # Close all matplotlib plots
        plt.close('all')

                # Clear the plot queue
        while not self.plot_queue.empty():
            try:
                self.plot_queue.get_nowait()
            except queue.Empty:
                break
        
        # Create a new canvas
        self.create_result_frame()

    def update_selection_label(self, option, date_range):
        self.selection_label.configure(text=f"Selected Option: {option} ({date_range})")

    
    def generate_pdf(self):
        if not self.graph_buffers:
            messagebox.showinfo("No Data", "Please generate graphs before downloading PDF")
            return

        try:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")]
            )
            
            if not save_path:
                return

            # Initialize PDF in landscape mode with A3 size for better graph visibility
            pdf = FPDF(orientation='L', format='A3')
            pdf.set_auto_page_break(auto=True, margin=15)

            # Add title page
            pdf.add_page()
            pdf.set_font("Arial", "B", 24)
            pdf.cell(0, 20, "Time Tracker Analytics Report", ln=True, align="C")
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
            if hasattr(self, 'selection_label'):
                selection_text = self.selection_label.cget("text")
                if selection_text:
                    pdf.cell(0, 10, selection_text, ln=True, align="C")
            
            # Constants for layout
            margin = 15
            max_width = pdf.w - (2 * margin)
            max_height = pdf.h - (2 * margin)
            
            # Calculate dimensions for 2x2 grid layout
            graph_width = max_width / 2
            graph_height = max_height / 2

            # Add graphs
            for i, buffer in enumerate(self.graph_buffers):
                # Create new page for every 4 graphs
                if i % 4 == 0:
                    pdf.add_page()

                try:
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                        tmp_path = tmp_file.name
                        buffer.seek(0)
                        tmp_file.write(buffer.getvalue())

                    # Calculate position in 2x2 grid
                    row = (i % 4) // 2
                    col = (i % 4) % 2
                    
                    x = margin + (col * graph_width)
                    y = margin + (row * graph_height)

                    # Add image to PDF with calculated dimensions
                    pdf.image(
                        tmp_path,
                        x=x,
                        y=y,
                        w=graph_width - margin,  # Subtract margin for spacing
                        h=graph_height - margin  # Subtract margin for spacing
                    )

                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

            # Save the PDF
            pdf.output(save_path)
            messagebox.showinfo("Success", "PDF generated successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generating PDF: {str(e)}")
            # Print detailed error for debugging
            import traceback
            traceback.print_exc()

def main():
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = TimeTrackerAnalytics()
    app.mainloop()

if __name__ == "__main__":
    main()







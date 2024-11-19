import customtkinter as ctk
from tkinterweb import HtmlFrame
from tkinter import filedialog
import plotly.express as px
import webbrowser
import os

# Define the data for the sunburst chart
data = dict(
       name=["MSE001011"]*106,
    task=[
        "Design Engineer", "Design Engineer", "Design Engineer", "Design Engineer", "Design Engineer", "Design Engineer", "Design Engineer", "Design Engineer", "Design Engineer",
        "GAD Draft Person", "GAD Draft Person", "GAD Draft Person", "GAD Draft Person",
        "DD Draft Person", "DD Draft Person",
        "Drawing Checker", "Drawing Checker",
        "BOM Person", "BOM Person", "BOM Person",
        "As Built Person",
        "Rework ", "Rework ","Rework ", "Rework ","Rework ",
        "Rework ", "Rework ","Rework ", "Rework ","Rework ", 
        "Rework ", "Rework ","Rework ", "Rework ","Rework ",
         "Rework ", "Rework ","Rework ", "Rework ","Rework ",
        "Rework ", "Rework ","Rework ", "Rework ","Rework ",
        "Meetings", "Meetings", "Meetings","Meetings","Meetings",
         "Other", "Other",
    ]*2,
    sub_task=[
        "Technical Specification Review", "Design of Impeller", "B.Out Requirement Release", "Design of Other Part", "D Shaft", 
        "GA Drawing Checking", "GA Drawing Correction", "CRS Preparation", "Raw Material Release",
        "B.Out Release", "Raw Material Release", "GA Drawing Preparation", "GA Drawing Correction", 
        
        "DD Preparation", "DD Correction",
        "DD Checking", "DD Correction",
        "B.Out Release", "Raw Material Requirement", "BOM Preparation",
        "As Built Preparation",

        "Due to Marketing/Client-GAD-DraftPerson", 
        "Due to Planning-GAD-DraftPerson",
        "Due to Subcontract-GAD-DraftPerson",
        "Due to Procurement-GAD-DraftPerson",
        "Due to Production-GAD-DraftPerson",

        "Due to Marketing/Client-Design Engineer", 
        "Due to Planning-Design Engineer",
        "Due to Subcontract-Design Engineer",
        "Due to Production-Design Engineer",
        "Due to Procurement-Design Engineer",

        "Due to Marketing/Client-Design BOM-Person", 
        "Due to Planning-Design BOM-Person",
        "Due to Subcontract-Design BOM-Person",
        "Due to Production-Design BOM-Person",
        "Due to Procurement-Design BOM-Person",

        "Due to Marketing/Client-Design Drawing Checker", 
        "Due to Planning-Design Drawing Checker",
        "Due to Subcontract-Design Drawing Checker",
        "Due to Production-Design Drawing Checker",
        "Due to Procurement-Design Drawing Checker",

        "Due to Marketing/Client-Design DD-Draft Person", 
        "Due to Planning-Design DD-Draft Person",
        "Due to Subcontract-Design DD-Draft Person",
        "Due to Production-Design DD-Draft Person",
        "Due to Procurement-Design DD-Draft Person",
        
        "CRM","CFM","PRM","QRM","CRM",
        "Other","Shop Visit",

    ]*2,
    time=[
        'Regular', 'Regular', 'Regular', 'Regular', 'Regular', 'Regular', 'Regular', 'Regular', 'Regular',
        'Regular', 'Regular', 'Regular', 'Regular', 'Regular', 'Regular',
        'Regular', 'Regular',
        'Regular', 'Regular',
        'Regular', 'Regular', 'Regular',
        'Regular',
        'Regular', 
        'Regular',
    
        
        'Regular', 
        'Regular',
        'Regular',
        'Regular',

        'Regular', 
        'Regular',
        'Regular',
        'Regular',
        'Regular',
        
        'Regular',
        'Regular',
        'Regular',
        'Regular',
        'Regular','Regular','Regular','Regular','Regular',
        'Regular','Regular','Regular','Regular','Regular',
        'Regular','Regular','Regular','Regular','Regular',
        

        

        'Overtime', 'Overtime', 'Overtime', 'Overtime', 'Overtime', 'Overtime', 'Overtime', 'Overtime', 'Overtime',
        'Overtime', 'Overtime', 'Overtime', 'Overtime', 'Overtime', 'Overtime',
        'Overtime', 'Overtime',
        'Overtime', 'Overtime',
        'Overtime', 'Overtime', 'Overtime',
        'Overtime',
        'Overtime', 
        'Overtime',
        

        'Overtime', 
        'Overtime',
        'Overtime',
        'Overtime',

        'Overtime',
        'Overtime',
        'Overtime', 
        'Overtime',
        'Overtime',

        'Overtime',
        'Overtime',
        'Overtime',
        'Overtime',

        'Overtime','Overtime','Overtime','Overtime','Overtime',
        'Overtime','Overtime','Overtime','Overtime','Overtime',
        'Overtime','Overtime','Overtime','Overtime','Overtime',
    ],
    value=[10, 10, 10, 10, 10, 10, 10, 10, 10,
           10, 10, 10, 10, 10, 10,
           10, 10,
           10, 10,
           10,
           10,
           5, 
           5,
           5,
           5, 
           5, 
           5,
           5,
           5,

           5, 
           5, 
           5,
           5,
           5,

           1,1,
           5,5,
           5,5,5,5,5,
           5,5,5,5,5,
           5,5,5,5,5,
           
           10, 10, 10, 10, 10, 10, 10, 10, 10,
           10, 10, 10, 10, 10, 10,
           10, 10,
           10, 10,
           10, 
           10,
           5, 
           5,
           5,
           5,
           5, 
           5,
           5,
           5,
           
           5, 
           5, 
           5,
           5,
           5,
           1,1,
           5,5,
           
           5,5,5,5,5,
           5,5,5,5,5,
           5,5,5,5,5,

           ]

)

# Create the sunburst chart with specified colors and show values
fig = px.sunburst(
    data,
    path=['name','task', 'sub_task', 'time'],
    values='value',
    color='task',
    color_discrete_sequence = [
    '#e3342f', '#f6993f', '#38c172', '#4dc0b5', '#3490dc', 
    '#6574cd', '#9561e2','#f66d9b','#895129','#ffed4a'
    
        



    ],
    

width=1200,
height=1200,
    
)

# Create the sunburst chart with specified colors and show values
fig = px.sunburst(
    data,
    path=['name', 'task', 'sub_task', 'time'],
    values='value',
    color='task',
    color_discrete_sequence=[
        '#e3342f', '#f6993f', '#38c172', '#4dc0b5', '#3490dc',
        '#6574cd', '#9561e2', '#f66d9b', '#895129', '#ffed4a'
    ],
    width=1200,
    height=1200,
)

fig.update_traces(textinfo='label+value+percent entry')


# Function to save the HTML file
def save_chart():
    save_path = filedialog.asksaveasfilename(
        defaultextension=".html",
        filetypes=[("HTML files", "*.html")],
        title="Save Sunburst Chart"
    )
    if save_path:
        fig.write_html(save_path, full_html=True, include_plotlyjs='cdn')
        webbrowser.open('file://' + save_path)


# Create the main window
root = ctk.CTk()
root.geometry("800x600")
root.title("Office Work Sunburst Chart in CustomTkinter")

# Create a button to save and open the chart
button = ctk.CTkButton(root, text="Save and Open Sunburst Chart", command=save_chart)
button.pack(pady=20)

# Run the application
root.mainloop()
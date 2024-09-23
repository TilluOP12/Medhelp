# /app.py
from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)

# Load and display the prescription JSON data
@app.route('/')
def display_prescription():
    # Load the JSON file
    json_filename = 'prescription_summary.json'
    
    # Check if the file exists
    if not os.path.exists(json_filename):
        return "No prescription data found!"

    # Read the JSON data
    with open(json_filename, 'r') as json_file:
        prescription_data = json.load(json_file)

    # Pass the data to the HTML template for display
    return render_template('form2.html', prescription=prescription_data)

if __name__ == '__main__':
    app.run(debug=True)

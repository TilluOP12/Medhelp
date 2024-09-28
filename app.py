import os
import json
import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda
from flask_pymongo import PyMongo

import os
import json
import traceback
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory, abort
from werkzeug.utils import secure_filename
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda
from flask_pymongo import PyMongo

app = Flask(__name__, static_url_path='/static', static_folder='static')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MONGO_URI'] = 'mongodb://localhost:27017/file_storage'
mongo = PyMongo(app)

# Set up your Google API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyDwa7fCt1DNhjJntr9mZlmw8eHzTyFevcA"

# Load the doctor data (ensure doctors.json is available)
with open("doctors.json", "r") as f:
    doctors_data = json.load(f)
doctors_list = [i for i in doctors_data]

with open('prescriptions.json') as json_file:
    prescription_data = json.load(json_file)

# Define the LangChain prompt template
prompt = ChatPromptTemplate.from_template(
    "You are a medical consultant with 30 years of experience in the medical industry.\n"
    "Given the following symptoms, you have to tell which type of doctor to consult from the following list: {doctors_list}.\n"
    "Symptoms: {symptoms}\n"
    "Just give the type of doctor from the list strictly, nothing else."
)

# Initialize model and output parser
model = ChatGoogleGenerativeAI(model='gemini-1.5-pro')
parser = StrOutputParser()
markdown = RunnableLambda(lambda x: x)  # Keep it simple

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class Routes:
    def __init__(self, app):
        self.app = app
        self.register_routes()

    def register_routes(self):
        self.app.add_url_rule('/', 'home', self.home)
        self.app.add_url_rule('/useracc', 'useracc', self.useracc)
        self.app.add_url_rule('/index', 'index', self.home)
        self.app.add_url_rule('/login', 'login', self.login, methods=['GET', 'POST'])
        self.app.add_url_rule('/signup', 'signup', self.signup, methods=['GET', 'POST'])
        self.app.add_url_rule('/book_appointment', 'book_appointment', self.book_appointment)
        self.app.add_url_rule('/med_history', 'med_history', self.med_history)
        self.app.add_url_rule('/get_recommendation', 'get_recommendation', self.get_recommendation, methods=['POST'])
        self.app.add_url_rule('/doctordash', 'doctordash', self.doctordash)
        self.app.add_url_rule('/confirm_doctor', 'confirm_doctor', self.confirm_doctor)
        self.app.add_url_rule('/form', 'form', self.form)
        self.app.add_url_rule('/start_appointment', 'start_appointment', self.start_appointment, methods=['POST'])
        self.app.add_url_rule('/start_user', 'start_user', self.start_user, methods=['POST'])
        self.app.add_url_rule('/upload/medication', 'upload_medication', self.upload_medication, methods=['POST'])
        self.app.add_url_rule('/upload/test', 'upload_test', self.upload_test, methods=['POST'])
        self.app.add_url_rule('/prescription_summary', 'display_prescription', self.display_prescription)
        self.app.add_url_rule('/userlogin', 'userlogin', self.userlogin, methods=['GET', 'POST'])
        self.app.add_url_rule('/get_doctors', 'get_doctors', self.get_doctors)
        self.app.add_url_rule('/test', 'test', self.test)
        self.app.add_url_rule('/start_appointment2','start_appointment2',self.start_appointment2    , methods=['POST'])
        self.app.add_url_rule('/get_dates', 'get_dates', self.get_dates, methods=['GET'])
        self.app.add_url_rule('/get_prescription_data/<date>', 'get_prescription_data', self.get_prescription_data, methods=['GET'])
        self.app.add_url_rule('/nofollowup', 'nofollowup', self.nofollowup)
        self.app.add_url_rule('/followup', 'followup', self.followup)
        self.app.add_url_rule('/uploads/<path:filename>', 'serve_file', self.serve_file, methods=['GET'])
        self.app.add_url_rule('/get_files_by_date', 'get_files_by_date', self.get_files_by_date, methods=['GET'])
        self.app.add_url_rule('/save_date', 'save_date', self.save_date, methods=['POST'])
        self.app.add_url_rule('/get_dates2', 'get_dates2', self.get_dates2, methods=['GET'])



    def home(self):
        return render_template('index.html')

    

    def doctordash(self):
        return render_template('doctordash.html')
    
    def form(self):
        return render_template('form.html')

    def book_appointment(self):
        return render_template('book-appointment.html')
    
    def useracc(self):
        return render_template('useracc.html')
    
    def test(self):
     return render_template('test.html')
    
    def followup(self):
     return render_template('confirm2.html')
    
    def nofollowup(self):
     return render_template('test.html')

    def get_doctors(self):
        with open('doctors.json') as f:
            doctors_data = json.load(f)
        return jsonify(doctors_data)
    
    def start_user(self):
        if request.method == 'POST':
            
            return redirect(url_for('useracc'))
            
    
    def userlogin(self):
           
        return render_template('userlogin.html')
    

    

    def login(self):
        if request.method == 'POST':
            username = request.form.get('username_doc')  # Use parentheses () with get
            password = request.form.get('password_doc')  # Use parentheses () with get
            
            if username == "admin" and password == "password":
                return redirect(url_for('doctordash'))
            else:
                return "Invalid username or password"
        return render_template('login.html')

    def signup(self):
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            otp = request.form['otp']
            password = request.form['password']
            specialization = request.form['specialization']
            experience = request.form['experience']
            file = request.files['degree-upload']
            if file and file.filename.endswith('.pdf'):
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            if otp == "123456":
                return redirect(url_for('login'))
            else:
                return "Invalid OTP"
        return render_template('signup.html')
    
    def start_appointment(self):
        if request.method == 'POST':
            action = request.form.get('action')
            patient_name = request.form.get('patient_name')
            specialty = request.form.get('specialty')
            time_slot = request.form.get('time_slot')
            symptoms = request.form.get('symptoms')
            if action == 'start':
                return redirect(url_for('form'))
            elif action == 'cancel':
                return redirect(url_for('doctordash'))

    def upload_test(self):
        if 'file' not in request.files:
            return jsonify({'message': 'No file part'}), 400
        
        file = request.files['file']
        filename = request.form.get('filename')
        selected_date = request.form.get('selectedDate')  # Retrieve the selected date

        if file.filename == '' or not filename or not selected_date:
            return jsonify({'message': 'File, filename, or date missing'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(filename)

            # Create the directory path dynamically
            directory_path = os.path.join(UPLOAD_FOLDER, selected_date, 'tests')
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)

            file_path = os.path.join(directory_path, filename)
            file.save(file_path)

            # Save the file details without the 'uploads/' prefix
            mongo.db.history.insert_one({
                'user_id': session.get('user_id', 'guest'),
                'file_name': filename,
                'file_path': os.path.relpath(file_path, UPLOAD_FOLDER),  # Save relative path
                'selected_date': selected_date,  
            })
            return jsonify({'message': 'Test uploaded successfully'}), 201
            
        return jsonify({'message': 'Invalid file type'}), 400


    def upload_medication(self):
        if 'file' not in request.files:
            return jsonify({'message': 'No file part'}), 400
        
        file = request.files['file']
        filename = request.form.get('filename')
        selected_date = request.form.get('selectedDate')  # Retrieve the selected date

        if file.filename == '' or not filename or not selected_date:
            return jsonify({'message': 'File, filename, or date missing'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(filename)

            # Create the directory path dynamically
            directory_path = os.path.join(UPLOAD_FOLDER, selected_date, 'medication')
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)

            file_path = os.path.join(directory_path, filename)
            file.save(file_path)

            # Save the file details without the 'uploads/' prefix
            mongo.db.history.insert_one({
                'user_id': session.get('user_id', 'guest'),
                'file_name': filename,
                'file_path': os.path.relpath(file_path, UPLOAD_FOLDER),  # Save relative path
                'selected_date': selected_date,  
            })
            return jsonify({'message': 'Medication uploaded successfully'}), 201
            
        return jsonify({'message': 'Invalid file type'}), 400


    def get_recommendation(self):
        symptoms = request.form['symptoms']
        chain = prompt | model | parser | markdown
        response = chain.invoke({"symptoms": symptoms, "doctors_list": doctors_list})
        doctor_type = response.strip()
        if doctor_type in doctors_data:
            doctor_info = doctors_data[doctor_type]
        else:
            doctor_info = None
        return jsonify({'doctor_type': doctor_type, 'doctor_info': doctor_info})

    def med_history(self):
        return render_template('med-history.html')
    
    def confirm_doctor(self):
    # Get the doctor's name from the query parameters
        doctor_name = request.args.get('doctor')
        doctor_qualifications = request.args.get('qualifications')

        # Check if doctor_name is provided
        if not doctor_name:
            return "Doctor name is missing", 400

        # Pass the doctor's name to the confirm.html template
        return render_template('confirm.html', doctor=doctor_name, qualifications=doctor_qualifications)

           

    def display_prescription(self):
        json_filename = 'prescriptions.json'
        # Check if the JSON file exists
        if not os.path.exists(json_filename):
            # If the file doesn't exist, return an error page or message
            return render_template('med-history.html', prescription={})
        
        # Load the prescription data
        with open(json_filename, 'r') as json_file:
            prescription_data = json.load(json_file)
        
        # Ensure the 'prescription' key exists in the JSON data
        if not prescription_data.get("prescriptions"):
            return render_template('med-history.html', prescription={})
        
        # Pass the prescription data to the template
        return render_template('med-history.html', prescription=prescription_data['prescription'])
    

    def get_dates(self):
        with open('prescriptions.json') as json_file:
            prescription_data = json.load(json_file)

        dates = list({item.get('date') for item in prescription_data if 'date' in item})
        return jsonify(dates)

    def get_prescription_data(self, date):
        # Load the prescription data dynamically from the JSON file
        with open('prescriptions.json') as json_file:
            prescription_data = json.load(json_file)

        # Fetch prescription data by date
# Ensure each item has the 'date' key before trying to access it
        prescription = next((item for item in prescription_data if 'date' in item and item['date'] == date), None)
        return jsonify(prescription) if prescription else jsonify({"error": "Prescription data not found"}), 404
    
    def start_appointment2(self):
        # Retrieve form data
        med_help_id = request.form.get('med_help_id')
        diagnosis = request.form.get('diagnosis')
        date = request.form.get('date')
        consultation_notes = request.form.get('consultation_notes')
        medication_name = request.form.get('medication_name')
        medication_dosage = request.form.get('medication_dosage')
        medication_frequency = request.form.get('medication_frequency')
        medication_duration = request.form.get('medication_duration')
        followup_schedule = request.form.get('followup_schedule')

        # Create a dictionary to store the form data
        appointment_data = {
            'date': date,
            'med_help_id': med_help_id,
            'diagnosis': diagnosis,
            'consultation_notes': consultation_notes,
            'medication_name': medication_name,
            'medication_dosage': medication_dosage,
            'medication_frequency': medication_frequency,
            'medication_duration': medication_duration,
            'followup_schedule': followup_schedule
        }

        # Write the data to a JSON file
        try:
            # Load existing data from the file if it exists
            with open('prescriptions.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            # If the file doesn't exist, initialize with an empty list
            data = []

        # Append the new appointment data to the list
        data.append(appointment_data)

        # Save the updated data back to the file
        with open('prescriptions.json', 'w') as file:
            json.dump(data, file, indent=4)

        # No return statement needed since we are just saving the data in a file
        return "Appointment data saved successfully!"
    
    def get_files_by_date(self):
        # Retrieve the selected date from the request parameters
        selected_date = request.args.get('selectedDate')

        if not selected_date:
            return jsonify({'message': 'Date parameter is missing'}), 400

        # Query the MongoDB collection for files that match the selected date
        files = mongo.db.history.find({'selected_date': selected_date}, {'file_name': 1, 'file_path': 1, '_id': 0})

        # If no files are found, return a message
        file_list = [{'file_name': file['file_name'], 'file_path': file['file_path']} for file in files]
        
        if not file_list:
            return jsonify({'message': 'No files found for the specified date'}), 404

        # Return the list of files along with the file paths
        return jsonify({'files': file_list}), 200
    
    def save_date(self):
        try:
            # Try to retrieve the selected date from the form data
            selected_date = request.form.get('selectedDate')  # Using form data since you're sending FormData from frontend
            print(f"Received date: {selected_date}")  # Ensure selected_date is coming in correctly

            if not selected_date:
                return jsonify({'message': 'No date provided'}), 400

            # Check if the date already exists
            existing_date = mongo.db.threads.find_one({'date': selected_date})

            if existing_date:
                return jsonify({'message': 'Date already exists'}), 400

            # Insert new date into the database
            mongo.db.threads.insert_one({'date': selected_date})

            return jsonify({'message': 'Date saved successfully'}), 201

        except Exception as e:
            print("Error saving date:", str(e))  # Print the actual error
            traceback.print_exc()  # Print full traceback for debugging
            return jsonify({'message': 'Internal Server Error', 'error': str(e)}), 500  # Return 500 with error details

    
    def get_dates2(self):
        try:
            # Query the MongoDB database to get all dates
            dates_cursor = mongo.db.threads.find({}, {'_id': 0, 'date': 1})  # Exclude the `_id` field
            dates = [date['date'] for date in dates_cursor]  # Create a list of all dates
            # Return the list of dates as JSON
            return jsonify(dates), 200
        except Exception as e:
            # If something goes wrong, return an error message
            return jsonify({'message': 'Error retrieving dates', 'error': str(e)}), 500

    def serve_file(self, filename):
        try:
            # Normalize the file path to handle both Windows and Unix-style paths
            normalized_filename = os.path.normpath(filename)

            # Construct the absolute path to the requested file
            absolute_path = os.path.join(app.config['UPLOAD_FOLDER'], normalized_filename)
            print(f"Serving file from: {absolute_path}")  # Debug print to check the file path

            # Check if the file exists
            if not os.path.isfile(absolute_path):
                print(f"File not found: {absolute_path}")  # Debug if the file is missing
                abort(404)  # Return a 404 error if the file does not exist

            # Use send_from_directory to serve the file
            return send_from_directory(os.path.dirname(absolute_path), os.path.basename(absolute_path))
        except Exception as e:
            print(f"Error: {str(e)}")
            traceback.print_exc()  # Print the full traceback to the console
            abort(500)  # Return a 500 error if something goes wrong



# Instantiate the Routes class
Routes(app)

if __name__ == '__main__':
    app.run(debug=True)

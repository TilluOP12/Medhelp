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
        self.app.add_url_rule('/index', 'index', self.home)
        self.app.add_url_rule('/login', 'login', self.login, methods=['GET', 'POST'])
        self.app.add_url_rule('/signup', 'signup', self.signup, methods=['GET', 'POST'])
        self.app.add_url_rule('/book_appointment', 'book_appointment', self.book_appointment)
        self.app.add_url_rule('/med_history', 'med_history', self.med_history)
        self.app.add_url_rule('/get_recommendation', 'get_recommendation', self.get_recommendation, methods=['POST'])
        self.app.add_url_rule('/confirm', 'confirm', self.confirm)
        self.app.add_url_rule('/doctordash', 'doctordash', self.doctordash)
        self.app.add_url_rule('/confirm_doctor', 'confirm_doctor', self.confirm_doctor)
        self.app.add_url_rule('/form', 'form', self.form)
        self.app.add_url_rule('/start_appointment', 'start_appointment', self.start_appointment, methods=['POST'])
        self.app.add_url_rule('/upload/medication', 'upload_medication', self.upload_medication, methods=['POST'])
        self.app.add_url_rule('/upload/test', 'upload_test', self.upload_test, methods=['POST'])
        self.app.add_url_rule('/prescription_summary', 'display_prescription', self.display_prescription)

    def home(self):
        return render_template('index.html')

    def confirm(self):
        doctor_name = request.args.get('doctor')
        return render_template('confirm.html', doctor=doctor_name)

    def confirm_doctor(self):
        doctor_name = request.args.get('doctor')
        return render_template('confirm.html', doctor=doctor_name)

    def doctordash(self):
        return render_template('doctordash.html')
    
    def form(self):
        return render_template('form.html')

    def book_appointment(self):
        return render_template('book-appointment.html')

    def login(self):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
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
        if file.filename == '' or not filename:
            return jsonify({'message': 'No selected file or filename missing'}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            mongo.db.prescriptions.insert_one({
                'user_id': session.get('user_id', 'guest'),
                'file_name': filename,
                'file_path': file_path,
                'upload_date': datetime.datetime.utcnow()
            })
            return jsonify({'message': 'Prescription uploaded successfully'}), 201
        return jsonify({'message': 'Invalid file type'}), 400

    def upload_medication(self):
        if 'file' not in request.files:
            return jsonify({'message': 'No file part'}), 400
        file = request.files['file']
        filename = request.form.get('filename')
        if file.filename == '' or not filename:
            return jsonify({'message': 'No selected file or filename missing'}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            mongo.db.reports.insert_one({
                'user_id': session.get('user_id', 'guest'),
                'file_name': filename,
                'file_path': file_path,
                'upload_date': datetime.datetime.utcnow()
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

    def display_prescription(self):
        json_filename = 'prescription_summary.json'
        # Check if the JSON file exists
        if not os.path.exists(json_filename):
            # If the file doesn't exist, return an error page or message
            return render_template('med-history.html', prescription={})
        
        # Load the prescription data
        with open(json_filename, 'r') as json_file:
            prescription_data = json.load(json_file)
        
        # Ensure the 'prescription' key exists in the JSON data
        if not prescription_data.get("prescription"):
            return render_template('med-history.html', prescription={})
        
        # Pass the prescription data to the template
        return render_template('med-history.html', prescription=prescription_data['prescription'])


# Instantiate the Routes class
Routes(app)

if __name__ == '__main__':
    app.run(debug=True)

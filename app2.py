import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda
from flask_pymongo import PyMongo
import os
import datetime
from werkzeug.utils import secure_filename  


app = Flask(__name__, static_url_path='/static', static_folder='static')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure MongoDB
app.config['MONGO_URI'] = 'mongodb://localhost:27017/file_storage'
mongo = PyMongo(app)


# Set up your Google API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyDwa7fCt1DNhjJntr9mZlmw8eHzTyFevcA"

# Load the doctor data (ensure doctors.json is available)
with open("doctors.json", "r") as f:
    doctors_data = json.load(f)

# Prepare the list of doctors from the database
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
        # Add URL rules
        self.app.add_url_rule('/', 'home', self.home)
        self.app.add_url_rule('/index', 'index', self.home)
        self.app.add_url_rule('/login', 'login', self.login, methods=['GET', 'POST'])
        self.app.add_url_rule('/signup', 'signup', self.signup, methods=['GET', 'POST'])
        self.app.add_url_rule('/book_appointment', 'book_appointment', self.book_appointment)
        self.app.add_url_rule('/med_history', 'med_history', self.med_history)
        self.app.add_url_rule('/get_recommendation', 'get_recommendation', self.get_recommendation, methods=['POST'])
        self.app.add_url_rule('/upload/medication', 'upload_medication', self.upload_medication, methods=['POST'])
        self.app.add_url_rule('/upload/test', 'upload_test', self.upload_test, methods=['POST'])

    def home(self):
        return render_template('index.html')

    def login(self):
        return render_template('login.html')

    def signup(self):
        if request.method == 'POST':
            # Get form data
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            otp = request.form['otp']
            password = request.form['password']
            specialization = request.form['specialization']
            experience = request.form['experience']

            # Save the medical degree PDF
            file = request.files['degree-upload']
            if file and file.filename.endswith('.pdf'):
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

            # Simulate OTP verification
            if otp == "123456":  # Example static OTP
                # In a real case, check OTP from the database or external service
                return redirect(url_for('login'))
            else:
                return "Invalid OTP"

        return render_template('signup.html')    

    @app.route('/login')
    def success(self):
        return "Sign up successful!"

    def book_appointment(self):
        return render_template('book-appointment.html')

    def get_recommendation(self):
        # Get the symptoms from the form
        symptoms = request.form['symptoms']

        # Execute the AI model to get the doctor's type
        chain = prompt | model | parser | markdown
        response = chain.invoke({"symptoms": symptoms, "doctors_list": doctors_list})

        doctor_type = response.strip()

        # Fetch the doctor info from your database
        if doctor_type in doctors_data:
            doctor_info = doctors_data[doctor_type]
        else:
            doctor_info = None

        return jsonify({
            'doctor_type': doctor_type,
            'doctor_info': doctor_info
        })

    def med_history(self):
        return render_template('med-history.html')
    
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

            user_id = session.get('user_id', 'guest')
            mongo.db.prescriptions.insert_one({
                'user_id': user_id,
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

            user_id = session.get('user_id', 'guest')
            mongo.db.reports.insert_one({
                'user_id': user_id,
                'file_name': filename,
                'file_path': file_path,
                'upload_date': datetime.datetime.utcnow()
            })

            return jsonify({'message': 'Medication uploaded successfully'}), 201

        return jsonify({'message': 'Invalid file type'}), 400

# Instantiate the Routes class
Routes(app)

if __name__ == '__main__':
    app.run(debug=True)

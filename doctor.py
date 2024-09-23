import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.secret_key = 'your_secret_key'  # Required for session management

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
        self.app.add_url_rule('/confirm', 'confirm', self.confirm)
        self.app.add_url_rule('/doctordash', 'doctordash', self.doctordash)
        self.app.add_url_rule('/confirm_doctor', 'confirm_doctor', self.confirm_doctor)
        self.app.add_url_rule('/form', 'form', self.form)
        self.app.add_url_rule('/start_appointment', 'start_appointment', self.start_appointment, methods=['POST'])
        self.app.add_url_rule('/view_all_appointments', 'view_all_appointments', self.view_all_appointments)

    def home(self):
        return render_template('index.html')

    def confirm(self):
        doctor_name = request.args.get('doctor')
        # Logic to handle doctor details and render confirm page
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
            # Get form data (assuming you have username and password fields)
            username = request.form['username']
            password = request.form['password']

            # Implement your authentication logic here
            if username == "admin" and password == "password":  # Example static check
                # If successful, redirect to the desired page (e.g., dashboard or confirmation)
                return redirect(url_for('doctordash'))  # This redirects to the 'doctordash' page
            else:
                # If authentication fails, stay on login page or show error
                return "Invalid username or password"

        return render_template('login.html')  # Render the login page for GET requests

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
    
    def start_appointment(self):
        if request.method == 'POST':
            action = request.form.get('action')
            patient_name = request.form.get('patient_name')
            specialty = request.form.get('specialty')
            time_slot = request.form.get('time_slot')
            symptoms = request.form.get('symptoms')

            if action == 'start':
                # Logic to start the appointment
                return redirect(url_for('form'))
            elif action == 'cancel':
                # Logic to handle appointment cancellation
                return redirect(url_for('doctordash'))

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

    def view_all_appointments(self):
        # Logic to display all appointments
        return render_template('all-appointments.html')

# Instantiate the Routes class
Routes(app)

if __name__ == '__main__':
    app.run(debug=True)

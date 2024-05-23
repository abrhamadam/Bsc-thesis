from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, render_template, jsonify ,session, redirect # Import jsonify
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import pandas as pd
import pickle
import random
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey,create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://abrham:abrish1234@localhost:3306/telemedicine_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '123'

# Create SQLAlchemy instance
db = SQLAlchemy(app)

# Define user types (for example, doctor usernames)
doctors = {'abrham': 'abcd1234'}  # Mapping of doctor usernames to passwords


class Consultation(Base):
    __tablename__ = 'consultation'

    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False)
    phone = Column(String(20), nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    message = Column(Text)
    approved = Column(Boolean, default=False)

    action_status = relationship("ActionStatus", uselist=False, back_populates="appointment")

    def __repr__(self):
        return f"<Consultation(id={self.id}, full_name='{self.full_name}', email='{self.email}', phone='{self.phone}', appointment_date='{self.appointment_date}', message='{self.message}', approved={self.approved})>"
engine = create_engine('mysql://abrham:abrish1234@localhost:3306/telemedicine_db')
Session = sessionmaker(bind=engine)

class ActionStatus(Base):
    __tablename__ = 'action_status'

    id = Column(Integer, primary_key=True)
    appointment_id = Column(Integer, ForeignKey('consultation.id'), nullable=False)
    action = Column(String(10), nullable=False)  # 'approve' or 'reject'
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    appointment = relationship("Consultation", back_populates="action_status")
# Route to render the appointment form
@app.route('/appointmentForm')
def appointment_form():
    return render_template('appointmentForm.html')


# Route to handle form submission
@app.route('/book-consultation', methods=['POST'])
def book_consultation():
    if request.method == 'POST':
        # Extract data from the form submission
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        appointment_date = datetime.strptime(request.form['appointment_date'], '%Y-%m-%d').date()
        message = request.form['message']

        # Create a new consultation record
        new_consultation = Consultation(full_name=full_name, email=email, phone=phone, appointment_date=appointment_date, message=message)
        db.session.add(new_consultation)
        db.session.commit()

        consultation_id = new_consultation.id
        return f"Consultation booked successfully for {full_name} on {appointment_date}.Your Consultation ID is: {consultation_id} Thank you!"

    return "Invalid request"


@app.route('/approve_appointment/<int:appointment_id>', methods=['POST'])
def approve_appointment(appointment_id):
    if request.method == 'POST':
        action = request.form['action']  # 'approve' or 'reject'

        # Update appointment status
        appointment = db.session.query(Consultation).get(appointment_id)
        if action == 'approve':
            appointment.approved = True
        else:
            appointment.approved = False

        # Create action status record
        new_action_status = ActionStatus(appointment_id=appointment_id, action=action)
        db.session.add(new_action_status)
        db.session.commit()

        return redirect('/appointments')

    return "Invalid request"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve username and password from the form
        username = request.form['username']
        password = request.form['password']

        # Check if the entered credentials are valid for doctors
        if username in doctors and doctors[username] == password:
            # Set session variables to indicate user is logged in
            session['logged_in'] = True
            session['username'] = username

            # Redirect doctors to appointments page after login
            return redirect('/appointments')

        # Invalid credentials, show error message
        error_message = 'Invalid username or password. Please try again.'
        return render_template('login.html', error_message=error_message)

    # Render the login form for GET requests
    return render_template('login.html')


@app.route('/appointments')
def appointments():
    if 'logged_in' in session and session['logged_in']:
        # Retrieve appointments from the database
        appointments = db.session.query(Consultation).all()
        return render_template('appointments.html', appointments=appointments)

    # Redirect to login page if not logged in
    return redirect('/login')


@app.route('/logout')
def logout():
    session.clear()
    # Redirect to the home page after logout
    return redirect('/')
# Route to render the login form for action status
@app.route('/login_action_status', methods=['GET', 'POST'])
def login_action_status():
    if request.method == 'POST':
        # Retrieve username or ID from the form
        username = request.form.get('username')

        # Use the username or ID to query the action statuses
        session = Session()
        action_statuses = session.query(ActionStatus).all()
        session.close()
        if action_statuses:
            return render_template('action_status.html', action_statuses=action_statuses)
        else:
            error_message = 'No action statuses found for the provided username or ID.'
            return render_template('login_action_status.html', error_message=error_message)

    # Render the login form for GET requests
    return render_template('login_action_status.html')


# load databasedataset===================================
sym_des = pd.read_csv("datasets/symtoms_df.csv")
precautions = pd.read_csv("datasets/precautions_df.csv")
workout = pd.read_csv("datasets/workout_df.csv")
description = pd.read_csv("datasets/description.csv")
medications = pd.read_csv('datasets/medications.csv')
diets = pd.read_csv("datasets/diets.csv")


# load model===========================================
svc = pickle.load(open('models/model1.pkl','rb'))


#============================================================
# custome and helping functions
#==========================helper funtions================
def helper(dis):
    desc = description[description['Disease'] == dis]['Description']
    desc = " ".join([w for w in desc])

    pre = precautions[precautions['Disease'] == dis][['Precaution_1', 'Precaution_2', 'Precaution_3', 'Precaution_4']]
    pre = [col for col in pre.values]

    med = medications[medications['Disease'] == dis]['Medication']
    med = [med for med in med.values]

    die = diets[diets['Disease'] == dis]['Diet']
    die = [die for die in die.values]

    wrkout = workout[workout['disease'] == dis] ['workout']


    return desc,pre,med,die,wrkout



symptoms_dict = {'itching': 0, 'skin_rash': 1, 'nodal_skin_eruptions': 2, 'continuous_sneezing': 3, 'shivering': 4, 'chills': 5, 'joint_pain': 6, 'stomach_pain': 7, 'acidity': 8, 'ulcers_on_tongue': 9, 'muscle_wasting': 10, 'vomiting': 11, 'burning_micturition': 12, 'spotting_urination': 13, 'fatigue': 14, 'weight_gain': 15, 'anxiety': 16, 'cold_hands_and_feets': 17, 'mood_swings': 18, 'weight_loss': 19, 'restlessness': 20, 'lethargy': 21, 'patches_in_throat': 22, 'irregular_sugar_level': 23, 'cough': 24, 'high_fever': 25, 'sunken_eyes': 26, 'breathlessness': 27, 'sweating': 28, 'dehydration': 29, 'indigestion': 30, 'headache': 31, 'yellowish_skin': 32, 'dark_urine': 33, 'nausea': 34, 'loss_of_appetite': 35, 'pain_behind_the_eyes': 36, 'back_pain': 37, 'constipation': 38, 'abdominal_pain': 39, 'diarrhoea': 40, 'mild_fever': 41, 'yellow_urine': 42, 'yellowing_of_eyes': 43, 'acute_liver_failure': 44, 'fluid_overload': 45, 'swelling_of_stomach': 46, 'swelled_lymph_nodes': 47, 'malaise': 48, 'blurred_and_distorted_vision': 49, 'phlegm': 50, 'throat_irritation': 51, 'redness_of_eyes': 52, 'sinus_pressure': 53, 'runny_nose': 54, 'congestion': 55, 'chest_pain': 56, 'weakness_in_limbs': 57, 'fast_heart_rate': 58, 'pain_during_bowel_movements': 59, 'pain_in_anal_region': 60, 'bloody_stool': 61, 'irritation_in_anus': 62, 'neck_pain': 63, 'dizziness': 64, 'cramps': 65, 'bruising': 66, 'obesity': 67, 'swollen_legs': 68, 'swollen_blood_vessels': 69, 'puffy_face_and_eyes': 70, 'enlarged_thyroid': 71, 'brittle_nails': 72, 'swollen_extremeties': 73, 'excessive_hunger': 74, 'extra_marital_contacts': 75, 'drying_and_tingling_lips': 76, 'slurred_speech': 77, 'knee_pain': 78, 'hip_joint_pain': 79, 'muscle_weakness': 80, 'stiff_neck': 81, 'swelling_joints': 82, 'movement_stiffness': 83, 'spinning_movements': 84, 'loss_of_balance': 85, 'unsteadiness': 86, 'weakness_of_one_body_side': 87, 'loss_of_smell': 88, 'bladder_discomfort': 89, 'foul_smell_of urine': 90, 'continuous_feel_of_urine': 91, 'passage_of_gases': 92, 'internal_itching': 93, 'toxic_look_(typhos)': 94, 'depression': 95, 'irritability': 96, 'muscle_pain': 97, 'altered_sensorium': 98, 'red_spots_over_body': 99, 'belly_pain': 98, 'abnormal_menstruation': 99, 'dischromic _patches': 100, 'watering_from_eyes': 101, 'increased_appetite': 102, 'polyuria': 103, 'family_history': 104, 'mucoid_sputum': 105, 'rusty_sputum': 106, 'lack_of_concentration': 107, 'visual_disturbances': 108, 'receiving_blood_transfusion': 109, 'receiving_unsterile_injections': 110, 'coma': 111, 'stomach_bleeding': 112, 'distention_of_abdomen': 113, 'history_of_alcohol_consumption': 114, 'fluid_overload.1': 115, 'blood_in_sputum': 116, 'prominent_veins_on_calf': 117, 'palpitations': 118, 'painful_walking': 119, 'pus_filled_pimples': 120, 'blackheads': 121, 'scurring': 122, 'skin_peeling': 123, 'silver_like_dusting': 124, 'small_dents_in_nails': 125, 'inflammatory_nails': 126, 'blister': 127, 'red_sore_around_nose': 128, 'yellow_crust_ooze': 129}
diseases_list = {15: 'Fungal infection', 4: 'Allergy', 16: 'GERD', 9: 'Chronic cholestasis', 14: 'Drug Reaction', 33: 'Peptic ulcer diseae', 1: 'AIDS', 12: 'Diabetes ', 17: 'Gastroenteritis', 6: 'Bronchial Asthma', 23: 'Hypertension ', 30: 'Migraine', 7: 'Cervical spondylosis', 32: 'Paralysis (brain hemorrhage)', 28: 'Jaundice', 29: 'Malaria', 8: 'Chicken pox', 11: 'Dengue', 37: 'Typhoid', 40: 'hepatitis A', 19: 'Hepatitis B', 20: 'Hepatitis C', 21: 'Hepatitis D', 22: 'Hepatitis E', 3: 'Alcoholic hepatitis', 36: 'Tuberculosis', 10: 'Common Cold', 34: 'Pneumonia', 13: 'Dimorphic hemmorhoids(piles)', 18: 'Heart attack', 39: 'Varicose veins', 26: 'Hypothyroidism', 24: 'Hyperthyroidism', 25: 'Hypoglycemia', 31: 'Osteoarthristis', 5: 'Arthritis', 0: '(vertigo) Paroymsal  Positional Vertigo', 2: 'Acne', 38: 'Urinary tract infection', 35: 'Psoriasis', 27: 'Impetigo'}

# Model Prediction function
def get_predicted_value(patient_symptoms):
    input_vector = np.zeros(len(symptoms_dict))
    for item in patient_symptoms:
        input_vector[symptoms_dict[item]] = 1
    return diseases_list[svc.predict([input_vector])[0]]

# creating routes========================================


@app.route("/")
def index():
    return render_template("index.html")


# Define a route for the home page
@app.route('/predict', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        symptoms = request.form.get('symptoms')
        if symptoms is None or symptoms.strip() == "":
            message = "Please enter symptoms."
            return render_template('index.html', message=message)

        user_symptoms = [s.strip() for s in symptoms.split(',')]
        user_symptoms = [symptom.strip("[]' ") for symptom in user_symptoms]

        if not all(symptom in symptoms_dict for symptom in user_symptoms):
            message = "Invalid symptom detected."
            return render_template('index.html', message=message)

        predicted_disease = get_predicted_value(user_symptoms)
        desc, pre, med, diet, workout = helper(predicted_disease)

        my_precautions = pre[0] if pre else []

        return render_template('index.html', predicted_disease=predicted_disease,
                               dis_des=desc, my_precautions=my_precautions,
                               medications=med, my_diet=diet, workout=workout)

    return render_template('index.html')


# about view funtion and path
@app.route('/about')
def about():
    return render_template("about.html")


# contact view funtion and path
@app.route('/contact')
def contact():
    return render_template("contact.html")


# developer view funtion and path
@app.route('/developer')
def developer():
    return render_template("developer.html")


# about view funtion and path
@app.route('/blog')
def blog():
    return render_template("blog.html")




if __name__ == '__main__':

    app.run(debug=True)
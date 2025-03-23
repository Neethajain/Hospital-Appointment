from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import csv
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Appointment Model
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    doctor = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(100), nullable=False)  # Store as a string

# Create Database Tables
with app.app_context():
    db.create_all()

# Serve HTML Page
@app.route('/')
def index():
    return render_template('index.html')

# Get all appointments
@app.route('/appointments', methods=['GET'])
def get_appointments():
    appointments = Appointment.query.all()
    return jsonify([{"id": a.id, "name": a.name, "doctor": a.doctor, "time": a.time} for a in appointments])

# Add appointment with 1-hour gap enforcement
@app.route('/appointments', methods=['POST'])
def add_appointment():
    data = request.json
    name = data.get('name')
    doctor = data.get('doctor')
    time = data.get('time')

    # Convert time to datetime object
    try:
        appointment_datetime = datetime.strptime(time, "%Y-%m-%dT%H:%M")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DDTHH:MM"}), 400

    # Get the date part
    appointment_date = appointment_datetime.date()

    # Count existing appointments for the doctor on the same day
    doctor_appointments = Appointment.query.filter(
        Appointment.doctor == doctor,
        Appointment.time.like(f"{appointment_date}%")
    ).count()

    if doctor_appointments >= 10:
        return jsonify({"error": "Doctor has reached the maximum of 10 appointments for the day!"}), 400

    # Check if the patient already has an appointment for the same day
    existing_patient = Appointment.query.filter(
        Appointment.name == name,
        Appointment.time.like(f"{appointment_date}%")
    ).first()

    if existing_patient:
        return jsonify({"error": "Patient already has an appointment on this day!"}), 400

    # Ensure a 1-hour gap for the same doctor
    one_hour_before = appointment_datetime - timedelta(hours=1)
    one_hour_after = appointment_datetime + timedelta(hours=1)

    overlapping_appointment = Appointment.query.filter(
        Appointment.doctor == doctor,
        Appointment.time >= one_hour_before.strftime("%Y-%m-%dT%H:%M"),
        Appointment.time <= one_hour_after.strftime("%Y-%m-%dT%H:%M")
    ).first()

    if overlapping_appointment:
        return jsonify({"error": "Doctor is already booked at this time! Please select a different time."}), 400

    # Add new appointment
    new_appointment = Appointment(name=name, doctor=doctor, time=time)
    db.session.add(new_appointment)
    db.session.commit()
    
    return jsonify({"message": "Appointment added successfully!"}), 201

# Delete appointment
@app.route('/appointments/<int:id>', methods=['DELETE'])
def delete_appointment(id):
    appointment = Appointment.query.get(id)
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404
    db.session.delete(appointment)
    db.session.commit()
    return jsonify({"message": "Appointment deleted successfully!"})

# Export appointments to CSV
@app.route('/export', methods=['GET'])
def export_appointments():
    appointments = Appointment.query.all()
    with open('appointments.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 'name', 'doctor', 'time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for appointment in appointments:
            writer.writerow({'id': appointment.id, 'name': appointment.name, 'doctor': appointment.doctor, 'time': appointment.time})
    return jsonify({"message": "Appointments exported successfully!"})

if __name__ == '__main__':
    app.run(debug=True)

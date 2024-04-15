
# Import statements
from flask import Blueprint, request, jsonify, make_response, current_app
import json
from src import db

patient = Blueprint('patient', __name__)

# Add a patient
@patient.route('/patient', methods=['POST'])
def add_new_patient():
    # Parse request (json)
    data = request.get_json()
    current_app.logger.info(data)

    # Extract variables
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    sex = data.get('sex')
    birthdate = data.get('birthdate')

    # Validate the input data
    if not all([first_name, last_name, sex, birthdate]):
        return jsonify({'message': 'Missing required patient information'}), 400

    # Construct the SQL insert statement
    query = f"INSERT INTO Patient (FirstName, LastName, Sex, Birthdate) VALUES ('{first_name}', '{last_name}', '{sex}', '{birthdate}')"
    current_app.logger.info(query)

    try:
        cursor = db.get_db().cursor()
        cursor.execute(query)
        db.get_db().commit()
        return jsonify({'message': 'Patient added successfully'}), 201
    except Exception as e:
        db.get_db().rollback()
        current_app.logger.error(f"Failed to add patient: {e}")
        return jsonify({'error': str(e)}), 500

# Get list of doctors a patient is seeing 
@patient.route('/patient/<int:patient_id>/doctors', methods=['GET'])
def get_patient_doctors(patient_id):
    try:
        cursor = db.get_db().cursor()
        query = f"SELECT d.DoctorID, d.FirstName, d.LastName, d.VerifiedBy FROM Doctor d " \
                f"JOIN Patient_Doctor pd ON d.DoctorID = pd.DoctorID " \
                f"WHERE pd.PatientID = '{patient_id}'"
        cursor.execute(query)
        results = cursor.fetchall()

        doctors = [
            {
                'Doctor ID': result[0],
                'First Name': result[1],
                'Last Name': result[2],
                'Verified By': result[3]
            } for result in results
        ]

        response = make_response(jsonify(doctors), 200)
        response.mimetype = 'application/json'
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Get list of prescriptions, allow optional filtering based on status of prescription
@patient.route('/patient/<int:patient_id>/prescriptions', methods=['GET'])
def get_patient_prescriptions(patient_id):
    # Retrieve optional status
    status = request.args.get('status', None)
    
    try:
        cursor = db.get_db().cursor()
        
        query = f"SELECT PrescriptionID, PharmacyID, BranchID, DrugID, Dosage, Status, PrescribedDate, PrescribedExpiration FROM Prescription WHERE PatientID = '{patient_id}'"
        
        if status:
            query += f" AND Status = '{status}'"
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        prescriptions = [
            {
                'Prescription ID': result[0],
                'Pharmacy ID': result[1],
                'Branch ID': result[2],
                'Drug ID': result[3],
                'Dosage': result[4],
                'Status': result[5],
                'Prescribed Date': result[6].strftime('%Y-%m-%d'),
                'Expiration Date': result[7].strftime('%Y-%m-%d')
            } for result in results
        ]
        
        response = make_response(jsonify(prescriptions), 200)
        response.mimetype = 'application/json'
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Allow patient to add doctor relationship
@patient.route('/patient/<int:patient_id>/doctor/<int:doctor_id>', methods=['POST'])
def add_doctor_patient_relationship(patient_id, doctor_id):
    try:
        cursor = db.get_db().cursor()
        
        # Avoid duplicates
        check_query = f"SELECT * FROM Patient_Doctor WHERE PatientID = {patient_id} AND DoctorID = {doctor_id}"
        cursor.execute(check_query)
        if cursor.fetchone():
            return jsonify({'message': 'This relationship already exists.'}), 400
        
        # Insert new doctor-patient relationship
        insert_query = f"INSERT INTO Patient_Doctor (PatientID, DoctorID) VALUES ({patient_id}, {doctor_id})"
        cursor.execute(insert_query)
        db.get_db().commit()

        return jsonify({'message': 'New doctor-patient relationship added successfully.'}), 201
    
    except Exception as e:
        db.get_db().rollback()
        return jsonify({'error': str(e)}), 500

# Allow patient to delete a relationship (does not affect prescriptions)
@patient.route('/patient/<int:patient_id>/doctor/<int:doctor_id>', methods=['DELETE'])
def delete_doctor_patient_relationship(patient_id, doctor_id):
    try:
        cursor = db.get_db().cursor()
        
        # Check relationship exists
        check_query = f"SELECT * FROM Patient_Doctor WHERE PatientID = {patient_id} AND DoctorID = {doctor_id}"
        cursor.execute(check_query)
        if not cursor.fetchone():
            return jsonify({'message': 'Doctor-patient relationship does not exist.'}), 404
        
        # Delete relationship
        delete_query = f"DELETE FROM Patient_Doctor WHERE PatientID = {patient_id} AND DoctorID = {doctor_id}"
        cursor.execute(delete_query)
        db.get_db().commit()

        return jsonify({'message': 'Doctor-patient relationship deleted successfully.'}), 200
    
    except Exception as e:
        db.get_db().rollback()
        return jsonify({'error': str(e)}), 500

# Allow patient to create a ticket
@patient.route('/tickets', methods=['POST'])
def create_ticket():
    # Parse json
    data = request.get_json()
    current_app.logger.info(data)

    # Extract variables
    patient_id = data.get('patient_id')
    text = data.get('text')
    status = data.get('status', 'Open') 

    # Validate the input data
    if not all([patient_id, text]):
        return jsonify({'message': 'Missing required information for creating a ticket'}), 400

    try:
        cursor = db.get_db().cursor()

        # Generate random adminid to assign ticket to
        cursor.execute("SELECT AdminID FROM Admin ORDER BY RAND() LIMIT 1")
        random_admin = cursor.fetchone()
        if not random_admin:
            return jsonify({'message': 'No admins available to assign the ticket'}), 500
        
        admin_id = random_admin[0]

        # Make query w/ randomly generated adminid
        query = f"INSERT INTO Ticket (PatientID, AdminID, Text, Status, Date_Created) VALUES ('{patient_id}', '{admin_id}', '{text}', '{status}', CURRENT_DATE())"
        current_app.logger.info(query)

        cursor.execute(query)
        db.get_db().commit()
        return jsonify({'message': 'Ticket created successfully'}), 201

    except Exception as e:
        db.get_db().rollback()
        current_app.logger.error(f"Failed to create ticket: {e}")
        return jsonify({'error': str(e)}), 500

# Allow patients to edit text of open tickets
@patient.route('/tickets/<int:ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    # Parse json
    data = request.get_json()
    current_app.logger.info(data)

    # Extract text data
    new_text = data.get('text')
    if not new_text:
        return jsonify({'message': 'No new text provided'}), 400

    try:
        cursor = db.get_db().cursor()

        # Check status of ticket, only open tickets can be edited
        cursor.execute(f"SELECT Status FROM Ticket WHERE TicketID = {ticket_id}")
        ticket = cursor.fetchone()
        if not ticket:
            return jsonify({'message': 'Ticket not found'}), 404
        if ticket[0] != 'Open':
            return jsonify({'message': 'Only open tickets can be updated'}), 400

        # Update the ticket text
        update_query = f"UPDATE Ticket SET Text = '{new_text}' WHERE TicketID = {ticket_id} AND Status = 'Open'"
        cursor.execute(update_query)
        db.get_db().commit()

        return jsonify({'message': 'Ticket text updated successfully'}), 200
    
    except Exception as e:
        db.get_db().rollback()
        current_app.logger.error(f"Failed to update ticket: {e}")
        return jsonify({'error': str(e)}), 500
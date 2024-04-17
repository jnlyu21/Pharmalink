
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
@patient.route('/patient/<int:patient_id>', methods=['GET'])
def get_patient_doctors(patient_id):
    try:
        cursor = db.get_db().cursor()
        query = f"SELECT d.DoctorID, d.FirstName, d.LastName FROM Doctor d " \
                f"JOIN Patient_Doctor pd ON d.DoctorID = pd.DoctorID " \
                f"WHERE pd.PatientID = '{patient_id}'"
        cursor.execute(query)
        results = cursor.fetchall()

        doctors = [
            {
                'Doctor ID': result[0],
                'First Name': result[1],
                'Last Name': result[2]
            } for result in results
        ]

        response = make_response(jsonify(doctors), 200)
        response.mimetype = 'application/json'
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@patient.route('/prescriptions/<int:patient_id>', methods=['GET'])
def get_patient_prescriptions(patient_id):
    # Retrieve optional status from the query parameters
    status = request.args.get('status', None)
    
    try:
        cursor = db.get_db().cursor()
        
        # Extended query to join with Pharmacy, Medication, Branch, and Doctor tables for more detailed info
        query = f"""
        SELECT 
            p.PrescriptionID, 
            ph.Name as PharmacyName, 
            b.Street as BranchAddress, 
            m.Name as MedicationName,
            p.Dosage, 
            p.Status, 
            DATE(p.PrescribedDate) as PrescribedDate, 
            DATE(p.PrescribedExpiration) as PrescribedExpiration,
            CONCAT(d.FirstName, ' ', d.LastName) as DoctorName
        FROM 
            Prescription p
        INNER JOIN 
            Pharmacy ph ON p.PharmacyID = ph.PharmacyID
        INNER JOIN 
            Medication m ON p.DrugID = m.DrugID
        INNER JOIN 
            Branch b ON p.BranchID = b.BranchID AND b.PharmacyID = p.PharmacyID
        INNER JOIN 
            Doctor d ON p.PrescribedBy = d.DoctorID
        WHERE 
            p.PatientID = {patient_id}
        """
        
        # Adding filtering by status if provided
        if status:
            query += f" AND p.Status = '{status}'"
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Prepare data to return as JSON
        prescriptions = [
            {
                'Prescription ID': result[0],
                'Pharmacy Name': result[1],
                'Branch Address': result[2],
                'Medication Name': result[3],
                'Dosage': result[4],
                'Status': result[5],
                'Prescribed Date': result[6],
                'Expiration Date': result[7],
                'Prescribing Doctor': result[8]
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

# Allow patient to create ticket
@patient.route('/tickets/<int:patient_id>', methods=['POST'])
def create_ticket(patient_id):
    # Parse JSON
    data = request.get_json()
    current_app.logger.info(data)

    # Extract text from JSON
    text = data.get('text')

    # Validate the input data
    if not text:
        return jsonify({'message': 'Missing required text information for creating a ticket'}), 400

    try:
        cursor = db.get_db().cursor()

        # Select a random admin to assign the ticket to
        cursor.execute("SELECT AdminID FROM Admin ORDER BY RAND() LIMIT 1")
        random_admin = cursor.fetchone()
        if not random_admin:
            return jsonify({'message': 'No admins available to assign the ticket'}), 500
        admin_id = random_admin[0]

        # Get the next TicketID
        cursor.execute("SELECT MAX(TicketID) FROM Ticket")
        max_id_result = cursor.fetchone()
        next_ticket_id = max_id_result[0] + 1 if max_id_result[0] is not None else 1

        # Insert the new ticket with a manually determined TicketID
        query = f"INSERT INTO Ticket (TicketID, PatientID, AdminID, Text, Status, Date_Created) VALUES ('{next_ticket_id}', '{patient_id}', '{admin_id}', '{text}', 'Open', CURRENT_DATE())"
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
    new_text = data.get('new_text')
    if not new_text:
        return jsonify({'message': 'No new text provided'}), 400

    try:
        cursor = db.get_db().cursor()

        # Update the ticket text
        update_query = f"UPDATE Ticket SET Text = '{new_text}' WHERE TicketID = {ticket_id} AND Status = 'Open'"
        cursor.execute(update_query)
        db.get_db().commit()

        return jsonify({'message': 'Ticket text updated successfully'}), 200
    
    except Exception as e:
        db.get_db().rollback()
        current_app.logger.error(f"Failed to update ticket: {e}")
        return jsonify({'error': str(e)}), 500
    
@patient.route('/tickets/<int:patient_id>', methods=['GET'])
def get_open_tickets(patient_id):
    try:
        cursor = db.get_db().cursor()

        # Select tickets that are open given patientid
        query = f"""
        SELECT TicketID, Text, Date_Created, AdminID
        FROM Ticket
        WHERE PatientID = {patient_id} AND Status = 'Open'
        """

        cursor.execute(query)
        results = cursor.fetchall()

        # Check if there are tickets
        if not results:
            return jsonify({'message': 'No open tickets found for this patient'}), 404

        
        tickets = []
        for result in results:
            tickets.append({
                'Ticket ID': result[0],
                'Text': result[1],
                'Date Created': result[2].strftime('%Y-%m-%d'),  # Format the date
                'Admin ID': result[3]
            })

        response = make_response(jsonify(tickets), 200)
        response.mimetype = 'application/json'
        return response
    
    except Exception as e:
        current_app.logger.error(f"Failed to retrieve open tickets: {e}")
        return jsonify({'error': str(e)}), 500
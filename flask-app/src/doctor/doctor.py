
# Import statements
from flask import Blueprint, request, jsonify, make_response, current_app
import json
from src import db

doctor = Blueprint('doctor', __name__)

# Delete a doctor from the database
@doctor.route('/doctor/<int:admin_id>/<int:doctor_id>', methods=['DELETE'])
def delete_doctor(admin_id, doctor_id):
    cursor = db.get_db().cursor()

    # Cannot delete if doctor has prescriptions
    check_query = f'SELECT COUNT(*) FROM Prescription WHERE PrescribedBy = "{doctor_id}"'
    cursor.execute(check_query)
    if cursor.fetchone()[0] > 0:
        return 'Cannot delete doctor with active prescriptions.', 400
    
    # Cannot delete if doctor has patients
    check_query = f'SELECT COUNT(*) FROM Patient_Doctor WHERE DoctorId = "{doctor_id}"'
    cursor.execute(check_query)
    if cursor.fetchone()[0] > 0:
        return 'Cannot delete doctor with patients.', 400
    try:
        # Proceed with deletion if no dependencies
        delete_query = f'DELETE FROM Doctor WHERE DoctorID = "{doctor_id}"'
        cursor.execute(delete_query)
        db.get_db().commit()
        return 'Doctor successfully deleted', 200
    except Exception as e:
        db.get_db().rollback()
        return str(e), 500

# Add a doctor to the database
@doctor.route('/doctor/<int:admin_id>', methods=['POST'])
def add_new_doctor(admin_id):

    
    # Parse req
    the_data = request.json
    current_app.logger.info(the_data)

    # Extract vars
    first_name = the_data['first_name']
    last_name = the_data['last_name']
    verified_by = admin_id

    # Query
    query = 'INSERT INTO Doctor (FirstName, LastName, VerifiedBy) VALUES ("'
    query += first_name + '", "'
    query += last_name + '", "'
    query += str(verified_by) + '")'
    current_app.logger.info(query)

    # Executing insert
    cursor = db.get_db().cursor()
    cursor.execute(query)
    db.get_db().commit()
    
    return 'Doctor added successfully!'

# Retrieve information for all doctors
@doctor.route('/doctor', methods=['GET'])
def get_all_doctors():
    try:
        cursor = db.get_db().cursor()
        cursor.execute(
            "SELECT DoctorID, FirstName, LastName, VerifiedBy FROM Doctor"
        )
        row_headers = [x[0] for x in cursor.description] 
        json_data = []
        results = cursor.fetchall()
        for result in results:
            json_data.append(dict(zip(row_headers, result)))

        response = make_response(jsonify(json_data), 200)
        response.mimetype = 'application/json'
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get a doctor's patients
@doctor.route('/doctor/<int:doctor_id>/patients', methods=['GET'])
def get_doctors_patients(doctor_id):
    cursor = db.get_db().cursor()

    query = f'SELECT p.patientID, p.FirstName, p.LastName, p.Sex, p.Birthdate FROM Patient p JOIN Patient_Doctor pd ON p.patientID = pd.PatientID WHERE pd.DoctorID = "{doctor_id}"'
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Preparing JSON data
    patients = []
    for result in results:
        patients.append({
            'PatientID': result[0],
            'FirstName': result[1],
            'LastName': result[2],
            'Sex': result[3],
            'Birthdate': result[4].strftime('%Y-%m-%d')  
        })

    return jsonify(patients), 200

# View doctor's prescriptions for a certain patient
@doctor.route('/prescriptions/<int:patient_id>', methods=['GET']) #can also be used by patients to view their prescriptions
def get_prescriptions_for_patient(patient_id):
    the_data = request.json
    current_app.logger.info(the_data)

    # Extracting variables from the request
    doctor_id = the_data['doctor_id']

    try:
        cursor = db.get_db().cursor()

        query = 'SELECT p.PrescriptionID, ph.Name as PharmacyName, b.BranchID, p.Dosage, p.Status, '
        query += 'p.PrescribedDate, p.PrescribedExpiration, m.Name as MedicationName '
        query += 'FROM Prescription p '
        query += 'JOIN Pharmacy ph ON p.PharmacyID = ph.PharmacyID '
        query += 'JOIN Medication m ON p.DrugID = m.DrugID '
        query += f'WHERE p.PrescribedBy = "{doctor_id}" AND p.PatientID = "{patient_id}"'

        cursor.execute(query)
        results = cursor.fetchall()

        prescriptions = [
            {
                'Prescription ID': result[0],
                'Pharmacy Name': result[1],
                'Branch ID': result[2],
                'Dosage': result[3],
                'Status': result[4],
                'Prescribed Date': result[5].strftime('%Y-%m-%d'),
                'Expiration Date': result[6].strftime('%Y-%m-%d'),
                'Medication Name': result[7]
            } for result in results
        ]

        response = make_response(jsonify(prescriptions), 200)
        response.mimetype = 'application/json'
        return response
    except Exception as e:
        db.get_db().rollback()
        return jsonify({"error": str(e)}), 500

# Create a prescription for a patient
@doctor.route('/prescriptions/<int:patient_id>', methods=['POST'])
def create_prescription(patient_id):
    the_data = request.json
    current_app.logger.info(the_data)

    # Extracting variables from the request
    doctor_id = the_data['doctor_id']
    patient_id = patient_id
    pharmacy_id = the_data['pharmacy_id']
    branch_id = the_data['branch_id']
    drug_id = the_data['drug_id']
    dosage = the_data['dosage']
    status = the_data['status']
    prescribed_date = the_data['prescribed_date']
    prescribed_expiration = the_data['prescribed_expiration']

    # Constructing the query
    query = 'INSERT INTO Prescription (PrescribedBy, PatientID, PharmacyID, BranchID, DrugID, Dosage, Status, PrescribedDate, PrescribedExpiration) VALUES ('
    query += f'"{doctor_id}", "{patient_id}", "{pharmacy_id}", "{branch_id}", "{drug_id}", "{dosage}", "{status}", "{prescribed_date}", "{prescribed_expiration}")'

    try:
        cursor = db.get_db().cursor()
        cursor.execute(query)
        db.get_db().commit()
        return 'Prescription successfully created', 201
    except Exception as e:
        db.get_db().rollback()
        return str(e), 500

# Allow doctor to cancel a prescription    
@doctor.route('/prescriptions/<int:prescription_id>', methods=['PUT'])
def cancel_prescription(prescription_id):
    try:
        cursor = db.get_db().cursor()

        # Check the current status to ensure it is 'Active' before cancelling
        status_check_query = f'SELECT Status FROM Prescription WHERE PrescriptionID = "{prescription_id}"'
        cursor.execute(status_check_query)
        current_status = cursor.fetchone()
        if not current_status:
            return 'Prescription not found.', 404
        if current_status[0] != 'Active':
            return 'Prescription cannot be cancelled, as it is not in an Active state.', 400

        # Update the prescription status to 'Cancelled'
        update_query = f'UPDATE Prescription SET Status = "Cancelled" WHERE PrescriptionID = "{prescription_id}"'
        cursor.execute(update_query)
        db.get_db().commit()
        return 'Prescription status updated to Cancelled.', 200
    except Exception as e:
        db.get_db().rollback()
        return str(e), 500
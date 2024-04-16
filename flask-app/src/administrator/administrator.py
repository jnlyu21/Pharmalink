
# Import statements
from flask import Blueprint, request, jsonify, make_response, current_app
import json
from src import db

administrator = Blueprint('administrator', __name__)

# Retrieve information for all doctors
@administrator.route('/doctor', methods=['GET'])
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
    

# Display information of all pharmacists
@administrator.route('/pharmacist', methods=['GET'])
def get_all_pharmacists():
    try:
        cursor = db.get_db().cursor()
        cursor.execute(
            "SELECT PharmacistID, BranchID, PharmacyID, FirstName, LastName FROM Pharamcist"
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


# Add a doctor to the database
@administrator.route('/doctor/<int:admin_id>', methods=['POST'])
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

# Delete a doctor from the database
@administrator.route('/doctor/<int:admin_id>/<int:doctor_id>', methods=['DELETE'])
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

# Update doctor information in the database
@administrator.route('/doctor/<int:admin_id>/<int:doctor_id>', methods=['PUT'])
def update_doctor(admin_id, doctor_id):
    the_data = request.json
    current_app.logger.info(the_data)

    # Extracting variables
    first_name = the_data.get('first_name', '')
    last_name = the_data.get('last_name', '')
    verified_by = the_data.get('verified_by', '')

    # Query
    query = f'UPDATE Doctor SET '
    updates = []
    if first_name:
        updates.append(f'FirstName = "{first_name}"')
    if last_name:
        updates.append(f'LastName = "{last_name}"')
    if verified_by:
        updates.append(f'VerifiedBy = "{admin_id}"')

    query += ', '.join(updates)
    query += f' WHERE DoctorID = "{doctor_id}"'
    current_app.logger.info(query)

    try:
        cursor = db.get_db().cursor()
        cursor.execute(query)
        db.get_db().commit()
        return 'Doctor information updated successfully', 200
    except Exception as e:
        db.get_db().rollback()
        return str(e), 500
    
# Add pharmacist
@administrator.route('/pharmacist/<int:admin_id>', methods=['POST'])
def add_pharmacist():
    try:
        # Collecting data 
        the_data = request.json
        branch_id = the_data['branch_id']
        pharmacy_id = the_data['pharmacy_id']
        first_name = the_data['first_name']
        last_name = the_data['last_name']

        # Construct query
        query = 'INSERT INTO Pharmacist (BranchID, PharmacyID, FirstName, LastName) VALUES ('
        query += f'"{branch_id}", "{pharmacy_id}", "{first_name}", "{last_name}")'

        # Execute
        cursor = db.get_db().cursor()
        cursor.execute(query)
        db.get_db().commit()
        return 'Pharmacist added successfully!', 201

    except Exception as e:
        db.get_db().rollback()
        return jsonify({"error": str(e)}), 500
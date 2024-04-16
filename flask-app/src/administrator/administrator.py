
# Import statements
from flask import Blueprint, request, jsonify, make_response, current_app
import json
from src import db

administrator = Blueprint('administrator', __name__)

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
    
    
# Display information of all pharmacists
@pharmacist.route('/pharmacist', methods=['GET'])
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



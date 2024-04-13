
# import statements
from flask import Blueprint, request, jsonify, make_response, current_app
import json
from src import db


pharmacist = Blueprint('pharmacist', __name__)

# Todo: get all pharmacists
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

# Todo: add pharmacist

# Todo: remove pharmacist


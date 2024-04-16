
# Import statements
from flask import Blueprint, request, jsonify, make_response, current_app
import json
from src import db

administrator = Blueprint('administrator', __name__)


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
    
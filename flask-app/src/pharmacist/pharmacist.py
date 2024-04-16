
# import statements
from flask import Blueprint, request, jsonify, make_response, current_app
import json
from src import db


pharmacist = Blueprint('pharmacist', __name__)

    
# Allow pharmacist to change prescription status to complete
@pharmacist.route('/prescriptions/<int:prescription_id>', methods=['PUT'])
def complete_prescription(prescription_id):
    try:
        # Check if the prescription is currently active
        cursor = db.get_db().cursor()
        status_check_query = f'SELECT Status FROM Prescription WHERE PrescriptionID = "{prescription_id}"'
        cursor.execute(status_check_query)
        current_status = cursor.fetchone()
        if not current_status:
            return 'Prescription not found.', 404
        if current_status[0] != 'Active':
            return 'Prescription is not Active, cannot be completed.', 400

        # Update the prescription status to 'Complete'
        update_query = f'UPDATE Prescription SET Status = "Complete" WHERE PrescriptionID = "{prescription_id}"'
        cursor.execute(update_query)
        db.get_db().commit()
        return 'Prescription status updated to Complete.', 200
    except Exception as e:
        db.get_db().rollback()
        return str(e), 500

# Allow pharmacist to view stock of current branch
@pharmacist.route('/stock/<int:pharmacy_id>/<int:branch_id>/<int:drug_id>', methods=['GET'])
def check_drug_availability(pharmacy_id, branch_id, drug_id):
    try:
        cursor = db.get_db().cursor()
        # Query to check availability of certain drugid based on pharmacy and branch
        query = f'SELECT Quantity FROM Stock_Item WHERE PharmacyID = "{pharmacy_id}" AND BranchID = "{branch_id}" AND DrugID = "{drug_id}"'
        cursor.execute(query)
        result = cursor.fetchone()

        if not result:
            return jsonify({'message': 'Drug not found in this branch or pharmacy.'}), 404
        quantity = result[0]
        
        availability = "Available" if quantity > 0 else "Not Available"
        return jsonify({
            'Pharmacy ID': pharmacy_id,
            'Branch ID': branch_id,
            'Drug ID': drug_id,
            'Quantity': quantity,
            'Availability': availability
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# When a pharmacist fulfills an order, the quantity of the drug must be deducted from the branch's stock
@pharmacist.route('/stock/<int:pharmacy_id>/<int:branch_id>/<int:drug_id>', methods=['PUT'])
def deduct_drug_stock(pharmacy_id, branch_id, drug_id):
    try:
        the_data = request.json
        used_quantity = the_data['used_quantity']

        cursor = db.get_db().cursor()
        
        # Check there sufficient stock of drug
        check_query = f'SELECT Quantity FROM Stock_Item WHERE PharmacyID = "{pharmacy_id}" AND BranchID = "{branch_id}" AND DrugID = "{drug_id}"'
        cursor.execute(check_query)
        result = cursor.fetchone()
        if not result:
            return jsonify({'message': 'Drug not in this branch'})
        current_quantity = result[0]

        if current_quantity < used_quantity:
            return jsonify({'message': 'We do not have sufficient quantity of the medication to fulfill this order'})
        
        new_quantity = current_quantity - used_quantity
        update_query = f'UPDATE Stock_Item SET Quantity = "{new_quantity}" WHERE PharmacyID = "{pharmacy_id}" AND BranchID = "{branch_id}" AND DrugID = "{drug_id}"'
        cursor.execute(update_query)
        db.get_db.commit()

        return jsonify({'message': 'Stock updated successfully.', 'New Quantity': new_quantity}), 200
    except Exception as e:
        db.get_db().rollback()
        return jsonify({"error": str(e)}), 500
    
# TODO: allow pharmacist to make an order, add quantity to current drug's quantity. If drug is not in Stock_Item table for branch, add it and make a new randomly generated SKU (unique)
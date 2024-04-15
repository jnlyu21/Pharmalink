# Import statements
from flask import Blueprint, request, jsonify, make_response, current_app
import json
from src import db

# blueprint for dropdown menu so users can input names instead of id #s
dropdowns = Blueprint('dropdowns', __name__)

@dropdowns.route('/doctors', methods=['GET'])
def get_doctors():
    search_query = request.args.get('search', '') 
    cursor = db.get_db().cursor()
    query = """
        SELECT DoctorID, CONCAT(FirstName, ' ', LastName) AS Name FROM Doctor
        WHERE CONCAT(FirstName, ' ', LastName) LIKE %s
    """
    search_term = f"%{search_query}%"
    cursor.execute(query, (search_term,))
    doctors = cursor.fetchall()
    return jsonify([{'id': doc[0], 'name': doc[1]} for doc in doctors])

@dropdowns.route('/patients', methods=['GET'])
def get_patients():
    search_query = request.args.get('search', '') 
    cursor = db.get_db().cursor()
    query = """
        SELECT patientID, CONCAT(FirstName, ' ', LastName) AS Name FROM Patient
        WHERE CONCAT(FirstName, ' ', LastName) LIKE %s
    """
    search_term = f"%{search_query}%"
    cursor.execute(query, (search_term,))
    patients = cursor.fetchall()
    return jsonify([{'id': patient[0], 'name': patient[1]} for patient in patients])

@dropdowns.route('/pharmacies', methods=['GET'])
def get_pharmacies():
    search_query = request.args.get('search', '')
    cursor = db.get_db().cursor()
    query = """
        SELECT PharmacyID, Name FROM Pharmacy
        WHERE Name LIKE %s
    """
    search_term = f"%{search_query}%"
    cursor.execute(query, (search_term,))
    pharmacies = cursor.fetchall()
    return jsonify([{'id': pharmacy[0], 'name': pharmacy[1]} for pharmacy in pharmacies])

@dropdowns.route('/drugs', methods=['GET'])
def get_drugs():
    search_query = request.args.get('search', '')
    cursor = db.get_db().cursor()
    query = """
        SELECT DrugID, Name FROM Medication
        WHERE Name LIKE %s
    """
    search_term = f"%{search_query}%"
    cursor.execute(query, (search_term,))
    drugs = cursor.fetchall()
    return jsonify([{'id': drug[0], 'name': drug[1]} for drug in drugs])
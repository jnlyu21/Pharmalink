
# import statements
from flask import Blueprint, request, jsonify, make_response, current_app
import json
from src import db


patient = Blueprint('patient', __name__)

# Todo: get patient route

# Todo: get patient's prescriptions based on patient id
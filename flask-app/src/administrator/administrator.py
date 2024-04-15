
# Import statements
from flask import Blueprint, request, jsonify, make_response, current_app
import json
from src import db

administrator = Blueprint('administrator', __name__)

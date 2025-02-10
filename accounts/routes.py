# accounts/routes.py
from flask import Blueprint, request, jsonify
from accounts.models import get_users, get_user, update_user,add_user

account_bp = Blueprint('accounts', __name__, url_prefix='/accounts')

@account_bp.route('/<username>', methods=['GET'])
def get_account(username):
    """Récupère les informations d'un compte."""
    user = get_user(username)
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404

@account_bp.route('/<username>', methods=['POST'])
def modify_account(username):
    """Modifie le compte utilisateur (par exemple, la séquence de geste associée)."""
    data = request.get_json()
    if update_user(username, data):
        return jsonify({"success": True})
    return jsonify({"error": "User not found or update failed"}), 404



@account_bp.route('/', methods=['GET'])
def list_accounts():
    return jsonify(get_users())


@account_bp.route('/add', methods=['POST'])
def add_account():
    data = request.get_json()
    username = data.get("username")
    gestures = data.get("gestures")
    if not username or not gestures:
        return jsonify({"error": "Missing username or gestures"}), 400
    if add_user({"username": username, "gesture_sequence": gestures}):
        return jsonify({"success": True})
    else:
        return jsonify({"error": "User already exists"}), 409

@account_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    gesture_attempt = data.get("gesture")
    user = get_user(username)
    if not user:
        return jsonify({"error": "User not found"}), 404
    if user.get("gesture_sequence") == gesture_attempt:
        return jsonify({"success": True})
    return jsonify({"error": "Gesture mismatch"}), 401
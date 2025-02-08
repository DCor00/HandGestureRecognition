users = [
    {"username": "user1", "gesture_sequence": ["like", "peace", "peace_inverted"]},
    {"username": "user2", "gesture_sequence": ["dislike", "like", "like"]},
    {"username": "user3", "gesture_sequence": ["peace", "peace", "thumbs_down"]}
]

def get_users():
    return users

def get_user(username):
    return next((user for user in users if user["username"] == username), None)

def update_user(username, new_data):
    user = get_user(username)
    if user:
        user.update(new_data)
        return True
    return False

def add_user(new_user):
    if get_user(new_user["username"]) is None:
        users.append(new_user)
        return True
    return False
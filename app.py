from flask import Flask, request, jsonify
import os
from ct import handle_create_ticket
from conv import handle_ticket_info
from login_user import handle_login_user
from team import get_team_structure, handle_team_availability

app = Flask(__name__)

team_structure = get_team_structure()

@app.route('/team', methods=['GET'])
def team():
    return handle_team_availability(request, team_structure)


@app.route('/ct', methods=['POST'])
def create_ticket():
    return handle_create_ticket(request)

@app.route('/conv', methods=['POST'])
def conv():
    return handle_ticket_info(request)

@app.route('/login_user', methods=['POST'])
def login_user():
    return handle_login_user(request)

@app.route('/ping', methods=['POST'])
def ping():
    return "the service is alive"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

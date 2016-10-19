from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
import os
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import *

@app.route('/create/')
def hello():
	ps = PokerSession(3.0)
	db.session.add(ps)
	db.session.commit()
	return "Record created"

@app.rout('/<new_session_id>/create-session/')
def create_session(new_session_id):
	admin_name = 'Aaron'
	admin_email = 'amc424@cornell.edu'
	admin_stack = 20.00
	admin_seat_num = 1
	small_blind = .20
	
	new_session = PokerSession(new_session_id,[], None, small_blind, admin_seat_num)
	adminPlayer = Player(admin_name,admin_email,admin_stack, admin_seat_num, True, True,False,False)
	new_session.players.append(adminPlayer)
	
@app.rout('/<current_session_id>/add-player/')
def add_player(current_session_id):
	player_name = 'James'
	player_email = 'jamesemail@gmail.com'
	player_stack = 20.00
	player_seat_num = 2

	current_session = PokerSession.query.filter_by(session_id = current_session_id)
	current_session.players.append(Player(player_name,player_email,player_stack,player_seat_num, True,True,False,False)
	
@app.rout('/<current_session_id>/start-session/')
def start-session(current_session_id)
	current_session = PokerSession.query.filter_by(session_id = current_session_id)
	
	deck = Deck()
	hole_cards = []
	for i in range(0,len(current_session.players)):
		hole_cards.append([deck.drawCard(),deck.drawCard()])
	board = [deck.drawCard(),deck.drawCard(),deck.drawCard(),deck.drawCard(),deck.drawCard()]
	
	#initialize poker hand bet sizes with the button location and blind sizes
	# street always starts at 0
	button_position = (Player.query.filter_by(poker_session = current_session_id, has_button = True)).seat_num
	current_session.current_hand = PokerHand(button_position_current_session.small_blind, hole_cards, board) 



@app.route('/<seat_num>/bet/')
def bet_happened(player_name):
	

if __name__ == '__main__':
	app.run()
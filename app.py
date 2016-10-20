from flask import Flask, request, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
import os
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import *
from hand_evaluator import Card, Deck
from bet_logic import BetList, PlayerObject

@app.route('/create/')
def hello():
	
	return "Record created"

@app.route('/create-session/')
def create_session():
	# db.create_all()

	#create admin player
	new_admin_player = Player(username = 'Aaron', seat_num = 1, has_button = False, stack_size = 20.00)

	#create new session
	new_session = PokerSession(small_blind = 0.1)
	#add admin to the session
	new_session.players = [new_admin_player]
	new_admin_player.poker_session = new_session


	db.session.add(new_session)
	db.session.add(new_admin_player)
	db.session.commit()

	#redirect to lobby
	return redirect(url_for('lobby', current_session_id = str(new_session.id)))

@app.route('/<current_session_id>/lobby/')
def lobby(current_session_id):

	return "welcome to lobby"


	
@app.route('/<current_session_id>/lobby/add-player/')
def add_player(current_session_id):

	#retrieve the current session
	current_session = PokerSession.query.filter_by(id = current_session_id).first()

	#add a player to the this session
	new_player = Player(username = 'James', seat_num =6, stack_size = 20.00)
	new_player1 = Player(username = 'James2', seat_num =3, stack_size = 20.00)
	new_player2 = Player(username = 'James3', seat_num = 4, stack_size =20.00)
	new_player3 = Player(username = 'James4', seat_num = 5, stack_size =20.00, has_button = True)


	current_session.players.append(new_player)
	new_player.poker_session = current_session

	current_session.players.append(new_player1)
	new_player1.poker_session = current_session

	current_session.players.append(new_player2)
	new_player2.poker_session = current_session

	current_session.players.append(new_player3)
	new_player3.poker_session = current_session

	db.session.add(new_player)
	db.session.add(new_player1)
	db.session.add(new_player2)
	db.session.add(new_player3)

	db.session.commit()
	return str(len(current_session.players))

	
@app.route('/<current_session_id>/lobby/deal-hand/')
def start_session(current_session_id):

	#retrieve current session and number of players
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	num_players = len(current_session.players)

	#deal hole cards and board
	deck = Deck()
	current_hole_cards = []
	for i in range(0,len(current_session.players)):
		current_hole_cards.append([deck.drawCard(),deck.drawCard()])
	current_board = [deck.drawCard(),deck.drawCard(),deck.drawCard(),deck.drawCard(),deck.drawCard()]
	
	#retrieve button position
	button_position = (Player.query.filter_by(poker_session_id = current_session_id, has_button = True).first()).seat_num

	#createt BetList object to store hand information
	#populate with PlayerObject objects corresponding to seat numbers from PokerSession -> Players data
	current_bet_list = BetList(num_players = num_players, button_position = button_position)
	for i in range(0,num_players):
		current_bet_list.player_list.append(PlayerObject(current_session.players[i].seat_num))

	#initialize the bet list by forcing blinds to post
	current_bet_list.post_blinds(current_session.small_blind)
	## need to actually remove money from player stacks
	for player_object in current_bet_list.player_list:
		if player_object.total_bet > 0:
			player = Player.query.filter_by(poker_session_id = current_session_id, seat_num = player_object.seat_num).first()
			player.stack_size -= player_object.total_bet


	new_hand = PokerHand(street = 0, bet_list_object = current_bet_list, hole_cards = current_hole_cards, \
												board = current_board ) 
	current_session.current_hand = new_hand
	db.session.add(new_hand)
	db.session.commit()

	#return redirect(url_for('playing_hand', current_session_id = current_session_id))

	return 'Current Bets:{0} \nHole Cards:{1} \n Board:{2}'.format(str(current_bet_list.player_list), str(current_hole_cards), str(current_board)) 

@app.route('/<current_session_id>/lobby/<seat_num>/<bet_size>/bet/')
def bet_happened(current_session_id, seat_num, bet_size):
	seat_num = int(seat_num)
	bet_size = float(bet_size)

	#get sesssion and player trying to bet
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_player = Player.query.filter_by(poker_session_id = current_session_id, seat_num = seat_num).first()

	#update player stack and add bet to the bet list
	current_player.stack_size -= bet_size
	(current_session.current_hand.bet_list_object.get_player_at_seat(seat_num)).total_bet += bet_size

	
	return str(current_session.current_hand.bet_list_object.player_list)



if __name__ == '__main__':
	app.run(debug = True)
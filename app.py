from flask import Flask, request, redirect, url_for, render_template
from flask.ext.sqlalchemy import SQLAlchemy
import os
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

from models import *
from hand_evaluator import Card, Deck
from bet_logic import BetList, PlayerObject


@app.route('/')
def index():
	return render_template('index.html')

@app.route('/create-session/', methods=['POST'])
def create_session():
	print('HERE')
	print(request.form)
	print(request.form['username'])
	print(request.form['email'])
	print(request.form['session-name'])
	print(request.form['max-buy-in'])
	print(request.form['player-stack'])
	print(request.form['small-blind'])
	# print(request.form['big-blind'])

	#create admin player
	new_admin_player = Player(username = request.form['username'].lower(),
		seat_num = 5, 
		has_button = False, 
		is_admin = True,
		stack_size = float(request.form['player-stack']))

	#create dummy player for testing purposes
	dummy_player = Player(username = 'aaron', 
		seat_num = 9, 
		has_button = False, 
		stack_size = float(request.form['player-stack']))

	#create new session
	small_blind = float(request.form['small-blind'])
	new_session = PokerSession(name=request.form['session-name'].lower(), 
		small_blind = small_blind, big_blind = 2*small_blind, 
		max_buy_in = float(request.form['max-buy-in']))
	#add admin to the session
	new_session.players = [new_admin_player, dummy_player]
	new_admin_player.poker_session = new_session


	db.session.add(new_session)
	db.session.add(new_admin_player)
	db.session.add(dummy_player)
	db.session.commit()

	#redirect to lobby
	return redirect(url_for('poker_room', 
		current_session_id = str(new_session.id),
		player_id = str(new_admin_player.id)))

@app.route('/<current_session_id>/<player_id>/')
def poker_room(current_session_id, player_id):
	results = {}

	#retrieve the current session
	current_session = PokerSession.query.filter_by(
		id = current_session_id).first()

	current_player = Player.query.filter_by(
		id = player_id).first()

	# if hand in session return user's cards and board
	if current_session.hand_in_session:
		# TODO: return cards etc
		pass
	else:
		results['board'] = []
		results['hand'] = []

	current_player.stack_size = int(current_player.stack_size)
	print(current_session.players)
	results['player'] = current_player
	results['session'] = current_session

	return render_template('poker-session.html', results=results)


	
@app.route('/<current_session_id>/<admin_id>/add-player/', methods=['POST'])
def add_player(current_session_id, admin_id):

	json_data = request.json

	#retrieve the current session
	current_session = PokerSession.query.filter_by(id = current_session_id).first()

	#add a player to the this session
	new_player = Player(username = json_data['email'], email = json_data['email'], seat_num = json_data['seat_num'])
	current_session.players.append(new_player)

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

from flask import Flask, request, redirect, url_for, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import json
import os
import logging
import redis
import gevent
from flask_sockets import Sockets

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
# set up db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# Set up jinja2 functionality
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
# Set up redis
REDIS_URL = os.environ['REDIS_URL']
REDIS_CHAN = 'gamestate'
# set up sockets
sockets = Sockets(app)
redis = redis.from_url(REDIS_URL)


from models import *
from hand_evaluator import Card, Deck
from bet_logic import *
from copy import deepcopy


###################################################
#												  #
#                 App Routes                      #
#												  #
###################################################

@app.route('/')
def index():
	return render_template('index.html')


@app.route('/create-session/', methods=['POST'])
def create_session():

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

	return redirect(url_for('poker_room', current_session_id=new_session.id,
		player_id=new_admin_player.id))


def game_and_session_info(current_session):
	if current_session.poker_hand:
		game_state = current_session.poker_hand.game_state
		results = get_game_state_dict(current_session.id)
		if game_state.street != 0:
			results['board'] = [card.get_string_tuple() for card in game_state.board][:(2+game_state.street)]
		else:
			results['board'] = []
		results['currently_playing_seats'] = {i : False for i in range(1,11)}
		for player in current_session.players:
			results['currently_playing_seats'][player.seat_num] = \
			player.seat_num in [x.seat_num for x in game_state.player_list]
			
	else:
		results = {'board': []}
		results['currently_playing_seats'] = {i : False for i in range(1,11)}


@app.route('/<current_session_id>/show-gamestate')
def show_gamestate(current_session_id):
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_game_state = current_hand.game_state
	current_street = current_game_state.street

	return 'Player Info: {0}, Next Seat to act: {1}, Street {2}'.format(str(current_game_state.player_list) , current_game_state.player_to_act.seat_num,
			current_game_state.street) 



def retrieve_gamestate(current_session_id, player_id):

	#retrieve the current session
	
	
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_player = Player.query.filter_by(id = player_id).first()
	results = game_and_session_info(current_session)

	if current_session.poker_hand:
		current_hand = current_session.poker_hand
		current_game_state = current_hand.game_state
		winning_players = {x : False for x in range(1,11)}
		winning_hands ={}
		winning_hole_cards = {}
		pot_sizes = {}

		if current_game_state.pause_for_hand_end == True:
			pot_list = current_game_state.get_all_winnings()

			for x in pot_list:
				winning_players[x[0].seat_num] = True
				winning_hole_cards[x[0].seat_num] = [card.get_string_tuple() for card in x[0].hole_cards]
				winning_hands[x[0].seat_num] = [card.get_string_tuple() for card in current_game_state.get_best_hand(x[0])]
				pot_sizes[x[0].seat_num] = x[1]

		results['winning_players']=  winning_players
		results['winning_hole_cards'] = winning_hole_cards
		results['winning_hands'] = winning_hands
		results['pot_sizes'] = pot_sizes

	if results['currently_playing_seats'][current_player.seat_num]:
		results['hole_cards'] = [card.get_string_tuple() for card in \
			current_game_state.get_player_at_seat(current_player.seat_num).hole_cards]
	else:
		results['hole_cards'] = []

	return json.dumps(results)


@app.route('/<current_session_id>/<player_id>/')
def poker_room(current_session_id, player_id):

	#retrieve the current session
	current_session = PokerSession.query.filter_by(
		id = current_session_id).first()

	current_player = Player.query.filter_by(
		id = player_id).first()

	results = game_and_session_info(current_session)
	if results['currently_playing_seats'][current_player.seat_num]:
		game_state = current_session.poker_hand.game_state
		results['hole_cards'] = [card.get_string_tuple() for card in \
			game_state.get_player_at_seat(current_player.seat_num).hole_cards]

	current_player.stack_size = int(current_player.stack_size)
	results['player'] = current_player
	results['session'] = current_session
	# results['other_hole_cards'] = [None,[('2', 'hearts'), ('2', 'hearts')],
	# [('2', 'hearts'), ('2', 'hearts')],
	# [('2', 'hearts'), ('2', 'hearts')],
	# [('2', 'hearts'), ('2', 'hearts')],
	# [('2', 'hearts'), ('2', 'hearts')],
	# [('2', 'hearts'), ('2', 'hearts')],
	# [('2', 'hearts'), ('2', 'hearts')],
	# [('2', 'hearts'), ('2', 'hearts')],
	# [('2', 'hearts'), ('2', 'hearts')],
	# [('2', 'hearts'), ('2', 'hearts')]]
	results['other_hole_cards'] = [[]*10]

	return render_template('poker-session.html', results=results)

	
# @app.route('/<current_session_id>/<admin_id>/add-player/', methods=['POST'])
def add_player(current_session_id, admin_id, email, seat_num):

	json_data = request.json

	#retrieve the current session
	current_session = PokerSession.query.filter_by(id = current_session_id).first()

	#add a player to the this session
	new_player = Player(username = email, 
		email = email, 
		seat_num = seat_num,
		stack_size=current_session.max_buy_in)
	current_session.players.append(new_player)

	db.session.commit()
	# return 'Success.'



# @app.route('/<current_session_id>/deal-hand/', methods=['POST'])
def deal_hand(current_session_id):

	#retrieve current session and number of players
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	num_players = len(current_session.players)
	filled_seats = [player.seat_num for player in current_session.players]

	#retrieve button position
	button_position = random.choice(filled_seats)

	#Make a gamestate for the new hand. Deal cards and post blinds
	new_game_state = make_new_game_state(current_session_id, button_position, current_session.small_blind)

	#add this gamestate to the current hand in the db
	current_hand = PokerHand(game_state = new_game_state)

	#establish connection between hand and session
	current_session.poker_hand = current_hand
	current_hand.poker_session = current_session

	db.session.add(current_hand)
	db.session.commit()

	return 'Success.'


# @app.route('/<current_session_id>/<player_id>/<bet_size>/bet/', methods=['POST'])
def bet(current_session_id, player_id, bet_size):


	player_id = int(player_id)
	bet_size = float(bet_size)

	#get session, gamestate, player trying to bet, and street
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_player = Player.query.filter_by(id = player_id, poker_session_id = current_session_id,).first()
	seat_num = current_player.seat_num
	current_game_state = current_hand.game_state
	current_player_object = current_game_state.get_player_at_seat(seat_num)
	current_street = current_game_state.street

	if current_player_object == current_game_state.player_to_act:

		#If the player is able to bet, it means no one has entered the pot and thus
		#the player must be the last_valid_raiser
		current_game_state.last_valid_raiser = current_player_object

		#Update player stack and add bet to the bet list
		#Can remove betsize from stack directly, because player cannot bet
		# unless no other player has bet yet (i.e. all current_bets = 0
		current_player.stack_size = current_player.stack_size - bet_size 
		current_player_object.stack_size = current_player_object.stack_size - bet_size

		#Update the total and current bets of the player who bet
		current_player_object.total_bet = current_player_object.total_bet + bet_size
		current_player_object.current_bet = current_player_object.current_bet  + bet_size

		#Do not need to check if action has closed, because a bet can never close action
		#So just move the player_to_act to next live player
		old_actor = current_game_state.player_to_act ## this should also be current_player_object. front end should
														## only trigger this route from player whose action it is 										
		next_actor = current_game_state.get_live_player_to_left(old_actor)
		current_game_state.player_to_act = next_actor
		
		current_hand.game_state = deepcopy(current_game_state)
	
		db.session.commit()

	return 'Success.'


# @app.route('/<current_session_id>/<player_id>/fold/', methods=['POST'])
def fold(current_session_id, player_id):
	player_id = int(player_id)

	#get session, gamestate, player trying to bet, and street
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_player = Player.query.filter_by(id = player_id, poker_session_id = current_session_id).first()
	seat_num = current_player.seat_num
	current_game_state = current_hand.game_state
	current_player_object = current_game_state.get_player_at_seat(seat_num)


	if current_player_object == current_game_state.player_to_act:
		#Player is folding, so set is_folded to True in gamestate
		current_player_object.is_folded = True


		#Check to see if the bet loop is completed, action may not be over if invalid raise happened
		if current_game_state.street != 0 \
			and current_game_state.get_unfolded_player_to_left(current_player_object) == current_game_state.last_valid_raiser :
				current_game_state.is_raising_allowed = False 

		#if the street is pre-flop, must check to see if button has option. If the option is over (last_valid_raiser is no longer None), then proceed as normal
		if current_game_state.street == 0 and current_game_state.last_valid_raiser :
			if current_game_state.get_unfolded_player_to_left(current_player_object) == current_game_state.last_valid_raiser :
				current_game_state.is_raising_allowed = False 
		

	clean_up(current_session_id, seat_num, current_game_state, current_session)


	return 'Success.'


# @app.route('/<current_session_id>/<player_id>/call/', methods=['POST'])
def call(current_session_id, player_id):
	player_id = int(player_id) 

	#get session, gamestate, player trying to bet, and street
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_player = Player.query.filter_by(id = player_id, poker_session_id = current_session_id).first()
	seat_num = current_player.seat_num
	current_game_state = current_hand.game_state
	current_player_object = current_game_state.get_player_at_seat(seat_num)

	#get the maximum current bet for this street
	max_current_bet = max([x.current_bet for x in current_game_state.player_list])

	if current_player_object.stack_size > max_current_bet:
		if current_player_object == current_game_state.player_to_act:

			##See if the bet loop is being completed. The action may not be over yet, however, if there
			##has been at least one invalid raise above the current valid raise
			if current_game_state.street != 0 \
			and current_game_state.get_unfolded_player_to_left(current_player_object) == current_game_state.last_valid_raiser :
				current_game_state.is_raising_allowed = False 

			#if the street is pre-flop, must check to see if button has option. If the option is over (last_valid_raiser is no longer None), then proceed as normal
			if current_game_state.street == 0 and current_game_state.last_valid_raiser :
				if current_game_state.get_unfolded_player_to_left(current_player_object) == current_game_state.last_valid_raiser :
					current_game_state.is_raising_allowed = False 

			#update player stack -- since player is calling, make his total bet equal to the max total bet
			#reduce stack_size by how much more money needed to call (max bet - current bet)
			current_player.stack_size = current_player.stack_size - (max_current_bet - current_player_object.current_bet)
			current_player_object.stack_size = current_player_object.stack_size - (max_current_bet - current_player_object.current_bet)

			#update the player_objects current and total bet for this hand/street
			current_player_object.total_bet = current_player_object.total_bet + (max_current_bet - current_player_object.current_bet)
			current_player_object.current_bet = max_current_bet

			clean_up(current_session_id, seat_num, current_game_state, current_session)


	return 'Success.'


# @app.route('/<current_session_id>/<player_id>/<raise_size>/raise/', methods=['POST'])
def player_raise(current_session_id, player_id, raise_size):
	player_id = int(player_id)
	raise_size = float(raise_size)

	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_player = Player.query.filter_by(id = player_id, poker_session_id = current_session_id).first()
	seat_num = current_player.seat_num
	current_game_state = current_hand.game_state
	current_player_object = current_game_state.get_player_at_seat(seat_num)

	if current_player_object == current_game_state.player_to_act:
		if current_game_state.raising_allowed == True:
			if current_player_object == current_game_state.player_to_act:

				#This player is making a valid raise so set as the last_valid_raiser
				current_game_state.last_valid_raiser = current_player_object

				#update player total and current bet to include raise
				#reduce stack_size by the raise amount
				current_player.stack_size = current_player.stack_size - (raise_size - current_player_object.current_bet)
				current_player_object.stack_size = current_player_object.stack_size - (raise_size - current_player_object.current_bet)

				#update the player_objects current and total bet for this hand/street
				current_player_object.total_bet = current_player_object.total_bet + (raise_size - current_player_object.current_bet)
				current_player_object.current_bet = raise_size

				clean_up(current_session_id, seat_num, current_game_state, current_session)


	return 'Success.'


# @app.route('/<current_session_id>/<player_id>/check/', methods=['POST'])
def check(current_session_id, player_id):
	player_id = int(player_id)
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_player = Player.query.filter_by(id = player_id, poker_session_id = current_session_id).first()
	seat_num = current_player.seat_num
	current_game_state = current_hand.game_state
	current_player_object = current_game_state.get_player_at_seat(seat_num)


	if current_player_object == current_game_state.player_to_act:
		clean_up(current_session_id, seat_num, current_game_state, current_session)

	return 'Success.'


# @app.route('/<current_session_id>/<player_id>/all-in/', methods=['POST'])
def all_in(current_session_id, player_id):

	player_id = int(player_id)
	#get session, gamestate, player trying to bet, and street
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_player = Player.query.filter_by(id = player_id, poker_session_id = current_session_id).first()
	seat_num = current_player.seat_num
	current_game_state = current_hand.game_state
	current_player_object = current_game_state.get_player_at_seat(seat_num)

	if current_player_object == current_game_state.player_to_act:

		#if no one has raised yet, make this player the last valid raiser
		if current_game_state.can_raise(current_player_object) == True:
			current_game_state.last_valid_raiser = current_player_object
		elif current_game_state.get_unfolded_player_to_left(current_player_object) == current_game_state.last_valid_raiser:
			current_game_state.raising_allowed = False

		##See if the bet loop is being completed. The action may not be over yet, however, if there
		##has been at least one invalid raise above the current valid raise
		if current_game_state.get_unfolded_player_to_left(current_player_object) == current_game_state.last_valid_raiser and \
			current_game_state.can_raise(current_player_object) == False:
			current_game_state.raising_allowed = False

		current_player_object.current_bet = current_player_object.current_bet + current_player_object.stack_size
		current_player_object.total_bet = current_player_object.total_bet + current_player_object.stack_size 
		current_player_object.stack_size = 0
		current_player.stack_size = 0
		current_player_object.is_all_in = True

		clean_up(current_session_id, seat_num, current_game_state, current_session)

	return 'Success.'



def make_new_hand(current_session_id, player_id):
	 #move button and start new hand

	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_game_state = current_hand.game_state

	button_player = current_game_state.get_player_at_seat(current_game_state.button_position)
	next_button_seat = current_game_state.get_player_to_left(button_player).seat_num

	new_game_state = make_new_game_state(current_session_id, next_button_seat, current_session.small_blind)
	new_hand = PokerHand(new_game_state)

	current_session.poker_hand = new_hand
	new_hand.poker_session = current_session

	db.session.add(new_hand)
	db.session.commit()

	return 'Success.'


# @app.route('/<current_session_id>/<seat_num>/continue-playing/')
def continue_playing(current_session_id, seat_num):
	 #move button and start new hand

	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_game_state = current_hand.game_state

	current_game_state.pause_for_street_end = False

	current_session.poker_hand.game_state = deepcopy(current_game_state)

	return 'Success.'


@app.route('/<current_session_id>/<seat_num>/show-cards')
def show_cards(current_session_id, seat_num):

	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_game_state = current_hand.game_state
	current_player_object = current_game_state.get_player_at_seat(seat_num)

	if current_player_object == current_game_state.player_to_act:
		current_player_object.is_showing = True
		current_game_state.set_showing_players()
		current_session.poker_hand.game_state = deepcopy(current_game_state)


	return 'Success.'


###################################################
#												  #
#                 Socket Routes                   #
#												  #
###################################################

class GamestateBackend():
	"""Interface for registering and updating WebSocket clients."""

	def __init__(self):
		self.clients = list()
		self.pubsub = redis.pubsub()
		self.pubsub.subscribe(REDIS_CHAN)


	def __iter_data(self):
		for message in self.pubsub.listen():
			data = message.get('data')
			if message['type'] == 'message':
				app.logger.info(u'Sending message: {}'.format(data))
				yield data


	def register(self, client):
		"""Register a WebSocket connection for Redis updates."""
		self.clients.append(client)


	def send(self, client, data):
		"""Send given data to the registered client.
		Automatically discards invalid connections."""
		try:
			client.send(data)
		except Exception:
			self.clients.remove(client)


	def run(self):
		"""Listens for new messages in Redis, and sends them to clients."""
		for data in self.__iter_data():
			for client in self.clients:
				gevent.spawn(self.send, client, data)


	def start(self):
		"""Maintains Redis subscription in the background."""
		gevent.spawn(self.run)

gamestate = GamestateBackend()
gamestate.start()


@sockets.route('/submit')
def inbox(ws):
	"""Receives incoming chat messages, inserts them into Redis."""
	while not ws.closed:
		# Sleep to prevent *contstant* context-switches.
		gevent.sleep(0.1)
		message = ws.receive()
		app.logger.info(u'Received message: {}'.format(message))
		message = json.loads(message)
		app.logger.info(u'Inserting message: {}'.format(message))
		if message['func'] == 'add-player':
			add_player(message['session_id'], message['user_id'], 
				message['email'], message['seat_num'])
			gs = retrieve_gamestate(message['session_id'], message['user_id'])
			app.logger.info(u'Gamestate: {}'.format(gs))
		elif message['func'] == 'deal-hand':
			deal_hand(message['session_id'])
			gs = retrieve_gamestate(message['session_id'], message['user_id'])
			app.logger.info(u'Gamestate: {}'.format(gs))
		elif message['func'] == 'check':
			check(message['session_id'], message['user_id'])
			gs = retrieve_gamestate(message['session_id'], message['user_id'])
			app.logger.info(u'Gamestate: {}'.format(gs))
		elif message['func'] == 'call':
			call(message['session_id'], message['user_id'])
			gs = retrieve_gamestate(message['session_id'], message['user_id'])
			app.logger.info(u'Gamestate: {}'.format(gs))
		elif message['func'] == 'bet':
			bet(message['session_id'], message['user_id'],
				message['bet_amount'])
			gs = retrieve_gamestate(message['session_id'], message['user_id'])
			app.logger.info(u'Gamestate: {}'.format(gs))
		elif message['func'] == 'raise':
			player_raise(message['session_id'], message['user_id'],
				message['raise_amount'])
			gs = retrieve_gamestate(message['session_id'], message['user_id'])
			app.logger.info(u'Gamestate: {}'.format(gs))
		elif message['func'] == 'all-in':
			all_in(message['session_id'], message['user_id'])
			gs = retrieve_gamestate(message['session_id'], message['user_id'])
			app.logger.info(u'Gamestate: {}'.format(gs))
		elif message['func'] == 'fold':
			fold(message['session_id'], message['user_id'])
			gs = retrieve_gamestate(message['session_id'], message['user_id'])
			app.logger.info(u'Gamestate: {}'.format(gs))
		elif message['func'] == 'make-new-hand':
			make_new_hand(message['session_id'], message['user_id'])
			gs = retrieve_gamestate(message['session_id'], message['user_id'])
			app.logger.info(u'Gamestate: {}'.format(gs))

		
		if gs:
			app.logger.info(u'Inserting message: {}'.format(message))
			redis.publish(REDIS_CHAN, gs)








@sockets.route('/receive')
def outbox(ws):
    """Sends outgoing chat messages, via `ChatBackend`."""
    gamestate.register(ws)

    while not ws.closed:
        # Context switch while `ChatBackend.start` is running in the background.
        gevent.sleep(0.1)


###################################################
#												  #
#                 Helper Functions                #
#												  #
###################################################

def bet(current_session_id, player_id, bet_size):


	player_id = int(player_id)
	bet_size = float(bet_size)

	#get session, gamestate, player trying to bet, and street
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_player = Player.query.filter_by(id = player_id, poker_session_id = current_session_id,).first()
	seat_num = current_player.seat_num
	current_game_state = current_hand.game_state
	current_player_object = current_game_state.get_player_at_seat(seat_num)
	current_street = current_game_state.street

	if current_player_object == current_game_state.player_to_act:

		#If the player is able to bet, it means no one has entered the pot and thus
		#the player must be the last_valid_raiser
		current_game_state.last_valid_raiser = current_player_object

		#Update player stack and add bet to the bet list
		#Can remove betsize from stack directly, because player cannot bet
		# unless no other player has bet yet (i.e. all current_bets = 0
		current_player.stack_size = current_player.stack_size - bet_size 
		current_player_object.stack_size = current_player_object.stack_size - bet_size

		#Update the total and current bets of the player who bet
		current_player_object.total_bet = current_player_object.total_bet + bet_size
		current_player_object.current_bet = current_player_object.current_bet  + bet_size

		#Do not need to check if action has closed, because a bet can never close action
		#So just move the player_to_act to next live player
		old_actor = current_game_state.player_to_act ## this should also be current_player_object. front end should
														## only trigger this route from player whose action it is 										
		next_actor = current_game_state.get_live_player_to_left(old_actor)
		current_game_state.player_to_act = next_actor
		
		current_hand.game_state = deepcopy(current_game_state)
	
		db.session.commit()

	return 'Success.'

def game_and_session_info(current_session):
	if current_session.poker_hand:
		game_state = current_session.poker_hand.game_state
		results = get_game_state_dict(current_session.id)
		if game_state.street != 0:
			results['board'] = [card.get_string_tuple() for card in game_state.board][:(2+game_state.street)]
		else:
			results['board'] = []
		results['currently_playing_seats'] = {i : False for i in range(1,11)}
		for player in current_session.players:
			results['currently_playing_seats'][player.seat_num] = \
			player.seat_num in [x.seat_num for x in game_state.player_list]
			
	else:
		results = {'board': []}
		results['currently_playing_seats'] = {i : False for i in range(1,11)}

	results['filled_seats'] = {i : False for i in range(1,11)}
	
	results['usernames'] = {}
	results['stacks'] = {}
	for player in current_session.players:
		results['filled_seats'][player.seat_num] = True
		results['usernames'][player.seat_num] = player.username
		results['stacks'][player.seat_num] = player.stack_size

	return results


def make_new_game_state(current_session_id, new_button_position, small_blind):

	#retrieve current session and number of players
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	num_players = len(current_session.players)

	#deal hole cards and board
	deck = Deck()
	current_hole_cards = []
	for i in range(0, num_players):
		current_hole_cards.append([deck.drawCard(),deck.drawCard()])
	current_board = [deck.drawCard(),deck.drawCard(),deck.drawCard(),deck.drawCard(),deck.drawCard()]

	#Find stack_size/seat number from db for each player, then add a corresponding player object to player list
	#
	players_in_hand = []
	for i in range(0,num_players):
		players_in_hand.append(PlayerObject(current_session.players[i].seat_num, current_session.players[i].stack_size, hole_cards = current_hole_cards[i]))

	#Instantiate new game_state with all players in hand and button moved
	new_game_state = GameState(player_list = players_in_hand, board = current_board, button_position = new_button_position, small_blind = small_blind)

	##post blinds in game_state, also sets player_to_act and last_valid_raiser variables in game_state
	new_game_state.post_blinds()

	##remove blinds from player stacks in db
	for player_object in new_game_state.player_list:
		if player_object.current_bet > 0:
			player = Player.query.filter_by(poker_session_id = current_session_id, seat_num = player_object.seat_num).first()
			player.stack_size = player.stack_size - player_object.current_bet

	# # set player to act as UTG
	# new_game_state.player_to_act = new_game_state.get_live_players()[3 % len(new_game_state.get_live_players())]

	db.session.commit()

	return new_game_state


def get_game_state_dict(current_session_id):

	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	if current_session.poker_hand:
		current_hand = current_session.poker_hand
		current_game_state = current_hand.game_state
	admin_seat = Player.query.filter_by(poker_session_id = current_session_id, is_admin = True).first().seat_num
	
	player_names = {}
	can_bet = {}
	can_raise = {}
	can_call = {}
	current_bets = {}
	stack_sizes = {}
	folded_players = {}
	min_raises = {}
	showing_cards = {}


	for player in current_game_state.player_list:

		can_bet[player.seat_num] = current_game_state.can_bet(player)
		can_raise[player.seat_num] = current_game_state.can_raise(player)
		can_call[player.seat_num] = current_game_state.can_call(player)
		current_bets[player.seat_num] = player.current_bet
		stack_sizes[player.seat_num] = player.stack_size
		folded_players[player.seat_num] = player.is_folded
		min_raises[player.seat_num] = current_game_state.get_min_raise(player)

		if player.is_showing:
			showing_cards[player.seat_num] = [card.get_string_tuple() for card in player.hole_cards]
		else:
			showing_cards[player.seat_num] = []


	results = {}

	#these keys correspond to single objects not other dictionaries
	results['admin_seat'] = admin_seat
	results['seat_to_act'] = current_game_state.player_to_act.seat_num
	results['is_raising_allowed'] = current_game_state.raising_allowed
	results['button_seat'] = current_game_state.button_position
	results['total_pot'] = current_game_state.get_total_pot()
	results['pause_for_street_end'] = current_game_state.pause_for_street_end
	results['pause_for_hand_end'] = current_game_state.pause_for_hand_end


	#these keys correspond to other dictionaries that are indexed
	#by player seat
	results['can_bet']= can_bet
	results['can_raise'] = can_raise
	results['can_call'] = can_call
	results['current_bets'] = current_bets
	results['stack_sizes'] = stack_sizes
	results['folded_players'] = folded_players
	results['min_raises'] = min_raises
	results['showing_cards'] = showing_cards

	return results


def clean_up(current_session_id, seat_num, current_game_state, current_session):
	#Check to see if action is closed or not given the input gamestate/session. Adjust gamestate accordingly.


	#check if hand is over:
	if current_game_state.is_action_closed() and current_game_state.street == 3:

		pot_list = current_game_state.get_all_winnings()
		print(pot_list)

		current_game_state.set_showing_players()

		for player in current_session.players: 
			for pot in pot_list:
				if pot[0].seat_num == player.seat_num:
					player.stack_size = player.stack_size + pot[1]

		for player_object in current_game_state.player_list: 

			for pot in pot_list:
				if pot[0].seat_num == player_object.seat_num:
					player_object.stack_size = player_object.stack_size + pot[1]

		current_game_state.pause_for_hand_end = True
		current_session.poker_hand.game_state = deepcopy(current_game_state)

		db.session.commit()

	#check if action is over but it is not on the river
	elif current_game_state.is_action_closed() and current_game_state.street < 3:

		##check to see if hand is over due to all players all-in
		if len(current_game_state.get_live_players()) < 2 and len(current_game_state.get_unfolded_players()) > 1:

			print('test')

			current_game_state.street = current_game_state.street + 1
			current_session.poker_hand.game_state = deepcopy(current_game_state)

			db.session.commit()

			clean_up(current_session_id, seat_num, current_session.poker_hand.game_state, current_session)

		##check to see if hand is over due to all but one player folding
		elif len(current_game_state.get_unfolded_players()) < 2:

			current_game_state.set_showing_players()

			current_player_object = current_game_state.get_unfolded_players()[0]
			current_player = Player.query.filter_by(poker_session_id = current_session_id, seat_num = current_player_object.seat_num).first()

			total_pot = current_game_state.get_total_pot()
			current_player_object.stack_size = current_player_object.stack_size + total_pot
			current_player.stack_size = current_player.stack_size + total_pot

			current_game_state.pause_for_hand_end = True
			current_session.poker_hand.game_state = deepcopy(current_game_state)

			db.session.commit()

		## check to see if action for street has closed, but the hand is not over
		else:

			current_game_state.street += 1

			#find which player is first to act on the new street
			#live_players is sorted according to distance from button, so check if first element is button
			#otherwise the first to act will be the first element of live_players
			live_players = current_game_state.get_live_players()
			if live_players[0].seat_num == current_game_state.button_position:
				current_game_state.player_to_act = live_players[1]
			else:
				current_game_state.player_to_act = live_players[0]

			#set all current bets to zero for new street
			for player_object in current_game_state.player_list:
				player_object.current_bet = 0

			#reset the last_valid_raiser and pause for animation
			current_game_state.last_valid_raiser = None
			current_game_state.pause_for_street_end = True
			current_game_state.is_raising_allowed = True

			current_session.poker_hand.game_state = deepcopy(current_game_state)
			db.session.commit()

	##if action is not closed, move the player to act
	else:
		#if the street is not over, move gamestates's player_to_act to the next person
		# who is still able to act
		old_actor = current_game_state.player_to_act ## this should also be current_player_object. front end should
												## only trigger this route from player whose action it is	
		next_actor = current_game_state.get_live_player_to_left(old_actor)
		current_game_state.player_to_act = next_actor

		current_session.poker_hand.game_state = deepcopy(current_game_state)
		db.session.commit()


if __name__ == '__main__':
	app.run(debug = True)

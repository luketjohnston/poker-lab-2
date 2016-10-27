from flask import Flask, request, redirect, url_for, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
import os
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import *
from hand_evaluator import Card, Deck
from bet_logic import *
from copy import deepcopy


@app.route('/create-session/')
def create_session():
	# db.create_all()

	#create admin player
	new_admin_player = Player(username = 'Aaron', seat_num = 1, has_button = False, stack_size = 20.00, is_admin = True)

	#create new session
	new_session = PokerSession(small_blind = 0.1)
	#add admin to the session
	new_session.players = [new_admin_player]
	new_admin_player.poker_session = new_session


	db.session.add(new_session)
	db.session.add(new_admin_player)
	db.session.commit()

	return str(new_session.id)

@app.route('/<current_session_id>/show-gamestate')
def show_gamestate(current_session_id):
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_game_state = current_hand.game_state
	current_street = current_game_state.street

	return 'Player Info: {0}, Next Seat to act: {1}, Street {2}'.format(str(current_game_state.player_list) , current_game_state.player_to_act.seat_num,
			current_game_state.street) 

@app.route('/<current_session_id>/<player_id>')
def poker_room(current_session_id, player_id):
	pass

	
@app.route('/<current_session_id>/retrieve-gamestate')
def retrieve_gamestate(current_session_id):
	
	results = get_game_state_dict(current_session_id)
	return jsonify(results)

@app.route('/<current_session_id>/add-player/')
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

	
@app.route('/<current_session_id>/deal-hand/')
def start_session(current_session_id):

	#retrieve current session and number of players
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	num_players = len(current_session.players)
	
	#retrieve button position
	button_position = (Player.query.filter_by(poker_session_id = current_session_id, has_button = True).first()).seat_num

	#Make a gamestate for the new hand. Deal cards and post blinds
	new_game_state = make_new_game_state(current_session_id, button_position, current_session.small_blind)

	#add this gamestate to the current hand in the db
	current_hand = PokerHand(game_state = new_game_state)

	#establish connection between hand and session
	current_session.poker_hand = current_hand
	current_hand.poker_session = current_session

	db.session.add(current_hand)
	db.session.commit()


	return 'Board: {2}, Hands: {3}, Player Info:{0}, Player to Act: {1}'.format(       
		str(new_game_state.player_list), str(new_game_state.player_to_act.seat_num), str(new_game_state.board),
		str([x.hole_cards for x in new_game_state.player_list]) ) 

@app.route('/<current_session_id>/<seat_num>/<bet_size>/bet/')
def bet(current_session_id, seat_num, bet_size):

	seat_num = int(seat_num)
	bet_size = float(bet_size)

	#get session, gamestate, player trying to bet, and street
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_player = Player.query.filter_by(poker_session_id = current_session_id, seat_num = seat_num).first()
	current_game_state = current_hand.game_state
	current_player_object = current_game_state.get_player_at_seat(seat_num)
	current_street = current_game_state.street

	if current_player_object == current_game_state.player_to_act:

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
		# print('precopy')
		# print(current_game_state.player_list)
		current_hand.game_state = deepcopy(current_game_state)
		# print('postcopy')
		# print(current_game_state.player_list)
		db.session.commit()

		return 'Player Info: {0}, Next Seat to act: {1}, Street {2}'.format(str(current_game_state.player_list) , next_actor.seat_num,
			current_game_state.street) 

	return 'Not this players turn'

@app.route('/<current_session_id>/<seat_num>/fold/')
def fold(current_session_id, seat_num):
	seat_num = int(seat_num)

	#get session, gamestate, player trying to bet, and street
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_player = Player.query.filter_by(poker_session_id = current_session_id, seat_num = seat_num).first()
	current_game_state = current_hand.game_state
	current_player_object = current_game_state.get_player_at_seat(seat_num)
	current_street = current_game_state.street

	if current_player_object == current_game_state.player_to_act:
		#Player is folding, so set is_folded to True in gamestate
		current_player_object.is_folded = True

		clean_up(current_session_id, seat_num, current_game_state, current_session)

		return 'Player Info: {0}, Next Seat to act: {1}'.format(str(current_game_state.player_list) , str(current_game_state.player_to_act.seat_num))

	return 'Not this players turn'

@app.route('/<current_session_id>/<seat_num>/call/')
def call(current_session_id, seat_num):
	seat_num = int(seat_num) 

	#get session, gamestate, player trying to bet, and street
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_player = Player.query.filter_by(poker_session_id = current_session_id, seat_num = seat_num).first()
	current_game_state = current_hand.game_state
	current_player_object = current_game_state.get_player_at_seat(seat_num)
	current_street = current_game_state.street

	if current_player_object == current_game_state.player_to_act:

		#update player stack -- since player is calling, make his total bet equal to the max total bet
		#reduce stack_size by how much more money needed to call (max bet - current bet)
		max_current_bet = max([x.current_bet for x in current_game_state.player_list])
		current_player.stack_size = current_player.stack_size - (max_current_bet - current_player_object.current_bet)
		current_player_object.stack_size = current_player_object.stack_size - (max_current_bet - current_player_object.current_bet)

		#update the player_objects current and total bet for this hand/street
		current_player_object.total_bet = current_player_object.total_bet + (max_current_bet - current_player_object.current_bet)
		current_player_object.current_bet = max_current_bet

		clean_up(current_session_id, seat_num, current_game_state, current_session)

		return 'Player Info: {0}, Next Seat to act: {1}, Street: {2}'.format(str(current_game_state.player_list) , 
			str(current_game_state.player_to_act.seat_num), current_game_state.street)

	return 'not this players turn'

@app.route('/<current_session_id>/<seat_num>/all-in')
def all_in(current_session_id, seat_num):
	seat_num = int(seat_num)

	#get session, gamestate, player trying to bet, and street
	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_player = Player.query.filter_by(poker_session_id = current_session_id, seat_num = seat_num).first()
	current_game_state = current_hand.game_state
	current_player_object = current_game_state.get_player_at_seat(seat_num)
	current_street = current_game_state.street

	if current_player_object == current_game_state.player_to_act:

		current_player_object.current_bet = current_player_object.current_bet + current_player_object.stack_size
		current_player_object.total_bet = current_player_object.current_bet 
		current_palyer_object.stack_size = 0
		current_player.stack_size = 0
		current_player_object.is_all_in = True

		clean_up(current_session_id, seat_num, current_game_state, current_session)

		return 'Player Info: {0}, Next Seat to act: {1}'.format(str(current_game_state.player_list) , str(current_game_state.player_to_act.seat_num))
		
	return 'not this players turn'

def make_new_game_state(current_session_id, new_button_position, small_blind):

	print('entered make_new_gamestate')
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

def clean_up(current_session_id, seat_num, current_game_state, current_session):
	#Check to see if action is closed or not given the input gamestate/session. Adjust gamestate accordingly.

	#check if hand is over:
	if current_game_state.is_action_closed() and current_game_state.street ==3:
		pot_list = current_game_state.award_all_pots()

		for player in current_session.players: 
			for pot in pot_list:
				if pot[0] == player.seat_num:
					print('stack size increased')
					player.stack_size = player.stack_size + pot[1]

		#move button and start new hand
		button_player = current_game_state.get_player_at_seat(current_game_state.button_position)
		next_button_seat = current_game_state.get_player_to_left(button_player).seat_num

		new_game_state = make_new_game_state(current_session_id, next_button_seat, current_session.small_blind)
		new_hand = PokerHand(new_game_state)

		
		current_session.poker_hand = new_hand
		new_hand.poker_session = current_session

		db.session.add(new_hand)
		db.session.commit()

	#check if action is over on this street, but hand is not over
	elif current_game_state.is_action_closed() and not current_game_state.street == 3:
		print('street over')
		current_game_state.street += 1
		current_game_state.player_to_act = current_game_state.player_list[1]
		for player_object in current_game_state.player_list:
			player_object.current_bet = 0

		current_session.poker_hand.game_state = deepcopy(current_game_state)
		db.session.commit()

	else:
		#if the street is not over, move gamestates's player_to_act to the next person
		# who is still able to act
		old_actor = current_game_state.player_to_act ## this should also be current_player_object. front end should
												## only trigger this route from player whose action it is	
		next_actor = current_game_state.get_live_player_to_left(old_actor)
		current_game_state.player_to_act = next_actor

		current_session.poker_hand.game_state = deepcopy(current_game_state)
		db.session.commit()

def get_game_state_dict(current_session_id):

	current_session = PokerSession.query.filter_by(id = current_session_id).first()
	current_hand = current_session.poker_hand
	current_game_state = current_hand.game_state
	admin_seat = Player.query.filter_by(poker_session_id = current_session_id, is_admin = True).first().seat_num
	
	filled_seats = {}
	for i in range(1,11):
		filled_seats[i] = False
	player_names = {}
	can_bet = {}
	can_raise = {}
	can_call = {}
	current_bets = {}
	stack_sizes = {}
	folded_players = {}
	min_raises = {}


	for player in current_game_state.player_list:

		filled_seats[player.seat_num] = True
		can_bet[player.seat_num] = current_game_state.can_bet(player)
		can_raise[player.seat_num] = current_game_state.can_raise(player)
		can_call[player.seat_num] = current_game_state.can_call(player)
		current_bets[player.seat_num] = player.current_bet
		stack_size[player.seat_num] = player.stack_size
		folded_players[player.seat_num] = player.is_folded
		min_raises[player.seat_num] = current_game_state.get_min_raise(player)

		current_player = Player.query.filter_by(poker_session_id = current_session_id, seat_num = player.seat_num).first()
		player_names[current_player.seat_num] = current_player.username

	results = {}
	results['admin_seat'] = admin_seat
	results['seat_to_act'] = current_game_state.player_to_act.seat_num
	results['is_raising_allowed'] = current_game_state.player_to_act.raising_allowed
	results['button_seat'] = current_game_state.button_position
	results['total_pot'] = current_game_state.get_total_pot()
	results['can_bet']= can_bet
	results['can_raise'] = can_raise
	results['can_call'] = can_call
	results['current_bets'] = current_bets
	results['stack_sizes'] = stack_sizes
	results['folded_players'] = folded_players
	results['filled_seats'] = filled_seats
	results['min_raises'] = min_raises

	return results


if __name__ == '__main__':
	app.run(debug = True)

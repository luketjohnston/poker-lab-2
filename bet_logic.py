from hand_evaluator import *

class BetList:

	def __init__(self, num_players = 0, player_list = [], button_position = 0):
		self.num_players = num_players
		self.player_list = player_list
		self.button_position = button_position
	
	def get_live_players(self):
		#get list of player_objects still in the hand, sorted according to distance from the button
		live_players = []
		for player_object in self.player_list:
			#check to see if player has folded or is all-in, if not, add to list
			if player_object.is_folded == False and player_object.is_all_in == False:
				live_players.append(player_object)
			#sort players according to how far from the button they are, i.e. button -> small blind -> big blind
		live_players = sorted(live_players, key = lambda x: (x.seat_num - self.button_position) % (self.num_players+1))
		return live_players

	def get_folded_players(self):
		#get list of folded player_objects sorted to ascending seat number
		folded_players = []
		for player_object in self.player_list:
			if player_object.is_folded == True:
				folded_players.append(player_object)
		folded_players = sorted(folded_players, key = lambda x: x.seat_num)
		return folded_players

	def get_unfolded_players(self):
		#get list of unfolded player_objects sorted to ascending seat number
		unfolded_players = []
		for player_object in self.player_list:
			if player_object.is_folded == False:
				unfolded_players.append(player_object)
		unfolded_players = sorted(unfolded_players, key = lambda x: x.seat_num)
		return unfolded_players

	def get_player_at_seat(self, seat):
		#get the player_object corresponding to a certain seat number
		for player_object in self.player_list:
			if player_object.seat_num == seat:
				return player_object

	def is_action_closed(self, street):
		#test to see if betting is closed on a certain street
		live_players = self.get_live_players()
		if street == 0:
			#preflop: check if first to act total bet matches last to act total bet 
			if live_players[3 % self.num_players].total_bet == live_players[2 % self.num_players].total_bet:
				return True
			else:
				return False

		if street > 0:
			#if not preflop check to see first to act total bet  matches last to act total bet
			if live_players[ 1 % self.num_players].total_bet == live_players[0 % self.num_players].total_bet:
				return True
			else: 
				return False

	def post_blinds(self, small_blind):
		#update the total_bet of the small/big blind. 
		#use this at start of hand to post blinds
		players = sorted(self.player_list, key = lambda x: (x.seat_num - self.button_position) % (self.num_players+1))
		players[1].total_bet = small_blind
		players[2].total_bet = 2*small_blind

	def get_total_pot(self):
		#sum all the total_bets of each player_object 
		#returns the total pot size
		total_pot = 0
		for player_object in self.player_list:
			total_pot += player_object.total_bet
		return total_pot

	def award_pots(self):
		return


class PlayerObject:

	def __init__(self, seat_num, total_bet = 0, is_folded = False, is_all_in = False, hole_cards = []):
		self.seat_num = seat_num
		self.total_bet = total_bet
		self.is_folded = is_folded
		self.is_all_in = is_all_in
		self.hole_cards = hole_cards

	def __repr__ (self):
		return 'Seat:{0} Totalbet:{1}'.format(self.seat_num, self.total_bet)



# player1 = PlayerObject(0,40)
# player2 = PlayerObject(1,20)
# player3 = PlayerObject(2,40)
# player4 = PlayerObject(3,40)

# bet_list = BetList(4,[player1,player2,player3,player4],0)

# print(bet_list.is_action_closed(1))

# print(bet_list.player_list)




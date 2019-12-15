from hand_evaluator import *
from copy import deepcopy

class GameState:

	def __init__(self, player_list = [], button_position = 1, street =0, board = [], small_blind = 1):

		self.player_list = player_list
		self.button_position = button_position
		self.street = street
		self.board = board
		self.small_blind = small_blind
		self.raising_allowed = True
		self.pause_for_street_end = False
		self.pause_for_hand_end = False
		self.run_board = False
		self.player_to_act = None         # This is set when post_blinds() function is called
		self.last_valid_raiser = None     # also set by post_blinds()
		self.last_raise = None            # also set by post_blinds()
		
		# Sort self.player_list according to distance ahead of the button
		button_player = self.get_player_at_seat(button_position)
		player_list = sorted(player_list, key = lambda x: x.seat_num)
		player_list = sorted(player_list, key = lambda x: (player_list.index(x)-player_list.index(button_player)) % len(player_list))
		self.player_list = player_list
	
	def get_live_players(self):
		# get list of player_objects still capable of acting, sorted according to distance from the button
		live_players = []
		for player_object in self.player_list:
			# check to see if player has folded or is all-in, if not, add to list
			if player_object.is_folded == False and player_object.is_all_in == False:
				live_players.append(player_object)

		return live_players

	def get_folded_players(self):
		# get list of folded player_objects sorted to ascending seat number
		folded_players = []
		for player_object in self.player_list:
			if player_object.is_folded == True:
				folded_players.append(player_object)
		return folded_players

	def get_unfolded_players(self):
		# get list of unfolded player_objects sorted to ascending seat number
		unfolded_players = []
		for player_object in self.player_list:
			if player_object.is_folded == False:
				unfolded_players.append(player_object)
		return unfolded_players

	def get_player_to_left(self, player):
		# returns player to left of input player
		index = self.player_list.index(player)
		return self.player_list[(index +1) % len(self.player_list)]

	def get_live_player_to_left(self,player):
		# returns next live player to left of input player
		live_players = self.get_live_players()
		button_player = self.get_player_at_seat(self.button_position)
		if player not in live_players:
			live_players.append(player)
			live_players = sorted(live_players, key = lambda x: x.seat_num)
			live_players = sorted(live_players, key = lambda x: (self.player_list.index(x)-self.player_list.index(button_player)) % len(self.player_list))
		index = live_players.index(player)
		player_to_left = live_players[(index + 1) % len(live_players)]

		return player_to_left

	def get_unfolded_player_to_left(self,player):
		# returns next unfolded player to left of input player
		unfolded_players = self.get_unfolded_players()
		button_player = self.get_player_at_seat(self.button_position)
		if player not in unfolded_players:
			unfolded_players.append(player)
			unfolded_players = sorted(unfolded_players, key = lambda x: x.seat_num)
			unfolded_players = sorted(unfolded_players, key = lambda x: (self.player_list.index(x)-self.player_list.index(button_player)) % len(self.player_list))
		index = unfolded_players.index(player)
		player_to_left = unfolded_players[(index + 1) % len(unfolded_players)]

		return player_to_left

	def get_player_to_right(self, player):
		# return player to right of input player
		index = self.player_list.index(player)
		return self.player_list[(index - 1) % len(self.player_list)]

	def get_player_at_seat(self, seat):
		# get the player_object corresponding to a certain seat number
		for player_object in self.player_list:
			if player_object.seat_num == seat:
				return player_object

	def is_action_closed(self):
		# test to see if action is closed
		live_players = self.get_live_players()
		unfolded_players = self.get_unfolded_players()

		if len(unfolded_players) < 2:
			return True

		if len(live_players) == 0:
			return True
		
		## look to see if it has checked around
		if len([x for x in live_players if x.current_bet == 0]) == len(live_players):
			if live_players[0].seat_num ==  self.button_position and self.player_to_act == live_players[0]:
				return True
			if live_players[0].seat_num ==  self.button_position and self.player_to_act != live_players[0]:
				return False

			if live_players[0].seat_num != self.button_position and self.player_to_act == live_players[-1]:
				return True
			if live_players[0].seat_num != self.button_position and self.player_to_act != live_players[-1]:
				return False

		## if the bets of live players are not all equal to the max bet, then action is not closed
		for x in live_players:
			if x.current_bet != self.get_max_current_bet():
				return False

		## check to see if action should go to the big blind for his option preflop.
		if self.street == 0 and live_players[0].current_bet < 4*self.small_blind:

			## check if it is not heads up
			if len(self.player_list) >2:

			## Here, player_to_act is the player that fired the route. Must check if that player is the small blind 
			## It is impossible for small blind to close action preflop, so if the player_to_act is the SB, return False
				if self.player_list[0].seat_num == self.button_position and self.player_to_act == self.player_list[1]:
					return False
				if self.player_list[0].seat_num != self.button_position and self.player_to_act == self.player_list[0]:
					return False

			# if it is heads up, then the preflop action is reversed. Must check to see if button has called-- not small blind
			else:
				if self.player_to_act == live_players[0]:
					return False


		return True

	def get_max_current_bet(self):
		#get maximum current bet
		max_current_bet = max([x.current_bet for x in self.player_list])

		return max_current_bet

	def get_min_raise(self, player):
		#Returns the minimum raise amount for player given the current
		#valid raise and current max bet

		if self.last_valid_raiser: # last_valid_raiser is set when someone raises for the first time
			return self.last_valid_raiser.current_bet + self.last_raise
		else:
			return 0

	def get_raise_amount(self, player, bet_size):
		# returns the size of a raise, given the total bet size
		if self.last_valid_raiser:
			return (bet_size - self.last_valid_raiser.current_bet)
		else:
			return bet_size

	def post_blinds(self):
		#update the total_bet of the small/big blind. 
		#use this at start of hand to post blinds

		#These methods do not check to see if the blinds have enough money to post. Thus, the other game logic must 
		#ensure that a player with less money than the big blind is forced to sit out and never added to the gamestate.
		#
		#Otherwise the player stack will become negative

		if len(self.player_list) > 2:

			self.player_list[1].total_bet = self.small_blind
			self.player_list[1].current_bet = self.small_blind
			self.player_list[1].stack_size = self.player_list[1].stack_size - self.small_blind

			self.player_list[2 % len(self.player_list)].total_bet = 2*self.small_blind
			self.player_list[2 % len(self.player_list)].current_bet = 2*self.small_blind
			self.player_list[2 % len(self.player_list)].stack_size = self.player_list[2 % len(self.player_list)].stack_size - 2*self.small_blind

			self.player_to_act = self.player_list[3 % len(self.player_list)]
			self.last_valid_raiser = self.player_list[2]
			self.last_raise = self.small_blind * 2

		## If there are only two players, the preflop betting must be reversed.
		else:
			self.player_list[0].total_bet = self.small_blind
			self.player_list[0].current_bet = self.small_blind
			self.player_list[0].stack_size = self.player_list[0].stack_size - self.small_blind

			self.player_list[1].total_bet = 2*self.small_blind
			self.player_list[1].current_bet = 2*self.small_blind
			self.player_list[1].stack_size = self.player_list[1].stack_size - 2*self.small_blind

			self.player_to_act = self.player_list[0]
			self.last_valid_raiser = self.player_list[1]
			self.last_raise = small_blind * 2

	def can_bet(self, player):

		#checks to see if player can open the action, i.e. no previous bets
		for player in self.player_list:
			if player.current_bet != 0:
				return False

		return True

		#nned to set can_bet = True for big blind if everyone completes, then front end can check to see if 
		#anyone can bet and raise, this should only happen to big blind when everyone completes.


	def can_raise(self, player):
		#checks to see if player has enough money to raise, given previous raise
		if player.stack_size + player.current_bet >= self.get_min_raise(player):
			return True

		## need to set can_raise = True for big blind if everyone completes
		
		
	def can_call(self, player):
		#check to see if player has enough money to call the largest bet
		max_current_bet = self.get_max_current_bet()
		if player.stack_size + player.current_bet > max_current_bet:
			return True
		else:
			return False

	def get_next_to_act(self):
		index = self.get_live_players().index(self.player_to_act)
		return self.get_live_players()[(index + 1) % len(self.get_live_players())]

	def get_max_side_pot(self, hero, villians):
		#returns how much of the pot a player is elligible to win
		total_pot = 0
		for player_object in villians:
			if player_object.total_bet <= hero.total_bet:
				total_pot += player_object.total_bet
			else:
				total_pot += hero.total_bet

		return total_pot

	def get_total_pot(self):
		total_pot = 0
		for player in self.player_list:
			total_pot = total_pot + player.total_bet 

		return total_pot

	def get_side_pot_info(self):
		#returns the total side pot along with all players elligible for that pot
		#output is a list of the form [total_side_pot1,[player1,player2,...]], [total_side_pot2, [player..]]


		players_copy = deepcopy(self.player_list)
		unfolded_players_copy = deepcopy(self.get_unfolded_players())
		unfolded_players_copy = sorted(unfolded_players_copy, key= lambda x: x.total_bet)

		#if everyone else folded, give pot to last unfolded player
		if len(self.get_unfolded_players()) == 1:
			return [[self.get_max_side_pot(self.get_unfolded_players()[0], self.player_list), [self.get_unfolded_players()[0]]]]
		
		#if the hand made it showdown, divide pot into side pots
		side_pot_info_list = []
		while len(unfolded_players_copy) > 0:
			
			## The player objects held in player_copy and winner_copy are not the actual player objects held by the player list 
			## in the game_state object. Thus in order to return the actual player objects so that they can be used 
			#to update the gamestate-- The copy lists are iterated over and the actual player_objects are pulled from the 
			# game_state which correspond to the seat numbers.
			unfolded_players_real = []
			for x in unfolded_players_copy:
				unfolded_players_real.append(self.get_player_at_seat(x.seat_num))

			## Finally, the total side pot amount and players elligible for the side pot are added to the side_pot_info_list
			side_pot_info_list.append( [self.get_max_side_pot(unfolded_players_copy[0], players_copy), unfolded_players_real] )

		
			#After adding the side pot info of the previous smallest side pot, the total bets of all players_copy are 
			#reduced by the smallest previous bet. Then, any player_copy with a total_bet <= 0 is removed from 
			#unfolded_players_copy/players_copy. Thus, the next smallest total bet is again the first element of 
			#unfolded_players_copy.
			smallest_bet = unfolded_players_copy[0].total_bet
			for i in range(0, len(players_copy)):
				players_copy[i].total_bet -= smallest_bet
			players_copy = [x for x in players_copy if x.total_bet > 0]
			
			
			for i in range(0, len(unfolded_players_copy)):
				unfolded_players_copy[i].total_bet -= smallest_bet
			unfolded_players_copy = [x for x in unfolded_players_copy if x.total_bet > 0]

			#This process is repeated until the length of unfolded_players_copy becomes zero, at this point
			#all side_pots have been awarded

		return side_pot_info_list

	def get_all_winnings(self):
		## returns list of tuples containing a player in the hand and how much money they won from a side pot:
		## [[player1, winnings1, total_side_pot1],[player2, winnings2, total_side_pot2],..], NOTE: A player may appear more than once
		## if they win multiple side pots

		player_winnings =[]
		side_pot_info_list = self.get_side_pot_info()

		for pot_info in side_pot_info_list:
			#find the list of winners for a given side pot in side_pot_info_list
			winners = self.evaluate_hands(pot_info[1])
			for winner in winners:
				#for each winner of the side pot, assign to them the appropriate amount of money
				player_winnings.append([winner, pot_info[0]/len(winners), pot_info[0]])
			
		return player_winnings

	def set_showing_players(self):

		side_pot_info_list = self.get_side_pot_info()
		players_in_pots = [x[1] for x in side_pot_info_list]
		button_player = self.get_player_at_seat(self.button_position)
		left_of_button = self.get_player_to_left(button_player)

		if self.last_valid_raiser and (self.last_valid_raiser in self.get_unfolded_players()):

			for players in players_in_pots:
				players = sorted(players, key = lambda x: (self.player_list.index(x) - self.player_list.index(self.last_valid_raiser)) % len(self.player_list))
				players[0].is_showing = True
				for player1 in players:
					players_to_compare = players[0:players.index(player1)+1]
					for player2 in players:
						if player2.is_showing:
							players_to_compare.append(player2)
					if player1 in self.evaluate_hands(players_to_compare):
						player1.is_showing = True

		else:
			for players in players_in_pots:

				players = sorted(players, key = lambda x: (self.player_list.index(x) - self.player_list.index(left_of_button)) % len(self.player_list))
				players[0].is_showing = True
				for player1 in players:
					players_to_compare = players[0:players.index(player1)+1]
					for player2 in players:
						if player2.is_showing:
							players_to_compare.append(player2)
					if player1 in self.evaluate_hands(players_to_compare):
						player1.is_showing = True




			




	def find_winning_player(self, player1,player2):
	#compares two players' hands and returns the tuple of [winning player_object, winning hole_cards]#
	#see hand_evaluator.py for info on these methods
		bestHandValue1 = max( [findStraightFlush(player1.hole_cards,self.board),findFlush(player1.hole_cards,self.board),findStraight(player1.hole_cards,self.board),findPairs(player1.hole_cards,self.board)], key = lambda x: x[1])
		bestHandValue2 = max( [findStraightFlush(player2.hole_cards,self.board),findFlush(player2.hole_cards,self.board),findStraight(player2.hole_cards,self.board),findPairs(player2.hole_cards,self.board)], key = lambda x: x[1])
		
		if(bestHandValue1[1]>bestHandValue2[1]):
			return player1
		if(bestHandValue2[1]>bestHandValue1[1]):
			return player2

		if(bestHandValue1[1] == bestHandValue2[1]):
			
			if bestHandValue1[0] < bestHandValue2[0]:
				return player2
			if bestHandValue1[0] > bestHandValue2[0]:
				return player1
			if bestHandValue2[0] == bestHandValue1[0]:
				return None

	def evaluate_hands(self, player_list):
	#returns a list of the winning player given an input list of players and board
	#Will return list of length 1 containing winner if no side pots or ties 
	
		#make the first player the temporary winner
		temp_winner = player_list[0]

		#Hand strength obeys transitive property, so just nest find_winning_player calls 
		#on the list to determine the overall winner
		for i in range(0, len(player_list)):
				temp = self.find_winning_player(temp_winner, player_list[i])
				if temp:
					temp_winner = temp

		#Now check for split pots. temp_winner holds a winning player at this point,
		#but there may be others with the same hand strength. Iterate through list and
		#add players who tie with the temp_winner to the winner list
		winner_list = []
		for player in player_list:
			if self.find_winning_player(player, temp_winner) == None:
				winner_list.append(player)


		return winner_list

	def get_best_hand(self, player):
	## returns the best 5 card hand given hole cards and board
		bestHandValue = max( [findStraightFlush(player.hole_cards,self.board),findFlush(player.hole_cards,self.board),findStraight(player.hole_cards,self.board),findPairs(player.hole_cards,self.board)], key = lambda x: x[1])
		return bestHandValue[0]

	# def check_showing_players(self):


	# 	#get first player to show
	# 	live_players = self.get_live_players()

	# 	#check to see if the first player is the button
	# 	if live_players[0] == self.get_player_at_seat(button_position):
	# 		first_player = live_players[1]
	# 		first_player.is_showing = True

	# 		#need to loop over every player and compare hand with all the players who act before 
	# 		for index1 in range(2,len(live_players)):
	# 			hands_to_compare = live_players[1:index % len(live_players)]
	# 			#also need to compare with players who have opted to show early
	# 			for player in live_players:
	# 				if player.is_showing == True:
	# 					hands_to_compare.append(player)
	# 			#if the current player's hand is better than or equal to the best currently shown hand then they need to show
	# 			if live_players[index] in evaluate_hands(hand_to_compare):
	# 				live_players[index].is_showing = True

	# 	#Do the same as before if the first player isn't the button
	# 	else:
	# 		first_player = live_players[0]
	# 		first_player.is_showing = True
	# 		for index1 in range(1,len(live_players)):
	# 			hands_to_compare = live_players[1:index]
	# 			for player in live_players:
	# 				if player.is_showing == True:
	# 					hands_to_compare.append(player)
	# 			if live_players[index] in evaluate_hands(hand_to_compare):
	# 				live_players[index].is_showing = True
		

class PlayerObject:

	def __init__(self, seat_num, stack_size, total_bet = 0, current_bet = 0, 
					is_folded = False, is_all_in = False, hole_cards = [], 
					is_showing=False):
		#initalize a PlayerObject. Note: hole_cards must a be a 2 element list of Card objects
		self.seat_num = seat_num
		self.current_bet = current_bet
		self.total_bet = total_bet
		self.is_folded = is_folded
		self.is_all_in = is_all_in
		self.hole_cards = hole_cards
		self.stack_size = stack_size
		self.is_showing = is_showing

	def __repr__ (self):
		return '(Seat: {0}, Stack: {1}, TotalBet: {2}, CurrentBet: {3})'.format(self.seat_num,self.stack_size, self.total_bet, self.current_bet)



# deck = Deck()
# board = [Card(2,1),Card(4,1),Card(5,1),Card(14,2),Card(13,2)]
# player1 = PlayerObject(1,17, current_bet = 0, hole_cards = [Card(10,1),Card(11,1)])
# player2 = PlayerObject(2,30, current_bet = 0, hole_cards = [Card(3,3),Card(6,1)])
# player3 = PlayerObject(3,100, current_bet = 0, hole_cards = [Card(3,4),Card(6,4)])
# player4 = PlayerObject(4,100, current_bet = 3, hole_cards = [Card(14,1),Card(7,3)])
# player5 = PlayerObject(5,4, current_bet  = 0, hole_cards = [Card(8,1),Card(9,2)])
# player6 = PlayerObject(6,6, current_bet = 0, hole_cards = [Card(3,4),Card(7,1)])

# game_state = GameState(player_list =[player1,player2,player3,player4,player5,player6], button_position =1, board = board)



# for player in game_state.player_list:
# 	print('{}-- Can Raise: {} Can Bet: {} Can Call: {}'.format(player, game_state.can_raise(player), game_state.can_bet(player), game_state.can_call(player)))

# print ('Hand1: ' + str(player1.hole_cards))
# print ('Hand2: ' + str(player2.hole_cards))
# print ('Hand3: ' + str(player3.hole_cards))
# print ('Hand4: ' + str(player4.hole_cards))
# print ('Hand5: ' + str(player5.hole_cards))
# print ('Hand6: ' + str(player6.hole_cards))
# print ('Board: ' + str(board))

# #print('Winning Hand: ' + str(evaluate_hands([player1,player2,player3,player4,player5,player6],board).hole_cards))
# print('Side Pots' + str(game_state.award_all_pots()))




# print(game_state.is_action_closed(1))

# print(game_state.player_list)




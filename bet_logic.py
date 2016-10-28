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
		self.player_to_act = None #This is set when post_blinds() function is called
		self.last_valid_raiser = None #also set by post_blinds()
		
		#Sort self.player_list according to distance ahead of the button
		button_player = self.get_player_at_seat(button_position)
		player_list = sorted(player_list, key = lambda x: x.seat_num)
		player_list = sorted(player_list, key = lambda x: (player_list.index(x)-player_list.index(button_player)) % len(player_list))
		self.player_list = player_list
	
	def get_live_players(self):
		#get list of player_objects still capable of acting, sorted according to distance from the button
		live_players = []
		for player_object in self.player_list:
			#check to see if player has folded or is all-in, if not, add to list
			if player_object.is_folded == False and player_object.is_all_in == False:
				live_players.append(player_object)

		return live_players

	def get_folded_players(self):
		#get list of folded player_objects sorted to ascending seat number
		folded_players = []
		for player_object in self.player_list:
			if player_object.is_folded == True:
				folded_players.append(player_object)
		return folded_players

	def get_unfolded_players(self):
		#get list of unfolded player_objects sorted to ascending seat number
		unfolded_players = []
		for player_object in self.player_list:
			if player_object.is_folded == False:
				unfolded_players.append(player_object)
		return unfolded_players

	def get_player_to_left(self, player):
		#returns player to left of input player
		index = self.player_list.index(player)
		return self.player_list[(index +1) % len(self.player_list)]

	def get_live_player_to_left(self,player):
		#returns next live player to left of input player
		live_players = self.get_live_players()
		index = live_players.index(player)
		return live_players[(index +1) % len(live_players)]

	def get_player_to_right(self, player):
		#return player to right of input player
		index = self.player_list.index(player)
		return self.player_list[(index - 1) % len(self.player_list)]

	def get_player_at_seat(self, seat):
		#get the player_object corresponding to a certain seat number
		for player_object in self.player_list:
			if player_object.seat_num == seat:
				return player_object

	def is_action_closed(self):
		#test to see if action is closed
		live_players = self.get_live_players()
		if len(live_players) < 2:
			return True
		for x in live_players:
			if x.current_bet != live_players[0].current_bet:
				return False

		return True

	def get_min_raise(self, player):
		#Returns the minimum raise amount for player given the current
		#valid raise and current max bet
		largest_current_bet = max([x.current_bet for x in self.player_list])
		return (self.last_valid_raiser.current_bet)*2 - player.current_bet + (largest_current_bet - self.last_valid_raiser.current_bet)

	def post_blinds(self):
		#update the total_bet of the small/big blind. 
		#use this at start of hand to post blinds

		self.player_list[1].total_bet = self.small_blind
		self.player_list[1].current_bet = self.small_blind
		self.player_list[1].stack_size = self.player_list[1].stack_size - self.small_blind

		self.player_list[2 % len(self.player_list)].total_bet = 2*self.small_blind
		self.player_list[2 % len(self.player_list)].current_bet = 2*self.small_blind
		self.player_list[2 % len(self.player_list)].stack_size = self.player_list[2 % len(self.player_list)].stack_size - 2*self.small_blind

		self.player_to_act = self.player_list[3 % len(self.player_list)]
		self.last_valid_raiser = self.player_list[2 % len(self.player_list)]

	def can_bet(self, player):
		#checks to see if player can open the action, i.e. all previous players have checked
		for player in self.player_list:
			if player.current_bet != 0:
				return False
		return True


	def can_raise(self, player):
		#checks to see if player has enough money to raise, given previous raise
		if player.stack_size + player.current_bet >= self.get_min_raise(player):
			return True
		else: 
			return False
		

		#check to see if player has enough money to call the largest bet
	def can_call(self, player):
		max_current_bet = max([x.current_bet for x in self.player_list])
		if player.stack_size + player.current_bet > max_current_bet:
			return True
		else:
			return False

	def get_next_to_act(self):
		index = self.get_live_players().index(self.player_to_act)
		return self.get_live_players()[(index + 1) % len(self.get_live_players())]

	def get_side_pot(self, hero, villians):
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

	def award_all_pots(self):
		#returns the winners of all different side pots present in the hand.
		#output is a list of the form [[winner1.seat_num, side_pot_amount1],[winner2.seat_num, side_pot_amount2],...]

		players = deepcopy(self.player_list)
		unfolded_players = deepcopy(self.get_unfolded_players())
		unfolded_players = sorted(unfolded_players, key= lambda x: x.total_bet)

		#if everyone else folded, give pot to last unfolded player
		if len(unfolded_players) == 1:
			return [unfolded_players[1].seat_num, self.get_side_pot(unfolded_players[0], players)]
		
		#if the hand made it showdown, divide pot into side pots
		side_pot_list = []
		while len(unfolded_players) > 0:
			
			#unfolded_players is sorted by total_bet, so calling get_side_pot on the first element
			#returns the smallest side pot amount. The winners of this side pot are determined by evaluate_hands
			#Then, the tuple [winner, side_pot_amount/# of winners] is added to the side_pot_list

			winners = evaluate_hands(unfolded_players, self.board)
			for x in winners:
				side_pot_list.append( [x.seat_num, self.get_side_pot(unfolded_players[0], players)/len(winners) ] )

		
			#After adding the winners of the previous smallest side pot, the total bets of all players are 
			#reduced by the smallest previous bet. Then, any player with a total_bet <= 0 is removed from 
			#unfolded_players/players. Thus, the next smallest total bet is again the first element of 
			#unfolded_players.
			smallest_bet = unfolded_players[0].total_bet
			for i in range(0, len(players)):
				players[i].total_bet -= smallest_bet
			players = [x for x in players if x.total_bet > 0]
			
			
			for i in range(0, len(unfolded_players)):
				unfolded_players[i].total_bet -= smallest_bet
			unfolded_players = [x for x in unfolded_players if x.total_bet > 0]

			#This process is repeated until the length of unfolded_players becomes zero, at this point
			#all side_pots have been awarded

		return side_pot_list


class PlayerObject:

	def __init__(self, seat_num, stack_size, total_bet = 0, current_bet = 0, 
					is_folded = False, is_all_in = False, hole_cards = []):
		#initalize a PlayerObject. Note: hole_cards must a be a 2 element list of Card objects
		self.seat_num = seat_num
		self.current_bet = current_bet
		self.total_bet = total_bet
		self.is_folded = is_folded
		self.is_all_in = is_all_in
		self.hole_cards = hole_cards
		self.stack_size = stack_size

	def __repr__ (self):
		return 'Seat: {0}, Stack: {1}, TotalBet: {2}, CurrentBet: {3}'.format(self.seat_num,self.stack_size, self.total_bet, self.current_bet)



def find_winning_player(player1,player2, board):
	#compares two players' hands and returns the winning player_object#

	#see hand_evaluator.py for info on these methods
	bestHandValue1 = max( [findStraightFlush(player1.hole_cards,board),findFlush(player1.hole_cards,board),findStraight(player1.hole_cards,board),findPairs(player1.hole_cards,board)], key = lambda x: x[1])
	bestHandValue2 = max( [findStraightFlush(player2.hole_cards,board),findFlush(player2.hole_cards,board),findStraight(player2.hole_cards,board),findPairs(player2.hole_cards,board)], key = lambda x: x[1])
	
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

def evaluate_hands(player_list, board):
	#returns a list of player_objects who won the pot. Will return 
	#list of length 1 containing winner if no side pots 
	

	#make the first player the temporary winner
	temp_winner = player_list[0]

	#Hand strength obeys transitive property, so just nest find_winning_player calls 
	#on the list to determine the overall winner
	for i in range(0, len(player_list)):
			temp = find_winning_player(temp_winner, player_list[i], board)
			if temp:
				temp_winner = temp

	#Now check for split pots. temp_winner holds a winning player at this point,
	#but there may be others with the same hand strength. Iterate through list and
	#add players who tie with the temp_winner to the winner list
	winner_list = []
	for player in player_list:
		if find_winning_player(player, temp_winner, board) == None:
			winner_list.append(player)


	return winner_list

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




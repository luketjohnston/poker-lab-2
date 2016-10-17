import random
import math

rankName = [2,3,4,5,6,7,8,9,10,'J','Q','K','A']
suitName = ['c','d','h','s']

class Card:
	def __init__(self,rank, suit):
		self.rank = rank
		self.suit = suit

	def __repr__(self):
		return '{}{}'.format(rankName[self.rank-2], suitName[self.suit-1])

	def __lt__(self,other):
		return self.rank < other.rank

	def __gt__(self,other):
		return self.rank > other.rank

	def __eq__(self, other):
		return self.rank == other.rank 

class Player:
	def __init__(self, stackSize):
		self.hand = [drawCard(),drawCard()]
		self.stackSize = stackSize

class Deck:
	def __init__(self):
		self.cardList = [int(x) for x in range(52)]

	def drawCard(self):
		index = random.randint(0,len(self.cardList)-1)
		cardValue = self.cardList[index]
		del self.cardList[index]
		return Card(cardValue/4+2,(cardValue % 4)+1)

def findPairs(hand,board):

# Returns the best 5 card pair-type hand, hand strength tuple  
# (high card, pair, 2 pair, 3 of a kind, full house, 4 of a kind) 


	pairCountList = []
	bestHand = []
	rankSortedHand = sorted(hand+board, key = lambda x: -x.rank)

	for c1 in hand + board:
		pairCount = 0
		for c2 in hand + board:
			if c1.rank == c2.rank:
				pairCount += 1
		pairCountList.append((c1.rank,pairCount))
	
	pairCountList = sorted(sorted(set(pairCountList), key=lambda x: -x[0]), key=lambda x: -x[1])


	if pairCountList[0][1] == 1:
		bestHand = rankSortedHand[:5]
		return [bestHand,1]

	if pairCountList[0][1] == 2 and pairCountList[1][1] ==1:
		bestHand.append([x for x in rankSortedHand if x.rank == pairCountList[0][0]])
		bestHand.append([[x for x in rankSortedHand if x.rank == pairCountList[1][0]][0]])
		bestHand.append([[x for x in rankSortedHand if x.rank == pairCountList[2][0]][0]])
		bestHand.append([[x for x in rankSortedHand if x.rank == pairCountList[3][0]][0]])
		return [[x for list in bestHand for x in list],2]


	if pairCountList[0][1] == 2 and pairCountList[1][1] == 2:
		bestHand.append([x for x in rankSortedHand if x.rank == pairCountList[0][0]])
		bestHand.append([x for x in rankSortedHand if x.rank == pairCountList[1][0]])
		bestHand.append([[x for x in rankSortedHand if x.rank == pairCountList[2][0]][0]])
		return [[x for list in bestHand for x in list],3]

	if pairCountList[0][1] == 3 and pairCountList[1][1] == 1:
		bestHand.append([x for x in rankSortedHand if x.rank == pairCountList[0][0]])
		bestHand.append([[x for x in rankSortedHand if x.rank == pairCountList[1][0]][0]])
		bestHand.append([[x for x in rankSortedHand if x.rank == pairCountList[2][0]][0]])
		return [[x for list in bestHand for x in list],4]

	if pairCountList[0][1] == 3 and (pairCountList[1][1] == 2 or pairCountList[1][1] == 3):
		bestHand.append([x for x in rankSortedHand if x.rank == pairCountList[0][0]])
		bestHand.append([x for x in rankSortedHand if x.rank == pairCountList[1][0]][:2])
		return [[x for list in bestHand for x in list],7]

	if pairCountList[0][1] == 4:
		bestHand.append([x for x in rankSortedHand if x.rank == pairCountList[0][0]])
		bestHand.append([[x for x in rankSortedHand if x.rank == pairCountList[1][0]][0]])
		return [[x for list in bestHand for x in list],8]

def findFlush(hand, board):

# returns rank sorted list of flushing cards if there are at least 5 of that suit, hand strength tuple
# returns empty list if no flush

	allCards = hand +board
	flushList = [[allCards[0]]]
	
	for i in range(1,len(allCards)):
		s = allCards[i]
		canBuildFlush = False
		for l in flushList:
			if s.suit == l[0].suit:
				l.append(s)
				canBuildFlush = True
		if not canBuildFlush:
			flushList.append([s])
	
	bestFlush = max(flushList, key=len)
	
	if len(bestFlush) > 4:
		bestFlush = sorted(bestFlush, key = lambda x: -x.rank)
		return [bestFlush,6]

	return [[],0]
	
				
def findStraight(hand, board):
	
#returns longest list of consecutively ranked cards if it is at least length 5, hand strength tuple
# if multiple of the same rank card, the list includes all of them.
#returns empty list of no straight

# NOTE: in the function, the "val" of a card is its rank - 1 mod 13. 

	allCards = hand + board

	allCards = sorted(allCards, key = lambda x: -x.rank)
	# do compute straights, aces can be small and large. So go through 
	# all the cards and add each ace to the beginning of the list. Since there can 
	# only be 4 aces and there are 7 cards this will work fine
	for i in range(len(allCards)):
		if allCards[i].rank == 14:
			allCards = allCards + [allCards[i]] # add ace to lower end


	# list of all cards making up straight
	straightList = [allCards[0]]
	straightLen = 1 # length of straight

        # start on second card
	for card in allCards[1:]:
		# get the val of the previous card. 
		last_val = ((straightList[-1].rank - 1) % 13)
		cur_val = (card.rank - 1) % 13
		# test if this is the next card in the straight
		if ((cur_val+1) % 13) == (last_val % 13):
			straightLen += 1
		# test if this is the same as the last card in the straight
		elif (cur_val % 13) == (last_val % 13):
			continue # ignore duplicates
		else: 
			if straightLen >= 5:
				return [straightList,5]
			# straight ends
			straightLen = 1
			straightList = []
		straightList.append(card)

        if straightLen >= 5:
		return [straightList,5]
	return [[],0]

def findStraightFlush(hand,board):

#returns longest straight flush card list, hand strength tuple
#returns empty list if no straight flush

	bestStraightFlush=[]
	tempFlush = findFlush(hand, board)[0]
	if len(tempFlush) > 0:
		bestStraightFlush = findStraight( tempFlush, [])[0]
	if len(bestStraightFlush) >4:
		return [bestStraightFlush,9]

	return [[],0]
	
def winningHand(hand1,hand2,board):	

#compares two hands and returns the winning hand card list#

	bestHandValue1 = max( [findStraightFlush(hand1,board),findFlush(hand1,board),findStraight(hand1,board),findPairs(hand1,board)], key = lambda x: x[1])
	bestHandValue2 = max( [findStraightFlush(hand2,board),findFlush(hand2,board),findStraight(hand2,board),findPairs(hand2,board)], key = lambda x: x[1])
	
	

	if(bestHandValue1[1]>bestHandValue2[1]):
		return bestHandValue1[0][:5]
	if(bestHandValue2[1]>bestHandValue1[1]):
		return bestHandValue2[0][:5]

	if(bestHandValue1[1] == bestHandValue2[1]):
		
		if bestHandValue1[0] < bestHandValue2[0]:
			return bestHandValue2[0][:5]
		if bestHandValue1[0] > bestHandValue2[0]:
			return bestHandValue1[0][:5]
	
				
# Test #

deck = Deck()	

hand1= [deck.drawCard(),deck.drawCard()]
hand2 = [deck.drawCard(),deck.drawCard()]
board = [deck.drawCard(),deck.drawCard(),deck.drawCard(),deck.drawCard(),deck.drawCard()]

print ('Hand1: ' + str(hand1))
print ('Hand2: ' + str(hand2))
print ('Board: ' + str(board))
print ('Winning Hand: ' + str(winningHand(hand1,hand2,board)))


	
#handDist = [0]*9
#for i in range(0,1000000):
#	deck = Deck()
#	hand = [deck.drawCard(),deck.drawCard()]
#	board =[deck.drawCard(),deck.drawCard(),deck.drawCard(),deck.drawCard(),deck.drawCard()]
#	j = max( [findStraightFlush(hand,board),findFlush(hand,board),findStraight(hand,board),findPairs(hand,board)], key = lambda x: x[1])[1]
#	handDist[j-1] = handDist[j-1]+1
#print[handDist]




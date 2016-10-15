from random import randint

class Player:
	def __init__(self, buyIn):
		self.hand = [drawCard(),drawCard()]
		self.stackSize = buyIn

def drawCard():
	while 1:
		index = randint(0,51)
		if deck[index] == True:
			deck[index] = False
			return index
	
deck=[True]
for i in range(1,52):
	deck.append(True)

player1 = Player(2000);
board = [drawCard(),drawCard(),drawCard(),drawCard(),drawCard()]

print(player1.hand)

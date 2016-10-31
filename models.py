from app import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy_utils import UUIDType
import uuid


class PokerSession(db.Model):
	__tablename__ = 'poker_sessions'

	id = db.Column(UUIDType(binary =False), default = uuid.uuid4(), primary_key=True)
	name = db.Column(db.String(20))
	players = db.relationship('Player', backref='poker_session', \
                                lazy='joined')
	poker_hand = db.relationship('PokerHand', backref='poker_session', \
                                lazy='joined', uselist=False)
	small_blind = db.Column(db.Float)
	big_blind = db.Column(db.Float)
	max_buy_in = db.Column(db.Float)
	hand_in_session = db.Column(db.Boolean)


	def __init__(self, name = '', small_blind = None, players = None, 
		poker_hand = None, big_blind = None, max_buy_in = None):
		self.id = uuid.uuid4()
		self.small_blind = small_blind
		if players:
			self.players = players
		if poker_hand:
			self.poker_hand = poker_hand
		self.hand_in_session = False
		self.big_blind = big_blind
		self.name = name
		self.max_buy_in = max_buy_in


class Player(db.Model):
	__tablename__ = 'players'

	id = db.Column(db.Integer, primary_key=True)
	seat_num = db.Column(db.Integer)
	username = db.Column(db.String(20))
	email = db.Column(db.String(120))
	stack_size = db.Column(db.Float)
	has_button = db.Column(db.Boolean)
	is_admin = db.Column(db.Boolean)
	is_sitting_out = db.Column(db.Boolean)
	is_on_standby = db.Column(db.Boolean)
	poker_session_id = db.Column(UUIDType(binary = False), \
		db.ForeignKey('poker_sessions.id'))

	def __init__(self, username = None, email = None, stack_size = None, seat_num = None, \
				has_button = False, is_admin = False, is_sitting_out = False, is_on_standby = False):
		self.username = username
		self.seat_num = seat_num
		self.email = email
		self.stack_size = stack_size
		self.has_button = has_button
		self.is_admin = is_admin
		self.is_sitting_out = is_sitting_out
		self.is_on_standby = is_on_standby


class PokerHand(db.Model):
	__tablename__ = 'poker_hands'

	id = db.Column(db.Integer, primary_key=True)
	game_state = db.Column(db.PickleType)
	poker_session_id = db.Column(UUIDType(binary=False), \
		db.ForeignKey('poker_sessions.id'))

	def __init__(self, game_state = None):
		if game_state:
			self.game_state = game_state


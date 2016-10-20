getfrom app import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy_utils import UUIDType
import uuid


class PokerSession(db.Model):
	__tablename__ = 'poker_sessions'

	id = db.Column(UUIDType(binary =False), default = uuid.uuid4(), primary_key=True)
	players = db.relationship('Player', backref='poker_session', \
                                lazy='joined')
	current_hand = db.relationship('PokerHand', backref='poker_session', \
									lazy='joined', uselist=False)
	small_blind = db.Column(db.Float)

	def __init__(self, small_blind = None, players = None, current_hand = None):
		self.id = uuid.uuid4()
		self.small_blind = small_blind
		if players:
			self.players = players
		if current_hand:
			self.current_hand = current_hand


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
	street = db.Column(db.Integer)
	bet_list_object = db.Column(db.PickleType)
	hole_cards = db.Column(db.PickleType)
	board = db.Column(db.PickleType)
	poker_session_id = db.Column(UUIDType(binary=False), \
		db.ForeignKey('poker_sessions.id'))

	def __init__(self, street = None, bet_list_object = None, hole_cards = [None], board = [None]):
		self.street = street
		if bet_list_object:
			self.bet_list_object = bet_list_object
		self.hole_cards = hole_cards
		self.board = board


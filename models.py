from app import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy_utils import UUIDType
import uuid

class PokerSession(db.Model):
	__tablename__ = 'poker_sessions'

	id = db.Column(UUIDType(binary=False), primary_key=True)
	players = db.relationship('Player', backref='poker_session', \
                                lazy='select')
	current_hand = db.relationship('PokerHand', backref='poker_session', \
									lazy='select', uselist=False)
	small_blind = db.Column(db.Float)
	

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
	poker_session_id = db.Column(UUIDType(binary=False), \
		db.ForeignKey('poker_sessions.id'))


class PokerHand(db.Model):
	__tablename__ = 'poker_hands'

	id = db.Column(db.Integer, primary_key=True)
	street = db.Column(db.Integer)
	bet_sizes = db.Column(db.PickleType)
	hole_cards = db.Column(db.PickleType)
	board = db.Column(db.PickleType)
	poker_session_id = db.Column(UUIDType(binary=False), \
		db.ForeignKey('poker_sessions.id'))


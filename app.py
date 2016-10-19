from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
import os
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import *

@app.route('/create/')
def hello():
	ps = PokerSession(3.0)
	db.session.add(ps)
	db.session.commit()
	return "Record created"
	

if __name__ == '__main__':
	app.run()
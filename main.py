from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Lens, User
import random, string

# IMPORTS FOR PAGINATION
from flask.ext.paginate import Pagination
from sqlalchemy import func

# IMPORTS FOR OAUTH STEP
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Share A Lens"

engine = create_engine('sqlite:///sharealens.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
session = DBSession()

@app.route('/')
def showHome():
	featured = session.query(Lens).limit(3)
	return render_template('index.html', featured = featured)


@app.route('/lenses')
def showLenses():
	search = True
	brand = request.args['brand']
	style = request.args['style']
	try:
		page = int(request.args.get('page', 1))
	except ValueError:
		page = 1
	offset = (page - 1) * 10
	if (brand == 'all' and style == 'all'):
		lenses = session.query(Lens).limit(10).offset(offset)
		rows = session.query(func.count(Lens.id)).scalar()
	elif (brand == 'all' and style != 'all'):
		lenses = session.query(Lens).filter_by(style=style).all()
		rows = session.query(func.count(Lens.id)).filter_by(style=style).scalar()
	elif (brand != 'all' and style == 'all'):
		lenses = session.query(Lens).filter_by(brand=brand).all()
		rows = session.query(func.count(Lens.id)).filter_by(brand=brand).scalar()
	else:
		lenses = session.query(Lens).filter_by(brand=brand).filter_by(style=style).all()
		rows = session.query(func.count(Lens.id)).filter_by(brand=brand).filter_by(style=style).scalar()
	pagination = Pagination(page=page, total=rows, search=search, record_name='lenses', found=rows, alignment='right')
	return render_template('lenses.html', lenses=lenses, pagination=pagination)


if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host='0.0.0.0', port=5000)
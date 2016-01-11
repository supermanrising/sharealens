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
	try:
		brand = request.args['brand']
	except ValueError:
		brand = 'all'
	try:
		style = request.args['style']
	except ValueError:
		style = 'all'
	try:
		page = int(request.args.get('page', 1))
	except ValueError:
		page = 1
	# offset variable is current page number * results per page
	offset = (page - 1) * 12
	# array to hold lens objects separated in groups of three
	lenses = []
	if (brand == 'all' and style == 'all'):
		lenses = session.query(Lens).order_by(Lens.name).limit(12).offset(offset)
		# count total rows.  Used for pagination
		rows = session.query(func.count(Lens.id)).scalar()
		# count total lenses visible on this page
		remaining = rows - (page - 1) * 12
	elif (brand == 'all' and style != 'all'):
		lenses = session.query(Lens).filter_by(style=style).order_by(Lens.name).limit(12).offset(offset)
		# count total rows.  Used for pagination
		rows = session.query(func.count(Lens.id)).filter_by(style=style).scalar()
		# count total lenses visible on this page
		remaining = rows - (page - 1) * 12
	elif (brand != 'all' and style == 'all'):
		lenses = session.query(Lens).filter_by(brand=brand).order_by(Lens.name).limit(12).offset(offset)
		# count total rows.  Used for pagination
		rows = session.query(func.count(Lens.id)).filter_by(brand=brand).scalar()
		# count total lenses visible on this page
		remaining = rows - (page - 1) * 12
	else:
		lenses = session.query(Lens).filter_by(brand=brand).filter_by(style=style).order_by(Lens.name).limit(12).offset(offset)
		# count total rows.  Used for pagination
		rows = session.query(func.count(Lens.id)).filter_by(brand=brand).filter_by(style=style).scalar()
		# count total lenses visible on this page
		remaining = rows - (page - 1) * 12
	brands = []
	for value in session.query(Lens.brand).distinct():
		brands.append(value[0])
	styles = []
	for value in session.query(Lens.style).distinct():
		styles.append(value[0])
	msg = 'Results <b>{start}</b> - <b>{end}</b> of <b>{found}</b> {record_name}'
	pagination = Pagination(page=page, total=rows, record_name='lenses', found=rows, css_framework='bootstrap3', display_msg=msg, per_page=12)
	return render_template('lenses.html', lenses=lenses, remaining=remaining, pagination=pagination, brands=brands, styles=styles)


if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host='0.0.0.0', port=5000)
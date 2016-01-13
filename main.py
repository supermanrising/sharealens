import os
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

# FOR UPLOADING PHOTOS
from werkzeug import secure_filename
UPLOAD_FOLDER = 'static/lens-img'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Share A Lens"

engine = create_engine('sqlite:///sharealens.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
session = DBSession()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/')
def showHome():
	if 'username' not in login_session:
		loggedIn = False
	else:
		loggedIn = True
	totalLenses = session.query(func.count(Lens.id)).scalar()
	featured = []
	for num in range(1,4):
		randomNumber = random.randrange(1, totalLenses)
		featured.append(session.query(Lens).filter_by(id=randomNumber).one())
	brands = []
	for value in session.query(Lens.brand).distinct():
		brands.append(value[0])
	styles = []
	for value in session.query(Lens.style).distinct():
		styles.append(value[0])
	return render_template('index.html', featured=featured, brands=brands, styles=styles, user=loggedIn)


@app.route('/lenses')
def showLenses():
	if 'username' not in login_session:
		loggedIn = False
	else:
		loggedIn = True
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
	elif (brand == 'all' and style != 'all'):
		lenses = session.query(Lens).filter_by(style=style).order_by(Lens.name).limit(12).offset(offset)
		# count total rows.  Used for pagination
		rows = session.query(func.count(Lens.id)).filter_by(style=style).scalar()
	elif (brand != 'all' and style == 'all'):
		lenses = session.query(Lens).filter_by(brand=brand).order_by(Lens.name).limit(12).offset(offset)
		# count total rows.  Used for pagination
		rows = session.query(func.count(Lens.id)).filter_by(brand=brand).scalar()
	else:
		lenses = session.query(Lens).filter_by(brand=brand).filter_by(style=style).order_by(Lens.name).limit(12).offset(offset)
		# count total rows.  Used for pagination
		rows = session.query(func.count(Lens.id)).filter_by(brand=brand).filter_by(style=style).scalar()
	brands = []
	for value in session.query(Lens.brand).distinct():
		brands.append(value[0])
	styles = []
	for value in session.query(Lens.style).distinct():
		styles.append(value[0])
	msg = 'Results <b>{start}</b> - <b>{end}</b> of <b>{found}</b> {record_name}'
	pagination = Pagination(page=page, total=rows, record_name='lenses', found=rows, css_framework='bootstrap3', display_msg=msg, per_page=12)
	return render_template('lenses.html', lenses=lenses, rows=rows, pagination=pagination, brands=brands, styles=styles, user=loggedIn)


@app.route('/lens/<int:lens_id>')
def showLens(lens_id):
	if 'username' not in login_session:
		loggedIn = False
	else:
		loggedIn = True
	currentuser = login_session.get('user_id')
	lens = session.query(Lens).filter_by(id=lens_id).first()
	brand = lens.brand
	style = lens.style
	related = session.query(Lens).filter_by(brand=brand).filter(Lens.id!=lens_id).filter_by(style=style).limit(5)
	return render_template('lens.html', lens=lens, related=related, user=loggedIn, currentuser=currentuser)


@app.route('/login/<string:next>')
def showLogin(next):
	if 'username' not in login_session:
		loggedIn = False
	else:
		loggedIn = True
	return render_template('login.html', user=loggedIn, next=next)


@app.route('/rent-your-gear', methods = ['GET', 'POST'])
def uploadLens():
	if 'username' not in login_session:
		return redirect(url_for('showLogin', next='rent-your-gear'))
	else:
		loggedIn = True
	if request.method == 'POST':
		file = request.files['file']
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		else:
			filename = None
		newLens = Lens(
			name = request.form['name'],
			picture = filename,
			user_id = login_session['user_id'],
			brand = request.form['brand'],
			style = request.form['style'],
			zoom_min = request.form['min-zoom'],
			zoom_max = request.form['max-zoom'],
			aperture = request.form['aperture'],
			price_per_day = request.form['price-day'],
			price_per_week = request.form['price-week'],
			price_per_month = request.form['price-month']
		)
		session.add(newLens)
		session.commit()
		flash("New Lens Created")
		return redirect(url_for('showLens', lens_id = newLens.id))
	else:
		return render_template('rent-your-gear.html', user=loggedIn)


@app.route('/edit/<int:lens_id>', methods = ['GET', 'POST'])
def editLens(lens_id):
	if 'username' not in login_session:
		return redirect(url_for('showLogin', next='rent-your-gear'))
	else:
		loggedIn = True
	lens = session.query(Lens).filter_by(id=lens_id).one()
	if lens.user_id != login_session['user_id']:
		return "<script>function myFunction() {alert('You are not authorized to edit this lens');}</script><body onload='myFunction()'>"
	if request.method == 'POST':
		if request.files['file']:
			file = request.files['file']
			if file and allowed_file(file.filename):
				filename = secure_filename(file.filename)
				file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
				lens.picture = filename
		if request.form['name']:
			lens.name = request.form['name']
		if request.form['brand']:
			lens.brand = request.form['brand']
		if request.form['style']:
			lens.style = request.form['style']
		if request.form['min-zoom']:
			lens.zoom_min = request.form['min-zoom']
		if request.form['max-zoom']:
			lens.zoom_max = request.form['max-zoom']
		if request.form['aperture']:
			lens.aperture = request.form['aperture']
		if request.form['price-day']:
			lens.price_per_day = request.form['price-day']
		if request.form['price-week']:
			lens.price_per_week = request.form['price-week']
		if request.form['price-month']:
			lens.price_per_month = request.form['price-month']

		session.add(lens)
		session.commit()
		flash("Lens Successfully Edited")
		return redirect(url_for('showLens', lens_id = lens_id))
	else:
		return render_template('edit-lens.html', user=loggedIn, lens=lens)


@app.route('/getState')
def generateState():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
	login_session['state'] = state
	return state


@app.route('/gconnect', methods=['POST'])
def gconnect():
	# Validate state token
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# Obtain authorization code
	# this was passed here as POST data by AJAX request in login.html
	# data: authResult.code
	code = request.data

	try:
		# Upgrade the authorization code into a credentials object
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(
			json.dumps('Failed to upgrade the authorization code.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Check that the access token is valid.
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
			% access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	# If there was an error in the access token info, abort.
	if result.get('error') is not None:
		print result.get('error')
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'

	# Verify that the access token is used for the intended user.
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(
			json.dumps("Token's user ID doesn't match given user ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Verify that the access token is valid for this app.
	if result['issued_to'] != CLIENT_ID:
		response = make_response(
			json.dumps("Token's client ID does not match app's."), 401)
		print "Token's client ID does not match app's."
		response.headers['Content-Type'] = 'application/json'
		return response

	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is already connected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Store the access token in the session for later use.
	login_session['credentials'] = credentials.access_token
	login_session['gplus_id'] = gplus_id

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']
	# ADD PROVIDER TO LOGIN SESSION
	login_session['provider'] = 'google'

	# if user exists, store user id in login_session
	# if not, create user
	user_id = getUserID(login_session['email'])
	if not user_id:
		user_id = createUser(login_session)
	login_session['user_id'] = user_id

	output = ''
	output += '<h1>Welcome, '
	output += login_session['username']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	flash("you are now logged in as %s" % login_session['username'])
	print "done!"
	return output


@app.route('/fbdisconnect')
def fbdisconnect():
	facebook_id = login_session['facebook_id']
	# The access token must me included to successfully logout
	access_token = login_session['access_token']
	url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
	h = httplib2.Http()
	result = h.request(url, 'DELETE')[1]
	del login_session['username']
	del login_session['email']
	del login_session['picture']
	del login_session['user_id']
	del login_session['facebook_id']
	return "you have been logged out"


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
	print 'disconnecting'
	if 'credentials' not in login_session:
		print 'Access Token is None'
		response = make_response(json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = login_session['credentials']
	print 'In gdisconnect access token is %s', access_token
	print 'User name is: ' 
	print login_session['username']
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['credentials']
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]
	print 'result is '
	print result
	if result['status'] == '200':
		del login_session['credentials'] 
		del login_session['gplus_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		del login_session['user_id']
		response = make_response(json.dumps('Successfully disconnected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response
	else:
		response = make_response(json.dumps('Failed to revoke token for given user.', 400))
		response.headers['Content-Type'] = 'application/json'
		return response


# Disconnect based on provider
@app.route('/logout')
def disconnect():
    if 'provider' in login_session:
    	print login_session['provider']
        if login_session['provider'] == 'google':
            gdisconnect()
        if login_session['provider'] == 'facebook':
            fbdisconnect()
        del login_session['provider']
        flash("You have successfully been logged out.")
        print 'success'
        return redirect(url_for('showHome'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showHome'))


# User Helper Functions
def createUser(login_session):
	newUser = User(
		name=login_session['username'],
		email=login_session['email'],
		picture=login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email=login_session['email']).one()
	return user.id


def getUserInfo(user_id):
	user = session.query(User).filter_by(id=user_id).one()
	return user


def getUserID(email):
	try:
		user = session.query(User).filter_by(email=email).one()
		return user.id
	except:
		return None


if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host='0.0.0.0', port=5000)
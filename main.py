import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, \
    flash, jsonify, Markup
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Lens, User, Rental

from flask.ext.paginate import Pagination
from sqlalchemy import func

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

from datetime import date, timedelta as td

import xml.etree.ElementTree as ET
from ElementTree_pretty import prettify

from werkzeug import secure_filename
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())[
        'web']['client_id']
APPLICATION_NAME = 'Share A Lens'

engine = create_engine('sqlite:///sharealens.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def allowed_file(filename):
    """Return a filename if it has an allowed extension.
    """
    return '.' in filename and filename.rsplit('.', 1)[1] \
        in ALLOWED_EXTENSIONS


@app.route('/')
def showHome():
    if 'username' not in login_session:
        user = None
    else:
        currentuser = login_session.get('user_id')
        user = session.query(User).filter_by(id=currentuser).one()
    # Get all lens ID's and store in an array
    lensIDs = session.query(Lens.id).all()
    allLenses = []
    for id in lensIDs:
        allLenses.append(id[0])
    # empty array to store featured lenses
    featured = []
    for num in range(1, 4):
        # Generate a random lens ID from the allLenses array
        randomNumber = random.choice(allLenses)
        # Remove this lens ID so it doesn't get choses twice
        allLenses.remove(randomNumber)
        # append randomly choses lens to the featured array
        featured.append(session.query(Lens).filter_by(id=randomNumber).one())

    # Get distinct brand names
    brands = []
    for value in session.query(Lens.brand).distinct():
        brands.append(value[0])

    # Get distinct styles
    styles = []
    for value in session.query(Lens.style).distinct():
        styles.append(value[0])

    return render_template('index.html', featured=featured,
                           brands=brands, styles=styles, user=user)


@app.route('/lenses')
def showLenses():
    if 'username' not in login_session:
        user = None
    else:
        currentuser = login_session.get('user_id')
        user = session.query(User).filter_by(id=currentuser).one()
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

    # offset variable for pagination
    # current page number * results per page
    offset = (page - 1) * 12

    if brand == 'all' and style == 'all':
        lenses = \
            session.query(Lens).order_by(Lens.name).limit(12).offset(offset)
        # count total rows.  Used for pagination
        rows = session.query(func.count(Lens.id)).scalar()
    elif brand == 'all' and style != 'all':
        lenses = \
            session.query(Lens).filter_by(style=style).order_by(
            	Lens.name).limit(12).offset(offset)
        # count total rows.  Used for pagination
        rows = \
            session.query(func.count(Lens.id)).filter_by(style=style).scalar()
    elif brand != 'all' and style == 'all':
        lenses = \
            session.query(Lens).filter_by(brand=brand).order_by(
                Lens.name).limit(12).offset(offset)
        # count total rows.  Used for pagination
        rows = \
            session.query(func.count(Lens.id)).filter_by(brand=brand).scalar()
    else:
        lenses = \
            session.query(Lens).filter_by(brand=brand).filter_by(
                style=style).order_by(Lens.name).limit(12).offset(offset)
        # count total rows.  Used for pagination
        rows = \
            session.query(func.count(Lens.id)).filter_by(
                brand=brand).filter_by(style=style).scalar()
    # Get distinct brand names
    brands = []
    for value in session.query(Lens.brand).distinct():
        brands.append(value[0])

    # Get distinct style names
    styles = []
    for value in session.query(Lens.style).distinct():
        styles.append(value[0])

    msg = \
        'Results <b>{start}</b> - <b>{end}</b> of <b>{found}</b> {record_name}'
    pagination = Pagination(
        page=page,
        total=rows,
        record_name='lenses',
        found=rows,
        css_framework='bootstrap3',
        display_msg=msg,
        per_page=12
    )
    return render_template(
        'lenses.html',
        lenses=lenses,
        rows=rows,
        pagination=pagination,
        brands=brands,
        styles=styles,
        user=user
    )


@app.route('/lens/<int:lens_id>')
def showLens(lens_id):
    if 'username' not in login_session:
        user = None
    else:
        currentuser = login_session.get('user_id')
        user = session.query(User).filter_by(id=currentuser).one()
    lens = session.query(Lens).filter_by(id=lens_id).first()
    brand = lens.brand
    style = lens.style

    # Get related lenses
    related = session.query(Lens).filter_by(brand=brand).filter(
        Lens.id != lens_id).filter_by(style=style).limit(5)

    return render_template('lens.html', lens=lens, related=related,
                           user=user)


@app.route('/login/<string:next>')
def showLogin(next):
    if 'username' not in login_session:
        user = None
    else:
        currentuser = login_session.get('user_id')
        user = session.query(User).filter_by(id=currentuser).one()
    return render_template('login.html', user=user, next=next)


@app.route('/rent-your-gear', methods=['GET', 'POST'])
def uploadLens():
    if 'username' not in login_session:
        return redirect(url_for('showLogin', next='rent-your-gear'))
    else:
        currentuser = login_session.get('user_id')
        user = session.query(User).filter_by(id=currentuser).one()
    if request.method == 'POST':
        # If this is a prime lens, max zoom is the same as min zoom
        if request.form['style'] == 'Prime':
            maximumZoom = request.form['min-zoom']
        else:
            maximumZoom = request.form['max-zoom']

        newLens = Lens(
            name=request.form['name'],
            picture=None,
            user_id=login_session['user_id'],
            brand=request.form['brand'],
            style=request.form['style'],
            zoom_min=request.form['min-zoom'],
            zoom_max=maximumZoom,
            aperture=request.form['aperture'],
            price_per_day=request.form['price-day'],
            price_per_week=request.form['price-week'],
            price_per_month=request.form['price-month']
        )

        session.add(newLens)

        # flush and refresh to access the lens ID
        # More info here:
        # http://stackoverflow.com/questions/1316952/sqlalchemy-flush-and-get-inserted-id

        session.flush()
        session.refresh(newLens)

        # Get the picture item
        file = request.files['file']
        # If the image is an allowed extension (defined above)
        if file and allowed_file(file.filename):
            # create secure filename
            filename = secure_filename(file.filename)
            # define upload folder, each lens has it's own image folder
            UPLOAD_FOLDER = 'static/lens-img/' + str(newLens.id)
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
            # save image in upload folder
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],
                      filename))
            # save url string in lens database object
            newLens.picture = str(newLens.id) + '/' + filename
        session.add(newLens)
        session.commit()

        message = \
            Markup('<b>Well done!</b>  Your lens has been uploaded.')
        flash(message, 'success')
        return redirect(url_for('showLens', lens_id=newLens.id))
    else:
        return render_template('rent-your-gear.html', user=user)


@app.route('/edit/<int:lens_id>', methods=['GET', 'POST'])
def editLens(lens_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin', next='account?showRentals=lenses'))
    else:
        currentuser = login_session.get('user_id')
        user = session.query(User).filter_by(id=currentuser).one()

    # query the lens to edit
    lens = session.query(Lens).filter_by(id=lens_id).one()
    # if the lens user id does not match the login session user id
    # return an error alert
    if lens.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert(" + \
            "'You are not authorized to edit this lens');}</script>" + \
            "<body onload='myFunction()'>"

    if request.method == 'POST':
        if request.files['file']:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                UPLOAD_FOLDER = 'static/lens-img/' + str(lens.id)
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)
                app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
                file.save(os.path.join(app.config['UPLOAD_FOLDER'],
                          filename))
                lens.picture = str(lens.id) + '/' + filename
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

        message = Markup('<b>Well done!</b>  Your lens has been edited.'
                         )
        flash(message, 'success')
        return redirect(url_for('showLens', lens_id=lens_id))
    else:
        return render_template('edit-lens.html', user=user, lens=lens)


@app.route('/delete/<int:lens_id>', methods=['GET', 'POST'])
def deleteLens(lens_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin', next='account?showRentals=lenses'))
    else:
        currentuser = login_session.get('user_id')
        user = session.query(User).filter_by(id=currentuser).one()
    lens = session.query(Lens).filter_by(id=lens_id).one()
    if lens.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('" + \
            "You are not authorized to delete this lens');}</script>" + \
            "<body onload='myFunction()'>"
    if request.method == 'POST':

        # Protect against CSRF
        secret_key = request.form['CSRFToken']
        # if the secret key from the form submit does not match
        # the secret key from the user's login session
        # return an error alert
        if secret_key != login_session.get('user_secret'):
            return "<script>function myFunction() {alert('" + \
                "We enountered a problem.');}</script>" + \
                "<body onload='myFunction()'>"

        session.delete(lens)
        session.commit()
        flash('Your lens has been deleted.', 'success')
        return redirect(url_for('showAccount', showRentals='lenses'))
    else:
        user_secret_key = login_session.get('user_secret')
        return render_template('delete-lens.html', user=user,
                               lens=lens, secret=user_secret_key)


@app.route('/getState')
def generateState():
    """Creates state token.  Called via ajax"""
    state = ''.join(random.choice(string.ascii_uppercase +
                    string.digits) for x in range(32))
    login_session['state'] = state
    return state


@app.route('/gconnect', methods=['POST'])
def gconnect():

    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'
                                            ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    # this was passed here as POST data by AJAX request in login.html
    # data: authResult.code
    code = request.data

    try:

        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json',
                                             scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = \
            make_response(json.dumps('Failed to upgrade the authorization code.'
                                     ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = \
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' \
        % access_token
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
        response = \
            make_response(json.dumps("Token's user ID doesn't match given user ID."
                                     ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = \
            make_response(json.dumps("Token's client ID does not match app's."
                                     ), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = \
            make_response(json.dumps('Current user is already connected.'
                                     ), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # Create token and add to login session to prevent CSRF
    user_secret_key = ''.join(random.choice(string.ascii_uppercase +
                              string.digits) for x in range(32))
    login_session['user_secret'] = user_secret_key

    # if user exists, store user id in login_session
    # if not, create user
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    user = getUserInfo(user_id)

    # if picture has changed, update it
    if user.picture != login_session['picture']:
        user.picture = login_session['picture']
        session.add(user)
        session.commit()

    output = 'Success'
    message = \
        Markup('<strong>Success!</strong>  You are now logged in as %s'
               % login_session['username'])
    flash(message, 'success')
    return output


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'
                                            ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print 'access token received %s ' % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r'
                             ).read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r'
                                 ).read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=' + \
        'fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' \
        % (app_id, app_secret, access_token)

    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    print result

    # Use token to get user info from API
    userinfo_url = 'https://graph.facebook.com/v2.4/me'

    # strip expire tag from access token
    token = result.split('&')[0]

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' \
        % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    # Create token and add to login session to prevent CSRF
    user_secret_key = ''.join(random.choice(string.ascii_uppercase +
                              string.digits) for x in range(32))
    login_session['user_secret'] = user_secret_key

    # The token must be stored in the login_session in order to properly logout
    # let's strip out the information before the equals sign in our token
    stored_token = token.split('=')[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture' + \
        '?%s&redirect=0&height=200&width=200' \
        % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data['data']['url']

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    user = getUserInfo(user_id)

    # if picture has changed, update it
    if user.picture != login_session['picture']:
        user.picture = login_session['picture']
        session.add(user)
        session.commit()

    output = 'Success'

    message = \
        Markup('<strong>Success!</strong>  You are now logged in as %s'
               % login_session['username'])
    flash(message, 'success')
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']

    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' \
        % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    del login_session['facebook_id']
    del login_session['access_token']
    return 'you have been logged out'


# DISCONNECT - Revoke a current user's token and reset their login_session

@app.route('/gdisconnect')
def gdisconnect():
    print 'disconnecting'
    if 'credentials' not in login_session:
        print 'Access Token is None'
        response = \
            make_response(json.dumps('Current user not connected.'),
                          401)
        response.headers['Content-Type'] = 'application/json'

        # Make sure everything else is deleted as well
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['access_token']
        return response
    access_token = login_session['credentials']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
        % login_session['credentials']
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
        del login_session['access_token']
        response = make_response(json.dumps('Successfully disconnected.'
                                            ), 200)
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
        if login_session['provider'] == 'google':
            gdisconnect()
        if login_session['provider'] == 'facebook':
            fbdisconnect()
        del login_session['provider']
        flash('You have successfully been logged out.', 'success')
        return redirect(url_for('showHome'))
    else:
        flash('You were not logged in', 'warning')

        # I was having some problems with cookies being deleted over time
        # It caused issues logging out, so I delete login_session data here as well

        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['access_token']
        del login_session['provider']
        return redirect(url_for('showHome'))


@app.route('/account')
def showAccount():
    if 'username' not in login_session:
        return redirect(url_for('showLogin', next='account?showRentals=lenses'))
    else:
        currentuser = login_session.get('user_id')
        user = session.query(User).filter_by(id=currentuser).one()
    try:
        showRentals = request.args['showRentals']
    except ValueError:
        showRentals = 'lenses'
    lenses = session.query(Lens).filter_by(user_id=user.id).all()
    rentals = session.query(Rental).filter_by(renter_id=user.id).all()
    return render_template('account.html', user=user, lenses=lenses,
                           rentals=rentals, showRentals=showRentals)


@app.route('/request/<int:lens_id>', methods=['GET', 'POST'])
def requestRental(lens_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin', next='account?showRentals=lenses'))
    else:
        currentuser = login_session.get('user_id')
        user = session.query(User).filter_by(id=currentuser).one()
    lens = session.query(Lens).filter_by(id=lens_id).one()

    # Get all rentals for this lens
    rentals = session.query(Rental).filter_by(lens_id=lens.id)
    dates = []
    # For each rental, store all rented dates in dates array
    for rental in rentals:
        startDate = rental.start_date
        endDate = rental.end_date
        delta = endDate - startDate
        for i in range(delta.days + 1):
            thisDate = startDate + td(days=i)
            dates.append(thisDate.strftime('%Y-%m-%d'))

    if request.method == 'POST':
        start = request.form['startDate']
        end = request.form['endDate']
        start = start.split(' ')
        end = end.split(' ')
        start = map(int, start)
        end = map(int, end)
        # Create rental object with start and end date objects
        newRental = Rental(
            start_date=date(start[0], start[1], start[2]),
            end_date=date(end[0], end[1], end[2]),
            renter_id=login_session.get('user_id'),
            owner_id=lens.user_id, lens_id=lens.id
        )

        checkStart = newRental.start_date.strftime('%Y-%m-%d')
        checkEnd = newRental.end_date.strftime('%Y-%m-%d')

        try:
            startIndex = dates.index(checkStart)
        except ValueError:
            startIndex = -1

        try:
            endIndex = dates.index(checkEnd)
        except ValueError:
            endIndex = -1

        # If the dates array includes either the start or end date, cancel the rental
        # This should never happen anyway, since the dates are disabled in the frontend code
        if startIndex != -1 or endIndex != -1:
            return "<script>function myFunction() {alert('Oops!  " + \
                "It looks like the lens you requested is alread rented on those dates. " + \
                "Please go back and try again.');}</script><body onload='myFunction()'>"

        session.add(newRental)
        session.commit()

        message = \
            Markup('<strong>Well done!</strong> Your lens rental request has been approved.'
                   )
        flash(message, 'success')
        return redirect(url_for('showAccount', showRentals='rentals'))
    else:
        return render_template('request.html', user=user, lens=lens,
                               dates=dates)


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email'
                                                             ]).one()
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


# JSON APIs to view Lens Information
@app.route('/lenses/JSON')
def lensesJSON():
    lenses = session.query(Lens).all()
    return jsonify(Lenses=[i.serialize for i in lenses])


@app.route('/lens/<int:lens_id>/JSON')
def lensJSON(lens_id):
    lens = session.query(Lens).filter_by(id=lens_id).one()
    return jsonify(Lens=lens.serialize)


# XML API to view Lens Information
@app.route('/lenses/XML')
def lensesRSS():
    lensesQuery = session.query(Lens).all()

    lenses = ET.Element('lenses')
    for i in lensesQuery:
        lens = ET.SubElement(lenses, 'lens')
        id = ET.SubElement(lens, 'id').text = str(i.id)
        name = ET.SubElement(lens, 'name').text = i.name
        brand = ET.SubElement(lens, 'brand').text = i.brand
        style = ET.SubElement(lens, 'type').text = i.style
        zoom_min = ET.SubElement(lens, 'zoom_min').text = \
            str(i.zoom_min)
        zoom_max = ET.SubElement(lens, 'zoom_max').text = \
            str(i.zoom_max)
        aperture = ET.SubElement(lens, 'aperture').text = \
            str(i.aperture)
        price_per_day = ET.SubElement(lens, 'price_per_day').text = \
            str(i.price_per_day)
        price_per_week = ET.SubElement(lens, 'price_per_week').text = \
            str(i.price_per_week)
        price_per_month = ET.SubElement(lens, 'price_per_month').text = \
            str(i.price_per_month)

    print prettify(lenses)
    return prettify(lenses)


@app.route('/lens/<int:lens_id>/XML')
def lensXML(lens_id):
    query = session.query(Lens).filter_by(id=lens_id).one()
    lens = ET.Element('lens')
    id = ET.SubElement(lens, 'id').text = str(query.id)
    name = ET.SubElement(lens, 'name').text = query.name
    brand = ET.SubElement(lens, 'brand').text = query.brand
    style = ET.SubElement(lens, 'type').text = query.style
    zoom_min = ET.SubElement(lens, 'zoom_min').text = \
        str(query.zoom_min)
    zoom_max = ET.SubElement(lens, 'zoom_max').text = \
        str(query.zoom_max)
    aperture = ET.SubElement(lens, 'aperture').text = \
        str(query.aperture)
    price_per_day = ET.SubElement(lens, 'price_per_day').text = \
        str(query.price_per_day)
    price_per_week = ET.SubElement(lens, 'price_per_week').text = \
        str(query.price_per_week)
    price_per_month = ET.SubElement(lens, 'price_per_month').text = \
        str(query.price_per_month)

    print prettify(lens)
    return prettify(lens)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)

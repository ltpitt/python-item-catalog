from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask import session as login_session
from flask import make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
from database_setup import Base, User, Category, Item
from werkzeug import secure_filename
import random, string
import os
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json

import requests


UPLOAD_FOLDER = 'static/images/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog"

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

engine = create_engine('sqlite:///item-catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# Create anti-forgery state token
@app.route('/login')
def show_login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.2/me"
    # strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.2/me?%s' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.2/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
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

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
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
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
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

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
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
    flash(u'You are now logged in as %s' % login_session['username'], 'success')
    print "done!"
    return output


# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
        'email'], picture=login_session['picture'])
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


# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    for i in login_session:
        print i
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    print url
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash(u'You have successfully been logged out', 'success')
        return redirect(url_for('show_catalog'))
    else:
        flash(u'You were not logged in', 'error')
        return redirect(url_for('show_catalog'))


@app.route('/')
@app.route('/catalog/')
def show_catalog():
    """
    Render the catalog page with all the categories and
    a selection of the latest items inserted
    """
    categories = session.query(Category).order_by(Category.name).all()
    # Shows 6 newer items
    items = session.query(Item).order_by(desc(Item.id)).limit(6)
    if 'username' in login_session:
        user = getUserInfo(login_session['user_id'])
        return render_template('catalog.html', categories=categories, items=items, user=user)
    else:
        return render_template('catalog.html', categories=categories, items=items)


@app.route('/new', methods=['GET', 'POST'])
@app.route('/catalog/new', methods=['GET', 'POST'])
def new_category():
    """
    Get: Show the form allowing an authenticated user to create a category
    Post: Allow an authenticated user to create a category
    """
    if 'username' not in login_session:
        return redirect('/login')
    user = getUserInfo(login_session['user_id'])
    categories = session.query(Category).order_by(Category.name).all()
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['inputCategoryName'],
            description=request.form['inputCategoryDescription'],
            user_id=user.id
        )
        session.add(newCategory)
        session.commit()
        flash(u'Category added successfully', 'success')
        return redirect(url_for('show_catalog'))
    else:
        return render_template('new_category.html', categories=categories, user=user)


@app.route('/catalog/<int:category_id>/edit', methods=['GET', 'POST'])
def edit_category(category_id):
    """
    Get: Show to the authenticated user a form to change the category data
    Post: Allow authenticated user to change category data
    """
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(Category.name).all()
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if login_session['user_id'] == editedCategory.user_id:
            if request.form['inputCategoryName']:
                editedCategory.name = request.form['inputCategoryName']
            if request.form['inputCategoryDescription']:
                editedCategory.description = request.form['inputCategoryDescription']
            session.add(editedCategory)
            session.commit()
            flash(u'Category edited successfully', 'success')
            return redirect(url_for('show_catalog'))
        else:
            flash(u'Insufficient rights to edit this category', 'error')
            return redirect(url_for('show_catalog'))
    else:
        if login_session['user_id'] == editedCategory.user_id:
            user = getUserInfo(login_session['user_id'])
            return render_template('edit_category.html', category=editedCategory, categories=categories, user=user)
        else:
            flash(u'Insufficient rights to edit this category', 'error')
            return redirect(url_for('category_items', category_id=category_id))


@app.route('/catalog/<int:category_id>/delete', methods=['GET', 'POST'])
def delete_category(category_id):
    """
    Get: Show to the authenticated user a form to confirm category deletion
    Post: Allow authenticated user to delete category
    """
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(Category.name).all()
    deletedCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        session.delete(deletedCategory)
        session.commit()
        flash(u'Category deleted successfully', 'success')
        return redirect(url_for('show_catalog'))
    else:
        if login_session['user_id'] == deletedCategory.user_id:
            user = getUserInfo(login_session['user_id'])
            return render_template('delete_category.html', category=deletedCategory, categories=categories, user=user)
        else:
            flash(u'Insufficient rights to delete this category', 'error')
            return redirect(url_for('category_items', category_id=category_id))


@app.route('/catalog/<int:category_id>/')
@app.route('/catalog/<int:category_id>/items')
def category_items(category_id):
    """
    Render a catalog page with items present in a specific category
    """
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).order_by(Category.name).all()
    items = session.query(Item).filter_by(category_id=category_id).order_by(Item.name).all()
    total_items = len(items)
    if 'username' not in login_session:
        return render_template('category.html', category=category, items=items, categories=categories,
                               total_items=total_items)
    else:
        user = getUserInfo(login_session['user_id'])
        return render_template('category.html', category=category, items=items, categories=categories, user=user,
                               total_items=total_items)


@app.route('/catalog/<int:category_id>/<int:item_id>', methods=['GET', 'POST'])
def show_item(category_id, item_id):
    """
    Render the item page
    """
    categories = session.query(Category).order_by(Category.name).all()
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    if 'username' not in login_session:
        return render_template('item.html', category=category, item=item, categories=categories)
    else:
        user = getUserInfo(login_session['user_id'])
        return render_template('item.html', category=category, item=item, categories=categories, user=user)


@app.route('/catalog/<int:category_id>/new', methods=['GET', 'POST'])
def new_item(category_id):
    """
    Get: Show the form allowing an authenticated user to create an item in specified category
    Post: Allow an authenticated user to create an item in specified category
    """
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).order_by(Category.name).all()
    user = getUserInfo(login_session['user_id'])
    if request.method == 'POST':
        newItem = Item(
            name=request.form['inputItemName'],
            description=request.form['inputItemDescription'],
            price=request.form['inputItemPrice'],
            image="",
            category_id=category_id,
            user_id=user.id
        )
        session.add(newItem)
        session.commit()
        file = request.files['inputItemImage']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_extension = os.path.splitext(filename)[1]
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], str(newItem.id) + file_extension)
            file.save(image_path)
            newItem.image = "/" + image_path
            session.add(newItem)
            session.commit()
        flash(u'Item added successfully', 'success')
        return redirect(url_for('category_items', category_id=category_id))
    else:
        user = getUserInfo(login_session['user_id'])
        return render_template('new_item.html', category=category, categories=categories, user=user)


@app.route('/catalog/<int:category_id>/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(category_id, item_id):
    """
    Get: Show to the authenticated user a form to change an item data
    Post: Allow authenticated user to change an item data
    """
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).order_by(Category.name).all()
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        if login_session['user_id'] == editedItem.user_id:
            if request.form['inputItemName']:
                editedItem.name = request.form['inputItemName']
            if request.form['inputItemDescription']:
                editedItem.description = request.form['inputItemDescription']
            if request.form['inputItemPrice']:
                editedItem.price = request.form['inputItemPrice']
            if request.form['inputItemCategory']:
                editedItem.category_id = request.form['inputItemCategory']
            file = request.files['inputItemImage']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_extension = os.path.splitext(filename)[1]
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], str(editedItem.id) + file_extension)
                file.save(image_path)
                editedItem.image = "/" + image_path
            session.add(editedItem)
            session.commit()
            flash(u'Item edited successfully', 'success')
            return redirect(url_for('show_catalog'))
        else:
            flash(u'Insufficient rights to edit this item', 'error')
            return redirect(url_for('category_items', category_id=category_id))
    else:
        user = getUserInfo(login_session['user_id'])
        if login_session['user_id'] == editedItem.user_id:
            return render_template('edit_item.html', item=editedItem, category=category, categories=categories,
                                   user=user)
        else:
            flash(u'Insufficient rights to edit this item', 'error')
            return redirect(url_for('category_items', category_id=category_id))


@app.route('/catalog/<int:category_id>/<int:item_id>/delete', methods=['GET', 'POST'])
def delete_item(category_id, item_id):
    """
    Render the catalog page with all categories and items present in the db
    """
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).order_by(Category.name).all()
    deletedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        if login_session['user_id'] == editedItem.user_id:
            session.delete(deletedItem)
            session.commit()
            flash(u'Item deleted successfully', 'success')
            return redirect(url_for('show_catalog'))
        else:
            flash(u'Insufficient rights to delete this item', 'error')
            return redirect(url_for('category_items', category_id=category_id))
    else:
        user = getUserInfo(login_session['user_id'])
        if login_session['user_id'] == deletedItem.user_id:
            return render_template('delete_item.html', item=deletedItem, category=category, categories=categories,
                                   user=user)
        else:
            flash(u'Insufficient rights to delete this item', 'error')
            return redirect(url_for('category_items', category_id=category_id))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)

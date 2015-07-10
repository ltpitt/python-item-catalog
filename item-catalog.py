from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
from database_setup import Base, User, Category, Item
from werkzeug import secure_filename
import os

UPLOAD_FOLDER = 'static/images/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

engine = create_engine('sqlite:///item-catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/login')
def login():
    """
    Render login page to allow user login
    """
    return render_template('login.html')


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
    return render_template('catalog.html', categories=categories, items=items)


@app.route('/new', methods=['GET', 'POST'])
@app.route('/catalog/new', methods=['GET', 'POST'])
def new_category():
    """
    Get: Show the form allowing an authenticated user to create a category
    Post: Allow an authenticated user to create a category
    """
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['inputCategoryName'],
            description=request.form['inputCategoryDescription']
        )
        session.add(newCategory)
        session.commit()
        return redirect(url_for('show_catalog'))

    else:
        return render_template('new_category.html')


@app.route('/catalog/<int:category_id>/edit', methods=['GET', 'POST'])
def edit_category(category_id):
    """
    Get: Show to the authenticated user a form to change the category data
    Post: Allow authenticated user to change category data
    """
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['inputCategoryName']:
            editedCategory.name = request.form['inputCategoryName']
        if request.form['inputCategoryDescription']:
            editedCategory.description = request.form['inputCategoryDescription']
        session.add(editedCategory)
        session.commit()
        return redirect(url_for('show_catalog'))
    else:
        return render_template('edit_category.html', category=editedCategory)


@app.route('/catalog/<int:category_id>/delete', methods=['GET', 'POST'])
def delete_category(category_id):
    """
    Get: Show to the authenticated user a form to confirm category deletion
    Post: Allow authenticated user to delete category
    """
    deletedCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        session.delete(deletedCategory)
        session.commit()
        return redirect(url_for('show_catalog'))
    else:
        return render_template('delete_category.html', category=deletedCategory)

@app.route('/catalog/<int:category_id>/')
@app.route('/catalog/<int:category_id>/items')
def category_items(category_id):
    """
    Render a catalog page with items present in a specific category
    """
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).order_by(Item.name).all()
    return render_template('category.html', category=category, items=items)

@app.route('/catalog/<int:category_id>/<int:item_id>', methods=['GET', 'POST'])
def show_item(category_id, item_id):
    """
    Render the item page
    """
    item = session.query(Item).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    return render_template('item.html', category=category, item=item)

@app.route('/catalog/<int:category_id>/new', methods=['GET', 'POST'])
def new_item(category_id):
    """
    Get: Show the form allowing an authenticated user to create an item in specified category
    Post: Allow an authenticated user to create an item in specified category
    """
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).order_by(Category.name).all()
    if request.method == 'POST':
        newItem = Item(
            name=request.form['inputItemName'],
            description=request.form['inputItemDescription'],
            price=request.form['inputItemPrice'],
            image="",
            category_id=category_id
        )
        session.add(newItem)
        session.commit()
        file = request.files['inputItemImage']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_extension = os.path.splitext(filename)[1]
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], str(newItem.id)+file_extension)
            file.save(image_path)
            newItem.image="/"+image_path
            session.add(newItem)
            session.commit()
        return redirect(url_for('category_items', category_id=category_id))
    else:
        return render_template('new_item.html', category=category, categories=categories)

@app.route('/catalog/<int:category_id>/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(category_id, item_id):
    """
    Get: Show to the authenticated user a form to change an item data
    Post: Allow authenticated user to change an item data
    """
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).order_by(Category.name).all()
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['inputItemName']:
            editedItem.name = request.form['inputItemName']
        if request.form['inputItemDescription']:
            editedItem.description = request.form['inputItemDescription']
        if request.form['inputItemPrice']:
            editedItem.price = request.form['inputItemPrice']
        if request.form['inputItemCategory']:
            editedItem.category_id = request.form['inputItemCategory']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('show_catalog'))
    else:
        return render_template('edit_item.html', item=editedItem, category=category, categories=categories)


@app.route('/catalog/<int:category_id>/<int:item_id>/delete', methods=['GET', 'POST'])
def delete_item(category_id, item_id):
    """
    Render the catalog page with all categories and items present in the db
    """
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).order_by(Category.name).all()
    deletedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['inputItemName']:
            deletedItem.name = request.form['inputItemName']
        if request.form['inputItemDescription']:
            deletedItem.description = request.form['inputItemDescription']
        if request.form['inputItemPrice']:
            deletedItem.price = request.form['inputItemPrice']
        if request.form['inputItemCategory']:
            deletedItem.price = request.form['inputItemCategory']
        session.add(deletedItem)
        session.commit()
        return redirect(url_for('show_catalog'))
    else:
        return render_template('delete_item.html', item=deletedItem, category=category, categories=categories)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)

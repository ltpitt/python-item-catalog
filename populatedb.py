from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

app = Flask(__name__)

engine = create_engine('sqlite:///item-catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

newCategory = Category(
    name="Category 1",
    description="Description Category 1"
)

session.add(newCategory)
session.commit()

newCategory = Category(
    name="Category 2",
    description="Description Category 2"
)

session.add(newCategory)
session.commit()

newItem = Item(
    name="Item 1",
    description="Description Item 1",
    price="10",
    image="/static/images/test.jpg",
    category_id=1
)

session.add(newItem)
session.commit()

newItem = Item(
    name="Item 2",
    description="Description Item 2",
    price="20",
    image="/static/images/test.jpg",
    category_id=2
)

session.add(newItem)
session.commit()

newItem = Item(
    name="Item 3",
    description="Description Item 3",
    price="30",
    image="/static/images/test.jpg",
    category_id=1
)

session.add(newItem)
session.commit()

newItem = Item(
    name="Item 4",
    description="Description Item 4",
    price="40",
    image="/static/images/test.jpg",
    category_id=1
)

session.add(newItem)
session.commit()

newItem = Item(
    name="Item 5",
    description="Description Item 5",
    price="50",
    image="/static/images/test.jpg",
    category_id=2
)

session.add(newItem)
session.commit()

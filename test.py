from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

app = Flask(__name__)

engine = create_engine('sqlite:///item-catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


editedItem = session.query(Item).filter_by(id=1).one()


editedItem.name = "geppo"
editedItem.description = "descr"
editedItem.price = "10"
editedItem.category_id = 1
session.add(editedItem)
session.commit()

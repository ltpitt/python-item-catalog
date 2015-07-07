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
	name="Categoria 1",
	description="Descrizione Categoria 1"
)

session.add(newCategory)
session.commit()

newCategory = Category(
        name="Categoria 2",
        description="Descrizione Categoria 2"
)

session.add(newCategory)
session.commit()


newItem = Item(
            name="Oggetto 1",
            description="Descrizione Oggetto 1",
            price="10",
	    category_id = 1
        )

session.add(newItem)
session.commit()

newItem = Item(
            name="Oggetto 2",
            description="Descrizione Oggetto 2",
            price="20",
            category_id = 2
        )

session.add(newItem)
session.commit()

newItem = Item(
            name="Oggetto 3",
            description="Descrizione Oggetto 3",
            price="30",
            category_id = 1
        )

session.add(newItem)
session.commit()

newItem = Item(
            name="Oggetto 4",
            description="Descrizione Oggetto 4",
            price="40",
            category_id = 1
        )

session.add(newItem)
session.commit()

newItem = Item(
            name="Oggetto 5",
            description="Descrizione Oggetto 5",
            price="50",
	    category_id = 2
        )

session.add(newItem)
session.commit()

# README #

Item Catalog

### What is this repository for? ###

Item Catalog is a Python script that allows users to use a Web Item Catalog, using Facebook and Google OAuth providers for authentication and sqlite for data persistance.
All items in the catalog are organized in categories and there are various permission levels.
A public user can view all categories and items, a registered user also has rights to create items or categories and edit or delete items or categories he created (but not others')


### How do I get set up? ###

* Python (<3) is required. If you have Linux or Mac you should be good to go and you should skip to the next step, if you're on Windows get it from: http://ninite.com
* Clone the repository or simply download it as a zip file and unzip it on your pc
* Install all required components using pip (https://pip.pypa.io/en/latest/installing.html) with the following commands:
* pip install -r requirements.txt
* Launch the script with: python item-catalog.py
* Open a web browser and visit: http://localhost:8000

### API Endpoints ###

It is possible to retrieve data from the application in RSS and JSON format using the following urls:

##JSON##
* All catalog: http://localhost:8000/catalog/JSON
* Specific category: http://localhost:8000/catalog/INSERT_CATEGORY_ID/JSON
* Specific item: http://localhost:8000/catalog/INSERT_CATEGORY_ID/INSERT_ITEM_ID/JSON

##RSS##
* All catalog: http://localhost:8000/catalog/RSS
* Specific category: http://localhost:8000/catalog/INSERT_CATEGORY_ID/RSS
* Specific item: http://localhost:8000/catalog/INSERT_CATEGORY_ID/INSERT_ITEM_ID/RSS

### Contribution guidelines ###

* If you have any idea or suggestion contact directly the Repo Owner

### Who do I talk to? ###

* ltpitt: Repo Owner

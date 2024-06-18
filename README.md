# CyberChef

## Overview

This Flask application allows users to manage a virtual fridge, search for recipes, save and delete recipes, and view recommended recipes based on the ingredients in their virtual fridge. It integrates with the Spoonacular API to fetch recipe information.

## Features

- User Registration and Login
- Virtual Fridge Management
- Recipe Search using Spoonacular API
- Save and Delete Recipes
- Add Ingredients to Virtual Fridge from Search Results
- View Recommended Recipes based on Virtual Fridge Ingredients

## Technologies Used

- Flask
- Flask_SQLAlchemy
- Flask_WTF
- Requests
- Werkzeug
- PostgreSQL

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- Virtualenv (optional but recommended)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/recipe-fridge-app.git
   cd recipe-fridge-app

 2. Create and activate a virtual environment:

 python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

3. Install the dependencies:
pip install -r requirements.txt

4.Set up the PostgreSQL database and configure the database URI in wsgi.py:
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/dbname'


5.Configure your Spoonacular API key in wsgi.py:
API_KEY = 'your_spoonacular_api_key'


6.Initialize the database:
flask db init
flask db migrate -m "Initial migration."
flask db upgrade


Run the Flask application:
python wsgi.py








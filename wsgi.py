from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import requests
from urllib.parse import unquote
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


# Initialize SQLAlchemy without an app
db = SQLAlchemy()

# Define your models
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)  # Unique username
    password = db.Column(db.String(255))  # Ensure this is hashed in production
    saved_recipes = db.relationship('SavedRecipe', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)
    virtual_fridge_items = db.relationship('VirtualFridge', backref='user', lazy=True)

class SavedRecipe(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipe_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
    recipe_name = db.Column(db.String(255))
    recipe_details = db.Column(db.Text)
    image_url = db.Column(db.String(500))  # New field for image URL
    description = db.Column(db.Text)  
    comments = db.relationship('Comment', backref='saved_recipe', lazy=True)

class Comment(db.Model):
    comment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('saved_recipe.recipe_id'), nullable=False)
    comment_text = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class VirtualFridge(db.Model):
    fridge_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    quantity = db.Column(db.String(255))
    expiry_date = db.Column(db.Date)
    ingredient = db.Column(db.String(255))  
    ingredient_id = db.Column(db.Integer)

# Forms for user registration and login
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


# Spoonacular API Key
API_KEY = '15599c84fad84a0f9a160bc14e9ea4d6'

def search_recipes(query):
    url = f'https://api.spoonacular.com/recipes/complexSearch'
    params = {
        'apiKey': API_KEY,
        'query': query,
        'number': 10  # Number of results to return
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('results', [])
    else:
        return []

# Application Factory
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your secret key
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1826@localhost/spoonacular_app'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Define routes

    @app.route('/', methods=['GET'])
    def root():
        return render_template('front_page.html')
        
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            # Assuming users are identified by email, change this line to match your User model
            user = User.query.filter_by(username=form.username.data).first()
            if user and check_password_hash(user.password, form.password.data):
                session['user_id'] = user.user_id
                print("Login successful, user_id:", session['user_id'])  # Debug print
                return redirect(url_for('home'))
            else:
                print("Login failed")  # Debug print
                flash('Login Unsuccessful. Please check email and password', 'danger')
        return render_template('login.html', form=form)


    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegistrationForm()
        if form.validate_on_submit():
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Username already exists. Please choose a different one.', 'warning')
                return render_template('register.html', form=form)

            hashed_password = generate_password_hash(form.password.data)
            new_user = User(username=form.username.data, password=hashed_password)
            db.session.add(new_user)
            try:
                db.session.commit()
                return redirect(url_for('home'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred. Please try again.', 'danger')
                return render_template('register.html', form=form)

        return render_template('register.html', form=form)



    @app.route('/home', methods=['GET', 'POST'])
    def home():
        # Check if user is logged in
        if 'user_id' not in session:
            flash('Please log in to access this page', 'info')
            return redirect(url_for('login'))

        if request.method == 'POST':
            # Handle POST request when the user submits a search query
            query = request.form.get('search_query', '')
            recipes = search_recipes(query)
            return render_template('home.html', recipes=recipes, search_query=query)

        # Handle GET request
        search_query = request.args.get('search_query', '')
        recipes = search_recipes(search_query) if search_query else []
        return render_template('home.html', recipes=recipes, search_query=search_query)

    @app.route('/recipe/<int:recipe_id>')
    def view_recipe(recipe_id):
        search_query = request.args.get('search_query', '')
        url = f'https://api.spoonacular.com/recipes/{recipe_id}/information'
        params = {'apiKey': API_KEY}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            recipe = response.json()
            return render_template('view_recipe.html', recipe=recipe, search_query=search_query)
        else:
            return "Recipe not found", 404


    @app.route('/save_recipe/<int:recipe_id>', methods=['POST'])
    def save_recipe(recipe_id):
        user_id = session.get('user_id')
        if not user_id:
            # Handle not logged in user, maybe redirect to login page
            return redirect(url_for('login'))

        # Check if the recipe is already saved
        existing_recipe = SavedRecipe.query.filter_by(user_id=user_id, recipe_id=recipe_id).first()
        if existing_recipe:
            # Handle the case where the recipe is already saved
            # For example, you might want to inform the user or redirect them
            return redirect(url_for('my_profile'))  
        else:
            # Logic to save the new recipe
            new_saved_recipe = SavedRecipe(user_id=user_id, recipe_id=recipe_id)
            db.session.add(new_saved_recipe)
            db.session.commit()

            # Redirect to the user's profile or another appropriate page
            return redirect(url_for('my_profile'))

        # Optionally, add a generic return statement here for safety
        return redirect(url_for('home'))

    @app.route('/search_ingredients', methods=['POST'])
    def search_ingredients():
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))

        search_query = request.form.get('ingredient_search')
        url = f"https://api.spoonacular.com/food/ingredients/search?query={search_query}&apiKey={API_KEY}&number=10"
        response = requests.get(url)
        if response.status_code == 200:
            search_results = response.json().get('results', [])
            return render_template('my_profile.html', user=User.query.get(user_id),
                                fridge_ingredients=VirtualFridge.query.filter_by(user_id=user_id).all(),
                                search_results=search_results)
        else:
            flash('Failed to fetch ingredients.', 'danger')
            return redirect(url_for('my_profile'))


    @app.route('/add_to_fridge/<int:id>', methods=['POST'])
    def add_to_fridge(id):
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))

        quantity = request.form.get('quantity')
        url = f"https://api.spoonacular.com/food/ingredients/{id}/information?apiKey={API_KEY}"

        # Check if the ingredient already exists in the fridge
        existing_ingredient = VirtualFridge.query.filter_by(user_id=user_id, ingredient_id=id).first()
        if existing_ingredient:
            # Update quantity if ingredient already exists
            existing_ingredient.quantity = quantity  # or adjust quantity as needed
            db.session.commit()
        else:
            # Add new ingredient to fridge
            new_ingredient = VirtualFridge(user_id=user_id, ingredient_id=id, quantity=quantity)
            db.session.add(new_ingredient)
            db.session.commit()

        flash('Ingredient added to fridge.', 'success')
        return redirect(url_for('my_profile'))




    @app.route('/my-profile')
    def my_profile():
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to access this page', 'info')
            return redirect(url_for('login'))

        user = User.query.get(user_id)
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('home'))

        saved_recipes = SavedRecipe.query.filter_by(user_id=user_id).all()
        for recipe in saved_recipes:
            recipe.image_url = f"https://spoonacular.com/recipeImages/{recipe.recipe_id}-90x90.jpg"

            # Fetching the summary from Spoonacular API
            summary_url = f"https://api.spoonacular.com/recipes/{recipe.recipe_id}/summary?apiKey={API_KEY}"
            response = requests.get(summary_url)
            if response.status_code == 200:
                summary_data = response.json()
                recipe.description = summary_data.get('summary', 'No description available')

        fridge_ingredients = VirtualFridge.query.filter_by(user_id=user_id).all()
        recommended_recipes = get_recommended_recipes(fridge_ingredients)
        
        return render_template('my_profile.html', 
                            user=user,
                            saved_recipes=saved_recipes, 
                            fridge_ingredients=fridge_ingredients, 
                            recommended_recipes=recommended_recipes)

    @app.route('/delete_recipe/<int:recipe_id>', methods=['POST'])
    def delete_recipe(recipe_id):
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to delete recipes', 'info')
            return redirect(url_for('login'))

        recipe_to_delete = SavedRecipe.query.filter_by(user_id=user_id, recipe_id=recipe_id).first()
        if recipe_to_delete:
            db.session.delete(recipe_to_delete)
            db.session.commit()
            flash('Recipe deleted successfully', 'success')
        else:
            flash('Recipe not found', 'danger')

        return redirect(url_for('my_profile'))

    @app.route('/delete_ingredient/<int:ingredient_id>', methods=['POST'])
    def delete_ingredient(ingredient_id):
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to delete ingredients', 'info')
            return redirect(url_for('login'))

        ingredient_to_delete = VirtualFridge.query.filter_by(user_id=user_id, fridge_id=ingredient_id).first()
        if ingredient_to_delete:
            db.session.delete(ingredient_to_delete)
            db.session.commit()
            flash('Ingredient deleted successfully', 'success')
        else:
            flash('Ingredient not found', 'danger')

        return redirect(url_for('my_profile'))




    def get_recommended_recipes(ingredients):
        ingredient_names = ','.join([ingredient.ingredient for ingredient in ingredients])
        url = f'https://api.spoonacular.com/recipes/findByIngredients?ingredients={ingredient_names}&number=5&apiKey={API_KEY}'
        response = requests.get(url)
        if response.status_code == 200:
            recipes = response.json()
            return [{'title': recipe['title'], 'id': recipe['id'], 'image': f"https://spoonacular.com/recipeImages/{recipe['id']}-90x90.jpg"} for recipe in recipes]
        else:
            return []


    return app

# Start the application
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

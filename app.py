import os
from flask import Flask, render_template, redirect, request, url_for, session, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId 


app = Flask(__name__)
app.config["MONGO_DBNAME"] = 'cooking'

# if its on cloud9 it takes enviromental variables from there, else takes them from the config variables on heroku

if os.environ.get('C9_HOSTNAME'):
    import env
    app.config['DEBUG']=True
    URI=os.environ.get('URI')
    app.config["MONGO_URI"]=os.environ.get('MONGO_URI')
    mongo = PyMongo(app)
    app.secret_key=os.environ.get('SECRET_KEY')
else: 
    URI=os.environ.get('URI')
    app.config["MONGO_URI"]=os.environ.get('MONGO_URI')
    mongo = PyMongo(app)
    app.secret_key=os.environ.get('SECRET_KEY')
    
@app.route('/')
# home page displays all recipes
@app.route('/recipes', methods=['POST', 'GET'])
def recipes():
    # check if there is a user in session then flashes
    if 'username' in session:
        flash('You were successfully logged in')
    if request.method == 'POST':
        # need this variable set
        filter_allergen = ''
        # pulling data out as a dict
        filter_by = request.form.to_dict()
        try:
            #filter_allergen = filter_by['allergen']
            # getting allergens as a list
            filter_allergen = request.form.getlist('allergens')
            
            #removing allergens from filter_by
            del(filter_by['allergens'])
        except:
            pass
        # passing filter_by into the $and part and allergens into the $nin part and telling it its for key allergens
        recipes = mongo.db.recipes.find({'$and':[filter_by,{'allergens': {'$nin' : filter_allergen}}]}).sort("votes", -1)
        count = mongo.db.recipes.count({'$and':[filter_by,{'allergens': {'$nin' : filter_allergen}}]})
        # if no results
        if count == 0: 
            count="There are no"
        users=mongo.db.users.find()
        allergens=mongo.db.allergens.find()
        cuisine=mongo.db.cuisine.find()
        return render_template('recipes.html', 
                                recipes=recipes, 
                                users=users, 
                                allergens=allergens, 
                                cuisine=cuisine,
                                count=count)
        
    else:
        
        recipes=mongo.db.recipes.find().sort("votes", -1)
        count = mongo.db.recipes.count()
        # if no results
        if count == 0: 
            count="There are no"
        users=mongo.db.users.find()
        allergens=mongo.db.allergens.find()
        cuisine=mongo.db.cuisine.find()
        return render_template("recipes.html", 
                               recipes=recipes,
                               users=users,
                               allergens=allergens,
                               cuisine=cuisine,
                               count=count)
                               
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        users = mongo.db.users
        # finds the user in the database
        user_login = users.find_one({'name' : request.form['username']})
        if user_login:
            session['username'] = request.form['username']
            return redirect(url_for('recipes'))
        # if there is no user by that name and invalid user flash happens   
        flash("Invalid Log In")
    return render_template('login.html')
    
# logout  
@app.route('/logout')
def logout():
    # session is false, and user is logged out
    session['username'] = False
    flash("You were successfully logged out")
    return render_template('login.html') 
    
# register
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        # checks for existing user
        existing_user = users.find_one({'name' : request.form['username']})
        # if there is no existing use, registration goes ahead
        if existing_user is None:
            username = request.form["username"]
            country = request.form.get("country_name")
            users.insert_one({'name' : username, 'user_country' : country})
            session['username'] = request.form['username']
            return redirect(url_for('recipes'))
        flash("That username already exists!")
            
        
    return render_template('create_user.html',
                           countries=mongo.db.countries.find())


# create recipe
@app.route('/add_recipe', methods=['GET','POST'])
def add_recipe():
    recipes = mongo.db.recipes
    if request.method == 'POST':
        new_recipe = {'author': session['username'], 'votes': 0, 'voted': []}
        recipe_allergens = []
        recipe=request.form
        for key in recipe:
            if key in ['recipe_description','recipe_name','cuisine','recipe_instructions','recipe_image']:
                new_recipe[key]=request.form[key]
            elif key in ['5cb78b681c9d440000423101', '5cb78b841c9d440000423102', '5cb78b9c1c9d440000423103', '5cb78baa1c9d440000423104', '5cb78bb41c9d440000423105', '5cb78bbf1c9d440000423106', '5cb78bc91c9d440000423107', '5cb78bdc1c9d440000423108', '5cb78be71c9d440000423109', '5cb78bf31c9d44000042310a', '5cb78bfe1c9d44000042310b', '5cb78c081c9d44000042310c', '5cb78c141c9d44000042310d', '5cb78c211c9d44000042310e']:
                recipe_allergens.append(key)
                
            else:
                ingredients=request.form.getlist('ingredients-select')
                
        
		# Then recipe_allergens is added to the new_recipe dict
        new_recipe['allergens']=recipe_allergens
        new_recipe['ingredients']=ingredients
        
		# Then for your insert just pass in new_recipe
        recipes.insert_one(new_recipe)
        flash("Recipe successfully added")
        return redirect(url_for('recipes'))
    else:
        allergens = mongo.db.allergens.find()
        ingredients = mongo.db.ingredients.find()
        return render_template('add_recipe.html',
                                cuisine=mongo.db.cuisine.find(),
                                allergens = allergens,
                                ingredients = ingredients)
# open recipes
@app.route('/open_recipes/<recipe_id>')
def open_recipe(recipe_id):
    the_recipe =  mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    recipe_allergens = []
    recipe_ingredients = []
    for ingredient_id in the_recipe["ingredients"]:
        recipe_ingredients.append(mongo.db.ingredients.find_one({"_id": ObjectId(ingredient_id)}))
    for allergen_id in  the_recipe["allergens"]:
        recipe_allergens.append(mongo.db.allergens.find_one({"_id": ObjectId(allergen_id)}))
    the_recipe["allergens"] = recipe_allergens
    the_recipe["ingredients"] = recipe_ingredients
    return render_template('open_recipe.html', 
                            recipe=the_recipe)
    
    
# deletes the recipes
@app.route('/delete_recipe/<recipe_id>')
def delete_recipe(recipe_id):
    mongo.db.recipes.remove({'_id': ObjectId(recipe_id)})
    return redirect(url_for('recipes'))
    
#  edit recipe 
@app.route('/edit_recipe/<recipe_id>')
def edit_recipe(recipe_id):
    the_recipe =  mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    allergens = mongo.db.allergens.find()
    ingredients = mongo.db.ingredients.find()
    return render_template('edit_recipe.html', 
                            recipe=the_recipe, 
                            cuisine=mongo.db.cuisine.find(), 
                            allergens=allergens, 
                            ingredients=ingredients)
    

# update recipes
@app.route('/update_recipe/<recipe_id>', methods=["POST"])
def update_recipe(recipe_id):
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if request.method == 'POST':
		# This is going to be passed into mongo
        new_recipe = {'author': session['username'], "votes": recipe["votes"], "voted": recipe["voted"]}
        recipe_allergens = []
        recipe=request.form
        for key in recipe:
            if key in ['recipe_description','recipe_name','cuisine','recipe_instructions','recipe_image']:
                new_recipe[key]=request.form[key]
            elif key in ['5cb78b681c9d440000423101', '5cb78b841c9d440000423102', '5cb78b9c1c9d440000423103', '5cb78baa1c9d440000423104', '5cb78bb41c9d440000423105', '5cb78bbf1c9d440000423106', '5cb78bc91c9d440000423107', '5cb78bdc1c9d440000423108', '5cb78be71c9d440000423109', '5cb78bf31c9d44000042310a', '5cb78bfe1c9d44000042310b', '5cb78c081c9d44000042310c', '5cb78c141c9d44000042310d', '5cb78c211c9d44000042310e']:
                recipe_allergens.append(key)
                
            else:
                ingredients=request.form.getlist('ingredients-select')
                
    
		# Then recipe_allergens is added to the new_recipe dict
        new_recipe['allergens']=recipe_allergens
        new_recipe['ingredients']=ingredients
		# Then recipe_allergens is added to the new_recipe dict
        new_recipe['allergens']=recipe_allergens
        
        # pushes the edit to database
        mongo.db.recipes.update( {'_id': ObjectId(recipe_id)}, new_recipe)
    flash('Recipe succesfully edited')
    return redirect(url_for('recipes'))


# upvotes
@app.route('/vote/<recipe_id>', methods=['GET','POST'])
def vote(recipe_id):
    if "username" in session:
         filter = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
         voted = filter['voted']
         if not session['username'] in voted:
             voted.append(session['username'])
             mongo.db.recipes.update({"_id": ObjectId(recipe_id)}, {'$inc': {'votes': 1}})
             mongo.db.recipes.find_one_and_update({'_id': ObjectId(recipe_id)},{"$set": { "voted" : voted}}, upsert=True);
    else:
        flash(u'You need to log in to vote', 'error')
    return redirect(url_for('recipes'))


# session user page displays all their recipes
@app.route('/user/<name>')
def user_recipes(name):
    recipes =   mongo.db.recipes.find({ 'author' :  name  })
    return render_template('user_recipes.html',  
                            name=name, 
                            recipes=recipes)


if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')))
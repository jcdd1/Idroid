from flask import Flask, render_template, request, redirect, url_for, Response, session, flash
from config import Config
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
from flask_login import LoginManager, login_user, logout_user, login_required
from flask_wtf.csrf import CSRFProtect


#Modelos
from models.ModelLog import ModelLog

from models.ModelProduct import ModelProduct
# Entities

from models.entities.users import User
from models.entities.product import Products

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager_app = LoginManager(app)
csrf = CSRFProtect()
csrf.init_app(app)

@login_manager_app.user_loader
def load_user(user_id):
    return ModelLog.get_by_id(db, user_id)

@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method =='POST':
        user = User(0, "","","",request.form['username'], request.form['password'])
        logged_user =  ModelLog.login(db,user)
        
        if logged_user != None:
            login_user(logged_user)
            return redirect(url_for('menu'))
        else:
            flash("Usuario o contraseña invalida")
        #print(request.form['username'])
        return render_template("auth/login.html")
    else:
        return render_template("auth/login.html")
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/menu', methods=['GET', 'POST'])
@login_required
def menu():
    return render_template("menu.html")


@app.route('/products', methods=['GET'])
@login_required
def show_products():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    products = ModelProduct.get_products_paginated(db, per_page, offset)
    total = ModelProduct.count_products(db)
    total_pages = (total + per_page - 1) // per_page
    print(products)
    return render_template(
        'menu/products.html',
        products=products,
        page=page,
        total_pages=total_pages
    )




#Manejo de errores en el servidor
def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1> Página no encontrada</h>", 404

if __name__=='__main__':
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run(host='0.0.0.0', port = '8080')
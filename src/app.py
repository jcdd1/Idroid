from flask import Flask, render_template, request, redirect, url_for, Response, session, flash
from config import Config
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect



#Modelos
from models.ModelLog import ModelLog
from models.ModelWarehouse import ModelWarehouse
from models.ModelProduct import ModelProduct
from models.invoice_model import ModelInvoice

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


@app.route('/facturas', methods=['GET'])
@login_required
def show_invoices():
    # Parámetros de búsqueda
    document_number = request.args.get('document_number', '')  
    client_name = request.args.get('client_name', '')  
    invoice_type = request.args.get('type', '')  

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page


    # Consultar facturas
    if document_number or client_name or invoice_type:
        invoices, total = ModelInvoice.filter_invoices(
            db, document_number=document_number, client_name=client_name, invoice_type=invoice_type, limit=per_page, offset=offset
        )
    else:
        invoices = ModelInvoice.get_invoices_paginated(db, limit=per_page, offset=offset)
        total = ModelInvoice.count_invoices(db)

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'menu/invoices.html',
        invoices=invoices,
        page=page,
        total_pages=total_pages,
        document_number=document_number,
        client_name=client_name,
        invoice_type=invoice_type
    )



@app.route('/editar_factura', methods=['POST'])
@login_required
def edit_invoice():
    # Obtener el ID de la factura
    invoice_id = request.form.get('invoice_id')
    invoice = ModelInvoice.get_invoice_by_id(db, invoice_id)

    if not invoice:
        flash("Factura no encontrada.", "danger")
        return redirect(url_for('show_invoices'))

    # Actualizar los campos de la factura
    invoice.type = request.form.get('type')
    invoice.document_number = request.form.get('document_number')
    invoice.date = request.form.get('date')
    invoice.client = request.form.get('client')

    success = ModelInvoice.update_invoice(db, invoice)

    if success:
        flash("Factura actualizada correctamente.", "success")
    else:
        flash("Error al actualizar la factura.", "danger")

    return redirect(url_for('show_invoices'))





@app.route('/login', methods=['GET','POST'])
def login():



    if current_user.is_authenticated:
        return redirect(url_for('menu'))

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

@app.route('/invoices', methods=['GET', 'POST'])
@login_required
def show_invoice():
    return render_template("menu/invoices.html")


@app.route('/products', methods=['GET'])
@login_required
def show_products():
    # Parámetros de búsqueda
    imei = request.args.get('imei')  # Valor del IMEI
    productname = request.args.get('productname')  # Nombre del producto
    current_status = request.args.get('current_status')  # Estado actual

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    warehouses_name = ModelWarehouse.get_all_warehouses(db)

    # Verifica si hay filtros
    if imei or productname or current_status:
        # Aplica filtro si hay parámetros
        products, total = ModelProduct.filter_products(
            db, imei=imei, productname=productname, current_status=current_status, limit=per_page, offset=offset
        )
    else:
        # Muestra todos los productos si no hay filtros
        products = ModelProduct.get_products_paginated(db, limit=per_page, offset=offset)
        # Convierte a JSON serializable

        total = ModelProduct.count_products(db)

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'menu/products.html',
        products=products,
        page=page,
        total_pages=total_pages,
        imei=imei,
        productname=productname,
        current_status=current_status,
        warehouses_name = warehouses_name
    )


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'GET':
        # Renderiza el formulario con los almacenes cargados desde la base de datos
        warehouses = ModelWarehouse.get_all_warehouses(db)
        return render_template('menu/add_product.html', warehouses=warehouses)
    
    if request.method == 'POST':
        # Valida si los datos han sido enviados
        if not request.form:
            flash("No data submitted!", "danger")
            return redirect(url_for('menu/add_product'))

        # Obtiene los datos del formulario
        productname = request.form.get('productname')
        imei = request.form.get('imei')
        storage = request.form.get('storage', type=int)
        battery = request.form.get('battery', type=int)
        color = request.form.get('color')
        description = request.form.get('description', "")
        cost = request.form.get('cost', type=float)
        warehouse_id = request.form.get('warehouse', type=int)

        # Valida campos obligatorios
        if not (productname and imei and storage and battery and color and cost and warehouse_id):
            flash("All fields are required!", "danger")
            return redirect(url_for('add_product'))

        # Llama al modelo para agregar el producto con movimiento inicial
        success = ModelProduct.add_product_with_initial_movement(
            db, productname, imei, storage, battery, color, description, cost, warehouse_id
        )
        if success:
            flash("Product added successfully!", "success")
            return redirect(url_for('show_products'))
        else:
            flash("Error adding product. Please try again.", "danger")
            return redirect(url_for('add_product'))



#Manejo de errores en el servidor
def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1> Página no encontrada</h>", 404

if __name__=='__main__':
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run(host='0.0.0.0', port = '8080')
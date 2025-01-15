from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, Response, session, flash, jsonify
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
from models.ModelInvoice import ModelInvoice
from models.ModelMovement import ModelMovement


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

@app.route('/invoices', methods=['GET'])
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



@app.route('/edit_invoice', methods=['POST'])
@login_required
def edit_invoice():
    # Obtener el ID de la factura
    invoice_id = request.form.get('invoice_id')
    print(invoice_id)
    invoice = ModelInvoice.get_invoice_by_id(db, invoice_id)

    if not invoice:
        flash("Factura no encontrada.", "danger")
        return redirect(url_for('show_invoices'))

    # Actualizar los campos de la factura
    invoice.type = request.form.get('type')
    invoice.document_number = request.form.get('document_number')
    invoice.date = request.form.get('date')
    invoice.client = request.form.get('client')

    # Si la fecha no está en el formulario o está vacía, asigna None
    if not invoice.date:
        invoice.date = None
    else:
        # Convierte la fecha al formato datetime, si está presente
        invoice.date = datetime.strptime(invoice.date, '%Y-%m-%dT%H:%M')


    success = ModelInvoice.update_invoice(db, invoice)

    if success:
        flash("Factura actualizada correctamente.", "success")
    else:
        flash("Error al actualizar la factura.", "danger")

    return redirect(url_for('show_invoices'))


@app.route('/add_invoice', methods=['POST'])
def add_invoice():
    try:
        # Obtener datos del formulario
        invoice_type = request.form.get('type')
        document_number = request.form.get('document_number')
        date = request.form.get('date')
        client = request.form.get('client')
        status = request.form.get('status')

        # Validar datos
        if not invoice_type or not document_number or not date or not client or not status:
            flash('Todos los campos son obligatorios.', 'error')
            return redirect(url_for('invoices.show_invoices'))

        # Crear la factura utilizando el modelo
        success = ModelInvoice.create_invoice(
            db=db,
            invoice_type=invoice_type,
            document_number=document_number,
            date=date,
            client=client,
            status=status
        )

        if success:
            flash('Factura creada exitosamente.', 'success')
        else:
            flash('Error al crear la factura.', 'error')

    except Exception as e:
        print(f"Error al crear la factura: {e}")
        flash('Ocurrió un error al procesar la solicitud.', 'error')

    # Redirigir al listado de facturas
    return redirect(url_for('invoices.show_invoices'))


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

@app.route('/movements', methods=['GET'])
@login_required
def show_movements():
    # Search parameters
    movement_id = request.args.get('movement_id', '')  # Movement ID
    product_id = request.args.get('product_id', '')  # Product ID
    movement_status = request.args.get('movement_status', '')  # Movement status

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    # Query movements
    if movement_id or product_id or movement_status:
        movements, total = ModelMovement.filter_movements(
            db, movement_id=movement_id, product_id=product_id, movement_status=movement_status, limit=per_page, offset=offset
        )
    else:
        movements = ModelMovement.get_pending_movements(db, 1,limit=per_page, offset=offset)
        total = ModelMovement.count_movements(db)

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'menu/movements.html',
        movements=movements,
        page=page,
        total_pages=total_pages,
        movement_id=movement_id,
        product_id=product_id,
        movement_status=movement_status
    )

@app.route('/edit_movement', methods=['POST'])
@login_required
def edit_movement():
    # Get data from the form
    movement_id = request.form.get('movement_id')
    destination_warehouse_id = request.form.get('destination_warehouse_id')
    movement_status = request.form.get('movement_status')
    movement_description = request.form.get('movement_description')

    # Validate that the movement exists
    movement = ModelMovement.get_movement_by_id(db, movement_id)
    if not movement:
        flash("Movement not found.", "danger")
        return redirect(url_for('show_movements'))

    # Update movement
    movement.destination_warehouse_id = destination_warehouse_id
    movement.movement_status = movement_status
    movement.movement_description = movement_description

    success = ModelMovement.update_movement(db, movement)
    if success:
        flash("Movement updated successfully.", "success")
    else:
        flash("Error updating the movement.", "danger")

    return redirect(url_for('show_movements'))


@app.route('/create_movement', methods=['POST'])
def create_movement():
    try:
        # Obtener datos del formulario
        product_ids = request.form.getlist('product_ids')  # Lista de IDs de productos
        origin_warehouse_id = request.form.get('origin_warehouse_id')
        destination_warehouse_id = request.form.get('destination_warehouse_id')
        movement_description = request.form.get('movement_description')

        # Validar datos
        if not product_ids:
            flash('Debes seleccionar al menos un producto.', 'error')
            return redirect(url_for('movements.show_movements'))

        if not origin_warehouse_id or not destination_warehouse_id:
            flash('Debes especificar tanto el almacén de origen como el de destino.', 'error')
            return redirect(url_for('movements.show_movements'))

        if origin_warehouse_id == destination_warehouse_id:
            flash('El almacén de origen y destino no pueden ser iguales.', 'error')
            return redirect(url_for('movements.show_movements'))

        # Crear movimiento para cada producto seleccionado
        for product_id in product_ids:
            success = ModelMovement.create_movement(
                db=db,
                product_id=product_id,
                origin_warehouse_id=origin_warehouse_id,
                destination_warehouse_id=destination_warehouse_id,
                movement_description=movement_description
            )
            if not success:
                flash(f'Error al crear movimiento para el producto ID {product_id}.', 'error')

        # Si todo fue exitoso
        flash('Movimiento(s) creado(s) exitosamente.', 'success')
        return redirect(url_for('movements.show_movements'))

    except Exception as e:
        print(f"Error al crear el movimiento: {e}")
        flash('Error al procesar la solicitud. Inténtalo de nuevo.', 'error')
        return redirect(url_for('movements.show_movements'))

@app.route('/products', methods=['GET'])
@login_required
def show_products():
    # Parámetros de búsqueda
    imei = request.args.get('imei')  # Valor del IMEI
    productname = request.args.get('productname')  # Nombre del producto
    current_status = request.args.get('current_status')  # Estado actual
    category = request.args.get('category')
    warehouse = request.args.get('warehouse_name')

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    warehouses_name = ModelWarehouse.get_all_warehouses(db)
    print(warehouse)
    # Verifica si hay filtros
    if imei or productname or current_status or warehouse or category:
        # Aplica filtro si hay parámetros
        products, total = ModelProduct.filter_products(
            db, imei=imei, productname=productname, current_status=current_status, warehouse = warehouse, category = category,limit=per_page, offset=offset
        )
        
    else:
        # Muestra todos los productos si no hay filtros
        products = ModelProduct.get_product_full_info(db, limit=per_page, offset=offset)
        # Convierte a JSON serializable

        total = ModelProduct.count_products(db)
    
    print(products)
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


@app.route('/add_product', methods=['POST'])
def add_product():
    productname = request.form.get('productname')
    imei = request.form.get('imei')
    storage = request.form.get('storage')
    battery = request.form.get('battery')
    color = request.form.get('color')
    description = request.form.get('description')
    cost = request.form.get('cost')
    warehouse_id = request.form.get('warehouse_id')

    # Validar datos
    if not productname or not imei:
        flash('El nombre del producto e IMEI son obligatorios.', 'error')
        return redirect(url_for('show_products'))

    # Intentar añadir el producto utilizando el modelo
    success = ModelProduct.add_product_with_initial_movement(
        db=db,
        productname=productname,
        imei=imei,
        storage=storage,
        battery=battery,
        color=color,
        description=description,
        cost=cost,
        warehouse_id=warehouse_id
    )

    # Mostrar mensaje según el resultado
    if success:
        flash('Producto añadido exitosamente.', 'success')
    else:
        flash('Error al añadir el producto.', 'error')

    # Redirigir al listado de productos
    return redirect(url_for('show_products'))

@app.route('/edit_product', methods=['POST'])
@login_required
def edit_product():
    product_id = request.form['product_id']
    productname = request.form['productname']
    imei = request.form['imei']
    storage = request.form['storage']
    battery = request.form['battery']
    color = request.form['color']
    description = request.form['description']
    cost = request.form['cost']
    current_status = request.form['current_status']

    # Actualiza el producto en la base de datos
    success = ModelProduct.update_product(
        db, product_id, productname, imei, storage, battery, color, description, cost, current_status
    )

    if success:
        flash("Producto actualizado exitosamente.", "success")
    else:
        flash("Error al actualizar el producto.", "danger")

    return redirect(url_for('show_products'))

@app.route('/movements/<string:imei>', methods=['GET'])
def get_movements_by_imei(imei):
    try:
        # Supongamos que este método devuelve una lista de movimientos
        movements = ModelMovement.get_movements_by_imei(db, imei)
        # Devuelve los movimientos como JSON
        return jsonify({"movements": [movement for movement in movements]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500




#Manejo de errores en el servidor
def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1> Página no encontrada</h>", 404

if __name__=='__main__':
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run(host='0.0.0.0', port = '8080')
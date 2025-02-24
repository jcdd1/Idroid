from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, Response, session, flash, jsonify, get_flashed_messages, send_file
from config import Config
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
import pandas as pd
import math

#Código de barras
import barcode
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from PIL import Image
from reportlab.lib.utils import ImageReader

#Modelos
from models.ModelLog import ModelLog
from models.ModelWarehouse import ModelWarehouse
from models.ModelProduct import ModelProduct
from models.ModelInvoice import ModelInvoice
from models.ModelMovement import ModelMovement
from models.ModelReturn import ModelReturn


# Entities
from models.entities.users import User
from models.entities.product import Products


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager_app = LoginManager(app)
csrf = CSRFProtect()
csrf.init_app(app)

from flask import Blueprint


product_blueprint = Blueprint('product_blueprint', __name__)


@login_manager_app.user_loader
def load_user(user_id):
    return ModelLog.get_by_id(db, user_id)

@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect(url_for('login'))

@app.context_processor
def inject_user_info():
    if current_user.is_authenticated:
        return {
            "current_user_id": current_user.user_id,
            "current_warehouse_id": current_user.warehouse_id
        }
    return {}

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

@app.route('/update_units/<imei>', methods=['POST'])
def update_units(imei):
    try:
        data = request.get_json()
        amount = int(data.get('amount', 0))

        if amount == 0:
            return jsonify({'success': False, 'message': 'Cantidad inválida.'}), 400

        # Llamar al método del modelo para actualizar unidades
        response = ModelProduct.update_units(db, imei, amount)

        if response.get('success'):
            return jsonify({'success': True, 'new_units': response['new_units']})
        else:
            return jsonify({'success': False, 'message': response.get('error', 'Error desconocido.')}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/update_status/<imei>', methods=['POST'])
def update_status(imei):
    try:
        data = request.get_json()
        new_status = data.get('status')

        # Validar el estado antes de actualizar
        if new_status not in ['Under Repair', 'In Warehouse']:
            return jsonify({'success': False, 'message': 'Estado no válido.'}), 400

        # Llamada al método del modelo
        response = ModelProduct.update_status(db, imei, new_status)

        if response.get("success"):
            return jsonify({'success': True, 'message': 'Estado actualizado correctamente.'})
        else:
            return jsonify({'success': False, 'message': response.get('error', 'Error desconocido.')}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/invoicesUser', methods=['GET'])
@login_required
def show_invoicesUser():
    # Parámetros de búsqueda
    document_number = request.args.get('document_number', '')  
    client_name = request.args.get('client_name', '')  
    invoice_type = request.args.get('type', '')  
    status = request.args.get('status', '')  # Capturar el estado

    print(f"🔍 Parámetros de búsqueda -> Documento: {document_number}, Cliente: {client_name}, Tipo: {invoice_type}, Estado: {status}")

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    # Consultar facturas con filtro de estado
    if document_number or client_name or invoice_type or status:
        invoices, total = ModelInvoice.filter_invoices(
            db, document_number=document_number, client_name=client_name, invoice_type=invoice_type, status=status, limit=per_page, offset=offset
        )
    else:
        invoices = ModelInvoice.get_invoices_paginated(db, limit=per_page, offset=offset)
        total = ModelInvoice.count_invoices(db)

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'menu/invoicesUser.html',
        invoices=invoices,
        page=page,
        total_pages=total_pages,
        document_number=document_number,
        client_name=client_name,
        invoice_type=invoice_type,
        status=status
    )



@app.route('/edit_invoice', methods=['POST'])
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




@app.route('/add_invoiceUser', methods=['POST'])
def add_invoiceUser():
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
    return redirect(url_for('show_invoicesUser'))

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


from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_by_role(current_user.role)  # Redirige según el rol

    if request.method == 'POST':
        user = User(0, "", "", "", request.form['username'], request.form['password'])
        logged_user = ModelLog.login(db, user)

        if logged_user:
            login_user(logged_user)
            return redirect_by_role(logged_user.role)  # Redirige según el rol
        else:
            flash("Usuario o contraseña inválida")

    return render_template("auth/login.html")

def redirect_by_role(role):
    """Redirige a la plantilla correspondiente según el rol del usuario."""
    if role == 'usuario':
        return redirect(url_for('menuUser'))
    elif role == 'admin':
        return redirect(url_for('menuAdmin'))
    elif role == 'superAdmin':
        return redirect(url_for('menu'))
    else:
        flash("Rol desconocido, contacte con soporte.")
        return redirect(url_for('login'))  # Redirige al login en caso de error

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/menu', methods=['GET', 'POST'])
@login_required
def menu():
    return render_template("menu.html")

@app.route('/return', methods=['GET'])
@login_required
def show_returns():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    # Capturar parámetros de búsqueda
    return_id = request.args.get('return_id', '').strip()
    movement_detail_id = request.args.get('movement_detail_id', '').strip()

    print(f" Parámetros de búsqueda -> ID Devolución: {return_id}, ID Movimiento: {movement_detail_id}")

    # Consultar devoluciones con filtros
    if return_id or movement_detail_id:
        returns, total = ModelReturn.filter_returns(db, return_id=return_id, movement_detail_id=movement_detail_id, limit=per_page, offset=offset)
    else:
        returns = ModelReturn.get_returns_paginated(db, limit=per_page, offset=offset)
        total = ModelReturn.count_returns(db)

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'menu/return.html',
        returns=returns,
        page=page,
        total_pages=total_pages,
        return_id=return_id,
        movement_detail_id=movement_detail_id
    )


@app.route('/returnAdmin', methods=['GET'])
@login_required
def show_returnsAdmin():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    # Capturar parámetros de búsqueda
    return_id = request.args.get('return_id', '').strip()
    movement_detail_id = request.args.get('movement_detail_id', '').strip()

    print(f" Parámetros de búsqueda -> ID Devolución: {return_id}, ID Movimiento: {movement_detail_id}")

    # Consultar devoluciones con filtros
    if return_id or movement_detail_id:
        returns, total = ModelReturn.filter_returns(db, return_id=return_id, movement_detail_id=movement_detail_id, limit=per_page, offset=offset)
    else:
        returns = ModelReturn.get_returns_paginated(db, limit=per_page, offset=offset)
        total = ModelReturn.count_returns(db)

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'menu/returnAdmin.html',
        returns=returns,
        page=page,
        total_pages=total_pages,
        return_id=return_id,
        movement_detail_id=movement_detail_id
    )

@app.route('/menuUser', methods=['GET', 'POST'])
@login_required
def menuUser():
    return render_template("menuUser.html")


@app.route('/menuAdmin', methods=['GET', 'POST'])
@login_required
def menuAdmin():
    return render_template("menuAdmin.html")

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
@login_required
def create_movement():
    try:
        data = request.get_json()  # Obtener los datos del JSON
        product_id = data.get('product_id')
        origin_warehouse_id = data.get('origin_warehouse_id')
        destination_warehouse_id = data.get('destination_warehouse_id')
        movement_description = data.get('movement_description')

        print(f"📦 Datos recibidos -> Producto ID: {product_id}, Origen: {origin_warehouse_id}, Destino: {destination_warehouse_id}, Descripción: {movement_description}")

        if not product_id or not origin_warehouse_id or not destination_warehouse_id:
            return jsonify({"success": False, "message": "Faltan datos obligatorios."})

        if origin_warehouse_id == destination_warehouse_id:
            return jsonify({"success": False, "message": "El almacén de origen y destino no pueden ser iguales."})

        success = ModelMovement.create_movement(
            db=db,
            product_id=product_id,
            origin_warehouse_id=origin_warehouse_id,
            destination_warehouse_id=destination_warehouse_id,
            movement_description=movement_description,
            user_id = current_user.user_id
        )

        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Error al guardar el movimiento."})

    except Exception as e:
        print(f" Error al procesar la solicitud: {e}")
        return jsonify({"success": False, "message": "Error interno en el servidor."})



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
    active_invoices = ModelInvoice.get_invoices_active(db)
    
    # Verifica si hay filtros
    if imei or productname or current_status or warehouse or category:
        # Aplica filtro si hay parámetros
        products = ModelProduct.filter_products(
            db, imei=imei, productname=productname, current_status=current_status, warehouse = warehouse, category = category,limit=per_page, offset=offset
        )    
    else:
        products = ModelProduct.get_products_units(db, current_user.warehouse_id)

    total = len(products)
    
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'menu/products.html',
        products=products,
        page=page,
        total_pages=total_pages,
        current_status=current_status,
        warehouses_name = warehouses_name,
        active_invoices=active_invoices
    )

@app.route('/productsUser', methods=['GET'])
@login_required
def show_productsUser():
    # Parámetros de búsqueda
    imei = request.args.get('imei')
    productname = request.args.get('productname')
    current_status = request.args.get('current_status')
    category = request.args.get('category')
    warehouse = request.args.get('warehouse_name')

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    # Obtener los almacenes y facturas activas (solo una vez)
    warehouses = ModelWarehouse.get_all_warehouses(db)
    active_invoices = ModelInvoice.get_invoices_active(db)

    # Verificar si hay almacenes disponibles
    if not warehouses:
        print("⚠️ Advertencia: No hay almacenes disponibles en la base de datos.")

    # Obtener productos con o sin filtros
    if imei or productname or current_status or warehouse or category:
        products = ModelProduct.filter_products(
            db, imei=imei, productname=productname, current_status=current_status, 
            warehouse=warehouse, category=category, limit=per_page, offset=offset
        )
    else:
        products = ModelProduct.get_products_units(db, current_user.warehouse_id)

    # Verificar si hay productos y si contienen la bodega
    if products:
        print("🔍 Ejemplo de producto obtenido:", products[0])
    else:
        print("⚠️ No se encontraron productos.")

    total = len(products)
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'menu/productsUser.html',
        products=products,
        page=page,
        total_pages=total_pages,
        current_status=current_status,
        warehouses=warehouses,
        active_invoices=active_invoices
    )




@app.route('/productsAdmin', methods=['GET'])
@login_required
def show_productsAdmin():
    # Parámetros de búsqueda
    imei = request.args.get('imei')
    productname = request.args.get('productname')
    current_status = request.args.get('current_status')
    category = request.args.get('category')
    warehouse = request.args.get('warehouse_name')

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    # Obtener los almacenes y facturas activas (solo una vez)
    warehouses = ModelWarehouse.get_all_warehouses(db)
    active_invoices = ModelInvoice.get_invoices_active(db)

    # Verificar si hay almacenes disponibles
    if not warehouses:
        print("⚠️ Advertencia: No hay almacenes disponibles en la base de datos.")

    # Obtener productos con o sin filtros
    if imei or productname or current_status or warehouse or category:
        products = ModelProduct.filter_products(
            db, imei=imei, productname=productname, current_status=current_status, 
            warehouse=warehouse, category=category, limit=per_page, offset=offset
        )
    else:
        products = ModelProduct.get_products_units(db, current_user.warehouse_id)

    # Verificar si hay productos y si contienen la bodega
    if products:
        print("🔍 Ejemplo de producto obtenido:", products[0])
    else:
        print("⚠️ No se encontraron productos.")

    total = len(products)
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'menu/productsAdmin.html',
        products=products,
        page=page,
        total_pages=total_pages,
        current_status=current_status,
        warehouses=warehouses,
        active_invoices=active_invoices
    )

@app.route('/add_product', methods=['POST'])
def add_product():
    productname = request.form.get('add_productname')
    imei = request.form.get('add_imei')
    storage = request.form.get('add_storage')
    battery = request.form.get('add_battery')
    color = request.form.get('add_color')
    description = request.form.get('add_description')
    cost = request.form.get('add_cost')
    warehouse_id = request.form.get('add_warehouse_id')
    category = request.form.get('add_category')
    units = request.form.get('add_units')
    supplier = request.form.get('add_supplier')
    current_user = request.form.get('add_user_id')
    
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
        category=category,
        units = units,
        supplier = supplier,
        warehouse_id= warehouse_id,
        current_user = current_user
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
    product_id = request.form['edit_product_id']
    productname = request.form['edit_productname']
    imei = request.form['edit_imei']
    storage = request.form['edit_storage']
    battery = request.form['edit_battery']
    color = request.form['edit_color']
    description = request.form['edit_description']
    cost = request.form['edit_cost']
    category = request.form['edit_category']
    units = request.form['edit_units']
    supplier = request.form['edit_supplier']
    document_number = request.form['edit_invoice']
    invoice_quantity = request.form.get('edit_quantity')
    price = request.form.get('edit_price')
    current_user = request.form.get('edit_user_id')
    warehouse_id = request.form.get('edit_warehouse_id')
    # Actualiza el producto en la base de datos
    success = ModelProduct.update_product(
        db, product_id, productname, imei, storage, battery, color, description, cost,
        category, units, supplier, current_user, warehouse_id
    )

    if document_number and invoice_quantity:
        success_invoice = ModelInvoice.update_invoicedetail(db, product_id, document_number, invoice_quantity, price)
    else:
        success_invoice = False

    if success_invoice:
        flash("Factura asociada exitosamente.", "success")
    else:
        flash("No se  asoció el producto.", "danger")

    
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
    
@app.route('/generate_barcode/<code>')
def generate_barcode(code):
    try:
        # Generar código de barras con Code128
        barcode_class = barcode.get_barcode_class('code128')
        ean_barcode = barcode_class(code, writer=ImageWriter())

        product = ModelProduct.get_product_imei(
            db, imei=code
        )

        # Guardar el código de barras en BytesIO
        barcode_bytes = BytesIO()
        ean_barcode.write(barcode_bytes, options={'write_text': False})
        barcode_bytes.seek(0)

        # Convertir la imagen a RGB para evitar errores
        img = Image.open(barcode_bytes).convert("RGB")

        # Guardar en memoria en formato PNG
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        # Crear el PDF en memoria
        pdf_bytes = BytesIO()
        c = canvas.Canvas(pdf_bytes, pagesize=letter)
        c.drawString(200, 750, f"{product[0]['productname']} {product[0]['storage']}GB {product[0]['color']} {product[0]['battery']}%")
        c.drawString(250, 770, f"@idroid.com.co")
        #c.drawString(200, 750, f"Código de producto: {product[0]['imei']}")

        # ✅ Usar ImageReader para insertar la imagen sin archivos temporales
        img_reader = ImageReader(img_bytes)
        c.drawImage(img_reader, 150, 650, width=300, height=80)
        c.drawString(250, 730, f"IMEI: {product[0]['imei']}")
        c.save()
        pdf_bytes.seek(0)

        return send_file(pdf_bytes, as_attachment=True, download_name=f"{code}.pdf", mimetype="application/pdf")

    except Exception as e:
        print(f" Error: {str(e)}")  
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/carga_masiva', methods=['GET', 'POST'])
def carga_masiva():
    if request.method == 'POST':
        if 'archivo' not in request.files:
            flash('⚠️ No se seleccionó ningún archivo', 'danger')
            return redirect(url_for('show_productsUser'))

        archivo = request.files['archivo']

        if archivo.filename == '':
            flash('⚠️ Nombre de archivo vacío', 'danger')
            return redirect(url_for('show_productsUser'))

        if archivo and archivo.filename.endswith('.xlsx'):
            try:
                # Leer el archivo directamente sin guardarlo
                df = pd.read_excel(archivo)
                
                # # Insertar cada fila en la base de datos
                for _, row in df.iterrows():
                    valores = {
                        "db": db,
                        "productname": row.get('PRODUCTO'),
                        "imei": row.get('IMEI'),
                        "storage": row.get('ALMACENAMIENTO'),
                        "battery": row.get('BATERÍA'),
                        "color": row.get('COLOR'),
                        "description": row.get('DESCRIPCIÓN'),
                        "cost": row.get('COSTO'),
                        "category": row.get('CATEGORIA'),
                        "units": row.get('UNIDADES'),
                        "supplier": row.get('PROVEEDOR'),
                        "warehouse_id": current_user.warehouse_id,
                        "current_user": current_user.user_id
                    }

                    print("Valores que se pasan a add_product_with_initial_movement:", valores)
                    success = ModelProduct.add_product_with_initial_movement(
                        db=db,
                        productname=row['PRODUCTO'],
                        imei=str(row['IMEI']),
                        storage=int(row['ALMACENAMIENTO']),
                        battery= int(0) if math.isnan(float(row['BATERÍA'])) else int(float(row['BATERÍA'])),
                        color=row['COLOR'],
                        description =row['DESCRIPCIÓN'],
                        cost=row['COSTO'],
                        category=row['CATEGORIA'],
                        units = row['UNIDADES'],
                        supplier = row['PROVEEDOR'],
                        warehouse_id= current_user.warehouse_id,
                        current_user = current_user.user_id
                    )                

                flash('✅ Productos cargados exitosamente', 'success')
                return redirect(url_for('productsUser'))

            except Exception as e:
                flash('Error al cargue productos', 'danger')
                db.session.rollback()
                return redirect(url_for('show_productsUser'))

    return redirect(url_for('productsUser'))

#Manejo de errores en el servidor
def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1> Página no encontrada</h>", 404

if __name__=='__main__':
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run(host='0.0.0.0', port = '8080')


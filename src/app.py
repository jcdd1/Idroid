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
import json
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

@app.route('/pending_movements')
@login_required
def pending_movements():
    user_id = current_user.user_id 
    
    print(f"Usuario autenticado: {user_id}") 

    movements = db.session.execute(
    text("""
    SELECT m.movement_id, m.origin_warehouse_id, m.destination_warehouse_id, m.creation_date, md.product_id, 
           md.quantity, p.productname, p.imei, p.product_id
    FROM movement m
    JOIN movementdetail md ON m.movement_id = md.movement_id
    JOIN products p ON md.product_id = p.product_id
    WHERE m.handled_by_user_id = :user_id AND md.status = 'Pendiente'
    """),
    {"user_id": user_id}
    ).mappings().fetchall()  


    print(f"Movements encontrados: {movements}") 

    return render_template("menu/pending_movements.html", movements=movements)

@app.route('/approve_movement/<int:movement_id>', methods=['POST'])
@login_required
def approve_movement(movement_id):
    print(f"Recibida solicitud para aprobar movimiento ID: {movement_id}") 

    try:
        data = request.get_json()
        # Verificar si el movimiento existe antes de aprobar
        # movement = ModelMovement.get_movement_by_id(db, movement_id)
        # if not movement:
        #     return jsonify({"success": False, "message": "El movimiento no existe."}), 404
        product_id = data.get("product_id")
        
        success = ModelMovement.approve_movement(db, movement_id, product_id)

        if success:
            return jsonify({"success": True, "message": "Movimiento aprobado con éxito."}), 200
        else:
            return jsonify({"success": False, "message": "No se pudo aprobar el movimiento."}), 500

    except Exception as e:
        print(f"Error al aprobar movimiento: {str(e)}")
        return jsonify({"success": False, "message": "Error interno del servidor."}), 500



@app.route('/reject_movement/<int:movement_id>', methods=['POST'])
@login_required
def reject_movement(movement_id):
    print(f" Recibida solicitud para rechazar movimiento ID: {movement_id}")  
    data = request.get_json()
    reason = data.get("reason", "Sin motivo")

    success = ModelMovement.reject_movement(db, movement_id, reason)
    return jsonify({"success": success, "message": "Movimiento rechazado con éxito." if success else "Error al rechazar el movimiento."}), (200 if success else 500)










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


@app.route('/update_movement_status', methods=['POST'])
def update_movement_status():
    try:
        data = request.get_json()
        movement_id = data.get('movement_id')
        action = data.get('action')  # 'accept' o 'reject'
        rejection_reason = data.get('rejection_reason', None)

        if not movement_id or action not in ['accept', 'reject']:
            return jsonify({'success': False, 'message': 'Datos de entrada inválidos.'}), 400

        # Obtener el movimiento y sus detalles
        movement = db.session.execute(
            "SELECT * FROM movement WHERE movement_id = :id",
            {'id': movement_id}
        ).fetchone()

        if not movement:
            return jsonify({'success': False, 'message': 'Movimiento no encontrado.'}), 404

        movement_details = db.session.execute(
            "SELECT * FROM movementdetail WHERE movement_id = :id",
            {'id': movement_id}
        ).fetchall()

        if action == 'accept':
            # Actualizar unidades en las bodegas y el estado del movimiento
            for detail in movement_details:
                origin_warehouse_id = movement.origin_warehouse_id
                destination_warehouse_id = movement.destination_warehouse_id
                product_id = detail.product_id
                quantity = detail.quantity

                # Restar unidades de la bodega de origen
                db.session.execute("""
                    UPDATE warehousestock SET units = units - :quantity
                    WHERE warehouse_id = :warehouse_id AND product_id = :product_id
                """, {'quantity': quantity, 'warehouse_id': origin_warehouse_id, 'product_id': product_id})

                # Sumar unidades a la bodega de destino
                db.session.execute("""
                    INSERT INTO warehousestock (warehouse_id, product_id, units)
                    VALUES (:warehouse_id, :product_id, :quantity)
                    ON CONFLICT (warehouse_id, product_id)
                    DO UPDATE SET units = warehousestock.units + :quantity
                """, {'warehouse_id': destination_warehouse_id, 'product_id': product_id, 'quantity': quantity})

            # Cambiar estado del movimiento a completado
            db.session.execute("""
                UPDATE movement SET status = 'completado'
                WHERE movement_id = :id
            """, {'id': movement_id})

        else:  # Rechazar movimiento
            # Actualizar estado y motivo de rechazo
            db.session.execute("""
                UPDATE movement SET status = 'rechazado' WHERE movement_id = :id
            """, {'id': movement_id})

            if rejection_reason:
                db.session.execute("""
                    UPDATE movementdetail SET status = 'rechazado', rejection_reason = :reason
                    WHERE movement_id = :id
                """, {'reason': rejection_reason, 'id': movement_id})

        db.session.commit()
        return jsonify({'success': True, 'message': f"Movimiento {'aceptado' if action == 'accept' else 'rechazado'} correctamente."})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500





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
        print(f"📝 Formulario recibido: {request.form}") 

        # Obtener datos del formulario
        invoice_type = request.form.get('type')
        document_number = request.form.get('document_number')
        date = request.form.get('date')
        client = request.form.get('client')
        status = request.form.get('status')

        if not invoice_type or not document_number or not date or not client or not status:
            flash('Todos los campos son obligatorios.', 'error')
            return redirect(url_for('show_invoicesUser'))

        products_json = request.form.get('products')  

        if not products_json:
            flash('Debe agregar al menos un producto.', 'error')
            return redirect(url_for('show_invoicesUser'))

        products = json.loads(products_json)

        if not products:
            flash('Debe agregar al menos un producto.', 'error')
            return redirect(url_for('show_invoicesUser'))

        # **1️⃣ Crear la factura**
        invoice_id = ModelInvoice.create_invoice(
            db=db,
            invoice_type=invoice_type,
            document_number=document_number,
            date=date,
            client=client,
            status=status
        )

        if not invoice_id:
            flash('Error al crear la factura.', 'error')
            return redirect(url_for('show_invoicesUser'))

        print(f"📄 Factura creada con ID: {invoice_id}")

        # **2️⃣ Crear el movimiento de venta**
        movement_id = ModelMovement.create_movement(
            db=db,
            movement_type="sale",
            origin_warehouse_id=3,  # Cambiar si es dinámico
            destination_warehouse_id=None,
            movement_description=f"Venta asociada a la factura {invoice_id}",
            user_id=9,  # Cambiar si es dinámico
            products=products
        )

        if not movement_id:
            flash('Error al registrar el movimiento.', 'error')
            return redirect(url_for('show_invoicesUser'))

        print(f"🚀 Movimiento de venta creado con ID: {movement_id}")

        flash('Factura y movimiento de venta creados exitosamente.', 'success')

    except Exception as e:
        print(f"❌ Error al crear la factura y movimientos: {e}")
        flash('Ocurrió un error al procesar la solicitud.', 'error')

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


@app.route('/get_users_by_warehouse/<int:warehouse_id>', methods=['GET'])
def get_users_by_warehouse(warehouse_id):
    try:
        result = db.session.execute(
            text("SELECT user_id AS id, name FROM users WHERE warehouse_id = :warehouse_id"),
            {"warehouse_id": warehouse_id}
        )
        users = [{'id': row.id, 'name': row.name} for row in result]
        return jsonify({'users': users})
    except Exception as e:
        print(f" Error al obtener usuarios: {e}")
        return jsonify({'users': [], 'error': str(e)}), 500
    

from flask_login import current_user

@app.route('/get_user_warehouse', methods=['GET'])
def get_user_warehouse():
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Usuario no autenticado'}), 401

        print(f" user_id actual (current_user): {current_user.user_id}")
        print(f" Bodega vinculada: {current_user.warehouse_id}")

        return jsonify({'user_warehouse_id': current_user.warehouse_id})

    except Exception as e:
        print(f" Error al obtener la bodega del usuario: {e}")
        return jsonify({'error': str(e)}), 500




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



@app.route('/get_product_units/<string:product_id>/<int:warehouse_id>', methods=['GET'])
@login_required
def get_product_units(product_id, warehouse_id):
    try:
        available_units = ModelProduct.get_units_product(db, product_id, warehouse_id)
        return jsonify({"available_units": available_units[0]['stock_disponible']})
    except Exception as e:
        print(f"❌ Error al obtener unidades: {e}")
        return jsonify({"available_units": 0})




@app.route('/create_movement', methods=['POST'])
@login_required
def create_movement():
    try:
        if not request.is_json:
            return jsonify({"success": False, "message": "Se esperaba formato JSON"}), 400
            
        data = request.get_json()
        print(f" Datos recibidos: {data}")  # Log para depuración

        #  Obtener datos principales del movimiento
        products = data.get('products', [])
        if not products:
            products = [{
                "product_id": data.get("product_id"),  # En realidad es un IMEI
                "units_to_send": int(data.get("units_to_send"))
            }]
        
        origin_warehouse_id = data.get('origin_warehouse_id')
        destination_warehouse_id = data.get('destination_warehouse_id')
        movement_description = data.get('movement_description', '')
        destination_user_id = data.get('destination_user_id')

        print(f" Procesando movimiento: Origen: {origin_warehouse_id}, Destino: {destination_warehouse_id}, Productos: {products}")

        #  Validaciones
        if not origin_warehouse_id or not destination_warehouse_id:
            return jsonify({"success": False, "message": "Faltan datos obligatorios: origen o destino."}), 400
        
        if origin_warehouse_id == destination_warehouse_id:
            return jsonify({"success": False, "message": "El almacén de origen y destino no pueden ser iguales."}), 400
        
        if not destination_user_id:
            return jsonify({"success": False, "message": "Falta el usuario de destino."}), 400

        # Crear el movimiento en `movement`
        movement_id = db.session.execute(
            text("""
            INSERT INTO movement (
                origin_warehouse_id,
                destination_warehouse_id,
                creation_date,
                status,
                notes,
                created_by_user_id,
                handled_by_user_id,
                movement_type
            ) VALUES (
                :origin_warehouse_id,
                :destination_warehouse_id,
                NOW(),
                'Pendiente',  
                :movement_description, 
                :user_id, 
                :destination_user_id, 
                'Transferencia'
            ) RETURNING movement_id
            """),
            {
                "origin_warehouse_id": origin_warehouse_id,
                "destination_warehouse_id": destination_warehouse_id,
                "movement_description": movement_description,
                "user_id": current_user.user_id,
                "destination_user_id": destination_user_id
            }
        ).scalar()

        # Procesar cada producto y guardarlo en `movementdetail`
        for product_data in products:
            try:
                imei = product_data.get("product_id")  
                units_to_send = int(product_data.get("units_to_send", 0))

                if not imei or units_to_send <= 0:
                    return jsonify({"success": False, "message": f"Datos inválidos para el producto con IMEI {imei}."}), 400

                # Buscar el `product_id` correcto usando el IMEI
                product = db.session.execute(
                    text("""
                    SELECT product_id, units FROM products 
                    WHERE imei = :imei
                    """),
                    {"imei": imei}
                ).fetchone()

                if not product:
                    return jsonify({"success": False, "message": f"Producto con IMEI {imei} no encontrado."}), 404

                product_id = product.product_id  

                #  Insertar en `movementdetail` con estado "Pendiente"
                db.session.execute(
                    text("""
                    INSERT INTO movementdetail (
                        movement_id,
                        product_id,
                        quantity,
                        status
                    ) VALUES (
                        :movement_id,
                        :product_id,
                        :units,
                        'Pendiente'
                    )
                    """),
                    {
                        "movement_id": movement_id,
                        "product_id": product_id,
                        "units": units_to_send
                    }
                )

            except Exception as e:
                print(f" Error al procesar el producto con IMEI {imei}: {e}")
                db.session.rollback()
                return jsonify({"success": False, "message": f"Error al procesar el producto con IMEI {imei}: {e}"}), 500

        # 6️⃣ Confirmar cambios
        db.session.commit()
        print(" Movimiento(s) registrado(s) correctamente.")
        return jsonify({"success": True, "message": "Movimiento(s) registrado(s) correctamente."})

    except Exception as e:
        db.session.rollback()
        print(f" Error al procesar la solicitud: {str(e)}")
        return jsonify({"success": False, "message": f"Error interno en el servidor: {str(e)}"}), 500





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
        products = ModelProduct.get_products_units_ws(db, current_user.warehouse_id)

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


@app.route('/get_all_warehouses', methods=['GET'])
def get_all_warehouses():
    try:
        result = db.session.execute(
            text("SELECT warehouse_id, warehouse_name FROM warehouses")
        ).fetchall()

        print(f" Bodegas encontradas: {result}")  

        warehouses = [{'warehouse_id': row.warehouse_id, 'warehouse_name': row.warehouse_name} for row in result]
        return jsonify({'warehouses': warehouses})

    except Exception as e:
        print(f" Error al obtener las bodegas: {e}")
        return jsonify({'error': str(e)}), 500



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
        products = ModelProduct.get_products_units_ws(db, current_user.warehouse_id)

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





@app.route('/get_product_by_imei/<imei>', methods=['GET'])
@login_required
def get_product_by_imei(imei):
    try:
        product = ModelProduct.get_product_imei(db, imei)
        if product:
            product = product[0]
            return jsonify(
                success=True, 
                product=product, 
                current_user_warehouse_id=current_user.warehouse_id
            )
        else:
            return jsonify(success=False, message="Producto no encontrado.")
    except Exception as e:
        return jsonify(success=False, message=str(e))



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
        products = ModelProduct.get_products_units_ws(db, current_user.warehouse_id)

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

@app.route('/carga_masiva', methods=['POST'])
def carga_masiva():
    if 'archivo' not in request.files:
        return jsonify({"error": "⚠️ No se seleccionó ningún archivo"}), 400

    archivo = request.files['archivo']

    if archivo.filename == '':
        return jsonify({"error": "⚠️ Nombre de archivo vacío"}), 400

    if archivo and archivo.filename.endswith('.xlsx'):
        try:
            df = pd.read_excel(archivo)
            
            for _, row in df.iterrows():
                success = ModelProduct.add_product_with_initial_movement(
                    db=db,
                    productname=row['PRODUCTO'],
                    imei=str(row['IMEI']),
                    storage=int(row['ALMACENAMIENTO']),
                    battery=int(row['BATERIA']),
                    color=row['COLOR'],
                    description=row['DESCRIPCION'],
                    cost=row['COSTO'],
                    category=row['CATEGORIA'],
                    units=row['UNIDADES'],
                    supplier=row['PROVEEDOR'],
                    warehouse_id=current_user.warehouse_id,
                    current_user=current_user.user_id
                )                

            return jsonify({"message": "✅ Productos cargados exitosamente"}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"❌ Error al cargar productos: {str(e)}"}), 500

    return jsonify({"error": "❌ Formato de archivo no permitido"}), 400

#Manejo de errores en el servidor
def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1> Página no encontrada</h>", 404

if __name__=='__main__':
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run(host='0.0.0.0', port = '8080')


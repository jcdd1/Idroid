from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, Response, session, flash, jsonify, get_flashed_messages, send_file
from config import Config
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
import pandas as pd
import json
import math
from io import BytesIO
from openpyxl import Workbook
from xlsxwriter import Workbook
import os
from flask import send_file


#Código de barras
import barcode
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from PIL import Image
from reportlab.lib.utils import ImageReader
from num2words import num2words
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
import os

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


@app.route('/users', methods=['GET'])
@login_required
def show_users():
    try:
        # Obtener los usuarios con la bodega asociada
        users = db.session.execute(text("""
            SELECT u.user_id, u.name, u.role, u.username, w.warehouse_name, u.warehouse_id
            FROM users u
            LEFT JOIN warehouses w ON u.warehouse_id = w.warehouse_id
        """)).mappings().all()

        users_list = [dict(user) for user in users]

        # Obtener todas las bodegas disponibles
        warehouses = db.session.execute(text("""
            SELECT warehouse_id AS id, warehouse_name AS name FROM warehouses
        """)).mappings().all()


        warehouses_list = [dict(warehouse) for warehouse in warehouses]

        return render_template("menu/users.html", users=users_list, warehouses=warehouses_list)

    except Exception as e:
        flash(f"❌ Error al obtener los datos: {e}", "error")
        return redirect(url_for('dashboard'))



@app.route('/edit_user', methods=['POST'])
@login_required
def edit_user():
    try:
        user_id = request.form.get('user_id')
        name = request.form.get('name')
        role = request.form.get('role')
        warehouse_id = request.form.get('warehouse_id')
        username = request.form.get('username')

        db.session.execute(text("""
            UPDATE users
            SET name = :name, role = :role, warehouse_id = :warehouse_id, username = :username
            WHERE user_id = :user_id
        """), {
            "user_id": user_id,
            "name": name,
            "role": role,
            "warehouse_id": warehouse_id,
            "username": username
        })

        db.session.commit()
        flash("Usuario actualizado con éxito", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar usuario: {e}", "error")

    return redirect(url_for("show_users"))




@app.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            role = request.form.get('role')
            warehouse_id = request.form.get('warehouse_id')
            username = request.form.get('username')
            password = request.form.get('userpassword')  # Contraseña ingresada por el usuario

            # Insertar usuario con la contraseña encriptada con bcrypt
            db.session.execute(text("""
                INSERT INTO users (name, role, warehouse_id, username, userpassword)
                VALUES (:name, :role, :warehouse_id, :username, crypt(:password, gen_salt('bf')))
            """), {"name": name, "role": role, "warehouse_id": warehouse_id, "username": username, "password": password})

            db.session.commit()
            flash("✅ Usuario creado con éxito", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error: {e}", "error")

        return redirect(url_for("show_users"))

    # 🔹 Obtener las bodegas disponibles para el desplegable
    warehouses = db.session.execute(text("SELECT warehouse_id, warehouse_name FROM warehouses")).fetchall()
    warehouses_list = [{"id": w.warehouse_id, "name": w.warehouse_name} for w in warehouses]

    return render_template("menu/create_user.html", warehouses=warehouses_list)




@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    try:
        # Verificar si el usuario existe
        user = db.session.execute(text("SELECT * FROM users WHERE user_id = :user_id"), {"user_id": user_id}).fetchone()
        if not user:
            return jsonify({"success": False, "message": "Usuario no encontrado"}), 404

        # Ejecutar la eliminación
        db.session.execute(text("DELETE FROM users WHERE user_id = :user_id"), {"user_id": user_id})
        db.session.commit()

        return jsonify({"success": True, "message": "Usuario eliminado correctamente"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@app.route('/pending_movementsSuperAd')
@login_required
def pending_movementsSuperAd():
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

    return render_template("menu/pending_movementsSuperAd.html", movements=movements)





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


@app.route('/pending_movements_Admin')
@login_required
def pending_movements_Admin():
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

    return render_template("menu/pending_movements_Admin.html", movements=movements)




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
    


@app.route('/check_document_exists/<document_number>', methods=['GET'])
def check_document_exists(document_number):
    # Verificar si el número de documento ya existe usando la función estática
    document_exists = ModelInvoice.check_document_exists(db, document_number)

    if document_exists:
        return jsonify({"exists": True}), 200
    else:
        return jsonify({"exists": False}), 200



@app.route('/reject_movement/<int:movement_id>', methods=['POST'])
@login_required
def reject_movement(movement_id):
    print(f"Recibida solicitud para rechazar movimiento ID: {movement_id}")
    
    try:
        data = request.get_json()
        print(f"Datos recibidos: {data}")  # Imprime los datos completos para verificar lo que llega
        
        product_id = data.get("product_id")
        reason = data.get("reason", "Sin motivo")
        
        print(f"Producto ID recibido: {product_id}")  # Verifica que el product_id se esté recibiendo correctamente
        
        success = ModelMovement.reject_movement(db, movement_id, product_id, reason)
        
        if success:
            return jsonify({"success": True, "message": "Movimiento rechazado con éxito."}), 200
        else:
            return jsonify({"success": False, "message": "No se pudo rechazar el movimiento."}), 500

    except Exception as e:
        print(f"Error al rechazar movimiento: {str(e)}")
        return jsonify({"success": False, "message": "Error interno del servidor."}), 500




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
        warehouse_id = data.get('warehouse_id')  
        if not warehouse_id:
            return jsonify({'success': False, 'message': 'El ID de la bodega es requerido.'}), 400

        if amount == 0:
            return jsonify({'success': False, 'message': 'Cantidad inválida.'}), 400

        # Llamar al método del modelo para actualizar unidades
        response = ModelProduct.update_units(db, imei, amount, warehouse_id)

        if response.get('success'):
            return jsonify({'success': True, 'new_units': response['new_units'], 'new_units': response['new_units']})
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
    

@app.route('/get_invoice_details/<int:invoice_id>', methods=['GET'])
@login_required
def get_invoice_details(invoice_id):
    try:
        details = db.session.execute(
            text("""
                SELECT p.imei, p.productname, id.quantity, id.price
                FROM invoicedetail id
                JOIN products p ON id.product_id = p.product_id
                WHERE id.invoice_id = :invoice_id
            """),
            {"invoice_id": invoice_id}
        ).mappings().fetchall()

        print(f"Detalles obtenidos para factura {invoice_id}: {details}")  # Depuración en consola

        if not details:
            return jsonify({"message": f"La factura {invoice_id} no tiene productos asociados."}), 200

        # Devuelve los productos asociados a la factura
        return jsonify([
            {
                "imei": row["imei"],
                "product_name": row["productname"], 
                "quantity": row["quantity"], 
                "price": float(row["price"]) 
            }
            for row in details
        ])

    except Exception as e:
        print(f"Error al obtener detalles de la factura {invoice_id}: {str(e)}")
        return jsonify({"error": "Error en el servidor"}), 500






# Ruta para obtener los datos de la factura para editar
@app.route('/get_invoice_for_edit/<int:invoice_id>', methods=['GET'])
@login_required
def get_invoice_for_edit(invoice_id):
    try:
        invoice = ModelInvoice.get_invoice_by_id(db, invoice_id)

        if not invoice:
            return jsonify({"error": "Factura no encontrada"}), 404
        
        # Obtener los productos asociados a la factura
        products = ModelInvoice.get_productos_by_factura(db, invoice_id)

        # Asegúrate de que el cliente está siendo obtenido correctamente
        print(f"Cliente de la factura {invoice_id}: {invoice.client}")

        invoice_data = {
            'invoice_id': invoice.invoice_id,
            'type': invoice.type,
            'document_number': invoice.document_number,
            'date': invoice.date.strftime('%Y-%m-%dT%H:%M'),
            'status': invoice.status,
            'client': invoice.client,  # Asegúrate de que este valor esté correcto
            'products': products
        }

        return jsonify(invoice_data)

    except Exception as e:
        print(f"Error al obtener la factura {invoice_id}: {str(e)}")
        return jsonify({"error": "Error en el servidor"}), 500

@app.route('/edit_invoice', methods=['POST'])
def edit_invoice():
    try:
        print(f"📝 Datos del formulario de edición: {request.form}")
        invoice_id = request.form.get('invoice_id')
        status = request.form.get('status')
        products_json = request.form.get('products')
        products = json.loads(products_json) if products_json else []

        with db.session.begin():  # Inicio de la transacción

            # 1️⃣ Actualizar el estado de la factura
            db.session.execute(
                text("UPDATE invoices SET status = :status WHERE invoice_id = :invoice_id"),
                {"status": status, "invoice_id": invoice_id}
            )

            # 2️⃣ Obtener productos actuales en la factura
            current_products = db.session.execute(
                text("""
                    SELECT p.imei, idetail.quantity 
                    FROM invoicedetail idetail 
                    JOIN products p ON idetail.product_id = p.product_id 
                    WHERE idetail.invoice_id = :invoice_id
                """),
                {"invoice_id": invoice_id}
            ).fetchall()
            current_products_dict = {row.imei: row.quantity for row in current_products}

            new_imeis = [product["imei"] for product in products]
            current_imeis = list(current_products_dict.keys())

            # 3️⃣ Procesar productos eliminados (devolver stock y crear movimiento reverso)
            deleted_imeis = list(set(current_imeis) - set(new_imeis))
            for imei in deleted_imeis:
                product_id = db.session.execute(
                    text("SELECT product_id FROM products WHERE imei = :imei"),
                    {"imei": imei}
                ).scalar()
                deleted_quantity = current_products_dict[imei]

                # Eliminar del invoicedetail
                db.session.execute(
                    text("DELETE FROM invoicedetail WHERE invoice_id = :invoice_id AND product_id = :product_id"),
                    {"invoice_id": invoice_id, "product_id": product_id}
                )

                # Registrar movimiento de reverso (el movimiento se encarga de devolver stock)
                movement_description = f"Reverso por eliminación de producto IMEI {imei} en edición de factura {invoice_id}"
                movement_id = ModelMovement.create_movement(
                    db=db,
                    movement_type="reverso",
                    origin_warehouse_id=current_user.warehouse_id,
                    destination_warehouse_id=None,
                    movement_description=movement_description,
                    user_id=current_user.user_id,
                    products=[{"imei": imei, "quantity": deleted_quantity}]
                )
                print(f"🔄 Movimiento de reverso creado ID: {movement_id}")

            # 4️⃣ Procesar productos nuevos o actualizados
            for product in products:
                imei = product["imei"]
                quantity = int(product["quantity"])
                price = float(product["price"])

                result = db.session.execute(
                    text("SELECT product_id FROM products WHERE imei = :imei"),
                    {"imei": imei}
                ).fetchone()
                if not result:
                    continue
                product_id = result[0]

                exists = db.session.execute(
                    text("""SELECT 1 FROM invoicedetail 
                            WHERE invoice_id = :invoice_id AND product_id = :product_id"""),
                    {"invoice_id": invoice_id, "product_id": product_id}
                ).fetchone()

                if exists:
                    # Si el producto ya está en la factura, actualizar solo el precio
                    db.session.execute(
                        text("""UPDATE invoicedetail 
                                SET price = :price 
                                WHERE invoice_id = :invoice_id AND product_id = :product_id"""),
                        {"price": price, "invoice_id": invoice_id, "product_id": product_id}
                    )
                else:
                    # Insertar producto nuevo en invoicedetail
                    db.session.execute(
                        text("""INSERT INTO invoicedetail (invoice_id, product_id, quantity, price) 
                                VALUES (:invoice_id, :product_id, :quantity, :price)"""),
                        {"invoice_id": invoice_id, "product_id": product_id, "quantity": quantity, "price": price}
                    )
                    # Registrar movimiento de venta (el movimiento se encarga de disminuir el stock)
                    movement_description = f"Venta asociada a edición de factura {invoice_id} (producto nuevo agregado)"
                    movement_id = ModelMovement.create_movement(
                        db=db,
                        movement_type="sale",
                        origin_warehouse_id=current_user.warehouse_id,
                        destination_warehouse_id=None,
                        movement_description=movement_description,
                        user_id=current_user.user_id,
                        products=[{"imei": imei, "quantity": quantity}]
                    )
                    print(f"🚀 Movimiento de venta creado ID: {movement_id}")

        flash('Factura y movimientos actualizados correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al actualizar la factura: {e}")
        flash('Ocurrió un error al actualizar la factura.', 'error')
    return redirect(url_for('show_invoices'))


@app.route('/edit_invoiceAdmin', methods=['POST'])
def edit_invoiceAdmin():
    try:
        print(f"📝 Datos del formulario de edición: {request.form}")
        invoice_id = request.form.get('invoice_id')
        status = request.form.get('status')
        products_json = request.form.get('products')
        products = json.loads(products_json) if products_json else []

        with db.session.begin():  # Inicio de la transacción

            # 1️⃣ Actualizar el estado de la factura
            db.session.execute(
                text("UPDATE invoices SET status = :status WHERE invoice_id = :invoice_id"),
                {"status": status, "invoice_id": invoice_id}
            )

            # 2️⃣ Obtener productos actuales en la factura
            current_products = db.session.execute(
                text("""
                    SELECT p.imei, idetail.quantity 
                    FROM invoicedetail idetail 
                    JOIN products p ON idetail.product_id = p.product_id 
                    WHERE idetail.invoice_id = :invoice_id
                """),
                {"invoice_id": invoice_id}
            ).fetchall()
            current_products_dict = {row.imei: row.quantity for row in current_products}

            new_imeis = [product["imei"] for product in products]
            current_imeis = list(current_products_dict.keys())

            # 3️⃣ Procesar productos eliminados (devolver stock y crear movimiento reverso)
            deleted_imeis = list(set(current_imeis) - set(new_imeis))
            for imei in deleted_imeis:
                product_id = db.session.execute(
                    text("SELECT product_id FROM products WHERE imei = :imei"),
                    {"imei": imei}
                ).scalar()
                deleted_quantity = current_products_dict[imei]

                # Eliminar del invoicedetail
                db.session.execute(
                    text("DELETE FROM invoicedetail WHERE invoice_id = :invoice_id AND product_id = :product_id"),
                    {"invoice_id": invoice_id, "product_id": product_id}
                )

                # Registrar movimiento de reverso (el movimiento se encarga de devolver stock)
                movement_description = f"Reverso por eliminación de producto IMEI {imei} en edición de factura {invoice_id}"
                movement_id = ModelMovement.create_movement(
                    db=db,
                    movement_type="reverso",
                    origin_warehouse_id=current_user.warehouse_id,
                    destination_warehouse_id=None,
                    movement_description=movement_description,
                    user_id=current_user.user_id,
                    products=[{"imei": imei, "quantity": deleted_quantity}]
                )
                print(f"🔄 Movimiento de reverso creado ID: {movement_id}")

            # 4️⃣ Procesar productos nuevos o actualizados
            for product in products:
                imei = product["imei"]
                quantity = int(product["quantity"])
                price = float(product["price"])

                result = db.session.execute(
                    text("SELECT product_id FROM products WHERE imei = :imei"),
                    {"imei": imei}
                ).fetchone()
                if not result:
                    continue
                product_id = result[0]

                exists = db.session.execute(
                    text("""SELECT 1 FROM invoicedetail 
                            WHERE invoice_id = :invoice_id AND product_id = :product_id"""),
                    {"invoice_id": invoice_id, "product_id": product_id}
                ).fetchone()

                if exists:
                    # Si el producto ya está en la factura, actualizar solo el precio
                    db.session.execute(
                        text("""UPDATE invoicedetail 
                                SET price = :price 
                                WHERE invoice_id = :invoice_id AND product_id = :product_id"""),
                        {"price": price, "invoice_id": invoice_id, "product_id": product_id}
                    )
                else:
                    # Insertar producto nuevo en invoicedetail
                    db.session.execute(
                        text("""INSERT INTO invoicedetail (invoice_id, product_id, quantity, price) 
                                VALUES (:invoice_id, :product_id, :quantity, :price)"""),
                        {"invoice_id": invoice_id, "product_id": product_id, "quantity": quantity, "price": price}
                    )
                    # Registrar movimiento de venta (el movimiento se encarga de disminuir el stock)
                    movement_description = f"Venta asociada a edición de factura {invoice_id} (producto nuevo agregado)"
                    movement_id = ModelMovement.create_movement(
                        db=db,
                        movement_type="sale",
                        origin_warehouse_id=current_user.warehouse_id,
                        destination_warehouse_id=None,
                        movement_description=movement_description,
                        user_id=current_user.user_id,
                        products=[{"imei": imei, "quantity": quantity}]
                    )
                    print(f"🚀 Movimiento de venta creado ID: {movement_id}")

        flash('Factura y movimientos actualizados correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al actualizar la factura: {e}")
        flash('Ocurrió un error al actualizar la factura.', 'error')
    return redirect(url_for('show_invoicesAdmin'))





    
    
@app.route('/get_invoice_data/<int:invoice_id>')
def get_invoice_data(invoice_id):
    try:
        # Obtener el estado de la factura
        invoice = db.session.execute(
            text("SELECT status FROM invoices WHERE invoice_id = :invoice_id"),
            {"invoice_id": invoice_id}
        ).fetchone()

        if not invoice:
            return jsonify({"error": "Factura no encontrada"})

        # CORREGIDA: usar productname AS name
        products = db.session.execute(
            text("""
                SELECT p.imei, p.productname AS name, p.storage, p.battery, p.color, idetail.quantity, idetail.price
                FROM invoicedetail idetail
                JOIN products p ON idetail.product_id = p.product_id
                WHERE idetail.invoice_id = :invoice_id
            """),
            {"invoice_id": invoice_id}
        ).fetchall()

        product_list = []
        for row in products:
            product_list.append({
                "imei": row.imei,
                "name": row.name,  # Aquí sí debe quedar "name" porque lo pusiste en el AS
                "storage": row.storage,
                "battery": row.battery,
                "color": row.color,
                "quantity": row.quantity,
                "price": row.price
            })

        return jsonify({
            "status": invoice.status,
            "products": product_list
        })
    except Exception as e:
        print(f"❌ Error al obtener los datos de la factura: {e}")
        return jsonify({"error": "Error interno del servidor"})








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
        invoices = ModelInvoice.get_invoices_paginated(db)
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


@app.route('/invoices', methods=['GET'])
@login_required
def show_invoices():
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
        invoices = ModelInvoice.get_invoices_paginated(db)
        total = ModelInvoice.count_invoices(db)

    total_pages = (total + per_page - 1) // per_page
    print(f"📊 Total de facturas: {total}, Total de páginas: {total_pages}, Página actual: {page}")
    invoices_dict = [inv.to_dict() for inv in invoices]
    return render_template(
        'menu/invoices.html',
        invoices=invoices_dict,
        page=page,
        total_pages=total_pages,
        document_number=document_number,
        client_name=client_name,
        invoice_type=invoice_type,
        status=status
    )


@app.route('/invoicesAdmin', methods=['GET'])
@login_required
def show_invoicesAdmin():
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
        invoices = ModelInvoice.get_invoices_paginated(db)
        total = ModelInvoice.count_invoices(db)

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'menu/invoicesAdmin.html',
        invoices=invoices,
        page=page,
        total_pages=total_pages,
        document_number=document_number,
        client_name=client_name,
        invoice_type=invoice_type,
        status=status
    )








# 📌 Ruta para mostrar todas las bodegas
@app.route('/warehouses', methods=['GET'])
def show_warehouses():
    warehouses = db.session.execute(text("SELECT * FROM warehouses")).mappings().all()
    
    # Convertir a lista de diccionarios
    warehouses_list = [dict(warehouse) for warehouse in warehouses]

    # 🔍 Ver en consola qué datos está trayendo
    print("📊 Datos de bodegas:", warehouses_list)

    return render_template("menu/warehouses.html", warehouses=warehouses_list)


# 📌 Ruta para crear una nueva bodega
@app.route('/create_warehouse', methods=['POST'])
def create_warehouse():
    try:
        data = request.form
        warehouse_name = data.get('warehouse_name')
        address = data.get('address')
        phone = data.get('phone')

        print(f"📥 Datos recibidos: {warehouse_name}, {address}, {phone}")

        if not warehouse_name or not address or not phone:
            flash("⚠️ Todos los campos son obligatorios", "danger")
            return redirect(url_for('show_warehouses'))

        # ⚠️ NO incluir warehouse_id en el INSERT
        query = text("INSERT INTO warehouses (warehouse_name, address, phone) VALUES (:warehouse_name, :address, :phone)")
        db.session.execute(query, {"warehouse_name": warehouse_name, "address": address, "phone": phone})
        db.session.commit()

        flash("✅ Bodega creada correctamente.", "success")
        return redirect(url_for('show_warehouses'))

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al crear bodega: {str(e)}")
        flash(f"❌ Error al crear bodega: {str(e)}", "danger")
        return redirect(url_for('show_warehouses'))

# 📌 Ruta para editar una bodega
@app.route('/edit_warehouse', methods=['POST'])
def edit_warehouse():
    try:
        warehouse_id = request.form.get('warehouse_id')
        warehouse_name = request.form.get('warehouse_name')
        address = request.form.get('address')
        phone = request.form.get('phone')

        if not warehouse_id or not warehouse_name or not address or not phone:
            flash("⚠️ Todos los campos son obligatorios.", "danger")
            return redirect(url_for('show_warehouses'))

        # ⚠️ Asegurar que los nombres de columnas coincidan con la base de datos
        query = text("UPDATE warehouses SET warehouse_name = :warehouse_name, address = :address, phone = :phone WHERE warehouse_id = :warehouse_id")
        db.session.execute(query, {"warehouse_name": warehouse_name, "address": address, "phone": phone, "warehouse_id": warehouse_id})
        db.session.commit()

        flash("✅ Bodega editada correctamente.", "success")
        return redirect(url_for('show_warehouses'))

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al editar bodega: {str(e)}")
        flash(f"❌ Error al editar bodega: {str(e)}", "danger")
        return redirect(url_for('show_warehouses'))



@app.route('/add_invoiceUser', methods=['POST'])
def add_invoiceUser():
    try:
        print(f"📝 Formulario recibido: {request.form}") 

        invoice_type = request.form.get('type')
        document_number = request.form.get('document_number')
        date = request.form.get('date')
        client = request.form.get('client')
        status = request.form.get('status')

        if not all([invoice_type, document_number, date, client, status]):
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

        
        with db.session.begin():  # Garantiza que todas las operaciones sean atómicas
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
                db.session.rollback()
                return redirect(url_for('show_invoicesUser'))

            print(f"📄 Factura creada con ID: {invoice_id}")

            # **2️⃣ Insertar detalles de factura**
            success = ModelInvoice.create_invoice_detail(db, invoice_id, products)
            if not success:
                flash('Error al registrar los productos en la factura.', 'error')
                db.session.rollback()
                return redirect(url_for('show_invoicesUser'))

            print(f"📑 Detalles de factura registrados para Invoice ID: {invoice_id}")



            # **3️⃣ Crear el movimiento de venta**
            movement_id = ModelMovement.create_movement(
                db=db,
                movement_type="sale",
                origin_warehouse_id= current_user.warehouse_id,  
                destination_warehouse_id=None,
                movement_description=f"Venta asociada a la factura {document_number}",
                user_id= current_user.user_id,  
                products=products
            )

            if not movement_id:
                flash('Error al registrar el movimiento.', 'error')
                db.session.rollback()
                return redirect(url_for('show_invoicesUser'))

            print(f"🚀 Movimiento de venta creado con ID: {movement_id}")

            flash('Factura y movimiento de venta creados exitosamente.', 'success')

    except Exception as e:
        db.session.rollback()  # Revertir cualquier cambio en caso de error
        print(f"❌ Error al crear la factura y movimientos: {e}")
        flash('Ocurrió un error al procesar la solicitud.', 'error')

    return redirect(url_for('show_invoicesUser'))


@app.route('/add_invoiceAdmin', methods=['POST'])
def add_invoiceAdmin():
    try:
        print(f"📝 Formulario recibido: {request.form}") 

        invoice_type = request.form.get('type')
        document_number = request.form.get('document_number')
        date = request.form.get('date')
        client = request.form.get('client')
        status = request.form.get('status')

        if not all([invoice_type, document_number, date, client, status]):
            flash('Todos los campos son obligatorios.', 'error')
            return redirect(url_for('show_invoicesAdmin'))

        products_json = request.form.get('products')  
        if not products_json:
            flash('Debe agregar al menos un producto.', 'error')
            return redirect(url_for('show_invoicesAdmin'))

        products = json.loads(products_json)

        if not products:
            flash('Debe agregar al menos un producto.', 'error')
            return redirect(url_for('show_invoicesAdmin'))

        
        with db.session.begin():  # Garantiza que todas las operaciones sean atómicas
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
                db.session.rollback()
                return redirect(url_for('show_invoicesAdmin'))

            print(f"📄 Factura creada con ID: {invoice_id}")

            # **2️⃣ Insertar detalles de factura**
            success = ModelInvoice.create_invoice_detail(db, invoice_id, products)
            if not success:
                flash('Error al registrar los productos en la factura.', 'error')
                db.session.rollback()
                return redirect(url_for('show_invoicesAdmin'))

            print(f"📑 Detalles de factura registrados para Invoice ID: {invoice_id}")



            # **3️⃣ Crear el movimiento de venta**
            movement_id = ModelMovement.create_movement(
                db=db,
                movement_type="sale",
                origin_warehouse_id= current_user.warehouse_id,  
                destination_warehouse_id=None,
                movement_description=f"Venta asociada a la factura {document_number}",
                user_id= current_user.user_id,  
                products=products
            )

            if not movement_id:
                flash('Error al registrar el movimiento.', 'error')
                db.session.rollback()
                return redirect(url_for('show_invoicesAdmin'))

            print(f"🚀 Movimiento de venta creado con ID: {movement_id}")

            flash('Factura y movimiento de venta creados exitosamente.', 'success')

    except Exception as e:
        db.session.rollback()  # Revertir cualquier cambio en caso de error
        print(f"❌ Error al crear la factura y movimientos: {e}")
        flash('Ocurrió un error al procesar la solicitud.', 'error')

    return redirect(url_for('show_invoicesAdmin'))




@app.route('/add_invoice', methods=['POST'])
def add_invoice():
    try:
        print(f"📝 Formulario recibido: {request.form}") 

        invoice_type = request.form.get('type')
        document_number = request.form.get('document_number')
        date = request.form.get('date')
        client = request.form.get('client')
        status = request.form.get('status')

        if not all([invoice_type, document_number, date, client, status]):
            flash('Todos los campos son obligatorios.', 'error')
            return redirect(url_for('show_invoices'))

        products_json = request.form.get('products')  
        if not products_json:
            flash('Debe agregar al menos un producto.', 'error')
            return redirect(url_for('show_invoices'))

        products = json.loads(products_json)

        if not products:
            flash('Debe agregar al menos un producto.', 'error')
            return redirect(url_for('show_invoices'))

        
        with db.session.begin():  # Garantiza que todas las operaciones sean atómicas
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
                db.session.rollback()
                return redirect(url_for('show_invoices'))

            print(f"📄 Factura creada con ID: {invoice_id}")

            # **2️⃣ Insertar detalles de factura**
            success = ModelInvoice.create_invoice_detail(db, invoice_id, products)
            if not success:
                flash('Error al registrar los productos en la factura.', 'error')
                db.session.rollback()
                return redirect(url_for('show_invoicesAdmin'))

            print(f"📑 Detalles de factura registrados para Invoice ID: {invoice_id}")



            # **3️⃣ Crear el movimiento de venta**
            movement_id = ModelMovement.create_movement(
                db=db,
                movement_type="sale",
                origin_warehouse_id= current_user.warehouse_id,  
                destination_warehouse_id=None,
                movement_description=f"Venta asociada a la factura {document_number}",
                user_id= current_user.user_id,  
                products=products
            )

            if not movement_id:
                flash('Error al registrar el movimiento.', 'error')
                db.session.rollback()
                return redirect(url_for('show_invoicesAdmin'))

            print(f"🚀 Movimiento de venta creado con ID: {movement_id}")

            flash('Factura y movimiento de venta creados exitosamente.', 'success')

    except Exception as e:
        db.session.rollback()  # Revertir cualquier cambio en caso de error
        print(f"❌ Error al crear la factura y movimientos: {e}")
        flash('Ocurrió un error al procesar la solicitud.', 'error')

    return redirect(url_for('show_invoices'))




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



@app.route('/returnSuperAd', methods=['GET'])
@login_required
def show_returnSuperAd():
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
        'menu/returnSuperAd.html',
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
        # Llamamos a la función que obtiene las unidades
        available_units = ModelProduct.get_units_product(db, product_id, warehouse_id)

        # Verificamos si la consulta devolvió resultados
        if available_units:
            # Retornamos la primera fila de la consulta con 'stock_disponible'
            return jsonify({"available_units": available_units[0].get('stock_disponible', 0)})
        else:
            # Si no hay resultados, devolvemos 0 como unidades disponibles
            return jsonify({"available_units": 0})
    
    except Exception as e:
        # Captura cualquier error y lo muestra
        print(f"❌ Error al obtener unidades: {e}")
        return jsonify({"available_units": 0})






@app.route('/create_movement', methods=['POST'])
@login_required
def create_movement():
    try:
        if not request.is_json:
            return jsonify({"success": False, "message": "Se esperaba formato JSON"}), 400

        data = request.get_json()
        print(f"📥 Datos recibidos: {data}")  # Log para depuración

        # Obtener los productos enviados
        products = data.get('products', [])
        if not products:
            products = [{
                "product_id": data.get("product_id"),  # Aquí podría ser el IMEI
                "units_to_send": int(data.get("units_to_send", 0))
            }]

        origin_warehouse_id = data.get('origin_warehouse_id')
        destination_warehouse_id = data.get('destination_warehouse_id')
        movement_description = data.get('movement_description', '')
        destination_user_id = data.get('destination_user_id')

        print(f"🔄 Procesando movimiento: Origen: {origin_warehouse_id}, Destino: {destination_warehouse_id}, Productos: {products}")

        # Validaciones
        if not origin_warehouse_id or not destination_warehouse_id:
            return jsonify({"success": False, "message": "Faltan datos obligatorios: origen o destino."}), 400

        if origin_warehouse_id == destination_warehouse_id:
            return jsonify({"success": False, "message": "El almacén de origen y destino no pueden ser iguales."}), 400

        if not destination_user_id:
            return jsonify({"success": False, "message": "Falta el usuario de destino."}), 400

        # Insertar el movimiento en la tabla `movement`
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
                product_id_or_imei = product_data.get("product_id")  # Puede ser un IMEI
                units_to_send = int(product_data.get("units_to_send", 0))

                if not product_id_or_imei or units_to_send <= 0:
                    return jsonify({"success": False, "message": f"Datos inválidos para el producto {product_id_or_imei}."}), 400

                # 🔍 Obtener el verdadero `product_id` desde la BD usando el IMEI o el ID
                product = db.session.execute(
                    text("SELECT product_id FROM products WHERE imei = :imei"),
                    {"imei": product_id_or_imei}
                ).fetchone()

                # Si no lo encuentra por IMEI, intenta buscar por product_id si es un número válido
                if not product:
                    try:
                        product_id_int = int(product_id_or_imei)  # Convertir a entero si es posible
                        product = db.session.execute(
                            text("SELECT product_id FROM products WHERE product_id = :product_id"),
                            {"product_id": product_id_int}
                        ).fetchone()
                    except ValueError:
                        # Si no se puede convertir a entero, significa que no es un product_id válido
                        product = None

                if not product:
                    return jsonify({"success": False, "message": f"Producto con IMEI o ID {product_id_or_imei} no encontrado."}), 404

                product_id = product.product_id  # Obtener el ID real del producto

                # Insertar en `movementdetail` con estado "Pendiente"
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
                print(f"❌ Error al procesar el producto {product_id_or_imei}: {e}")
                db.session.rollback()
                return jsonify({"success": False, "message": f"Error al procesar el producto {product_id_or_imei}: {e}"}), 500

        # Confirmar cambios en la BD
        db.session.commit()
        print("✅ Movimiento registrado correctamente.")
        return jsonify({"success": True, "message": "Movimiento registrado correctamente."})

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al procesar la solicitud: {str(e)}")
        return jsonify({"success": False, "message": f"Error interno en el servidor: {str(e)}"}), 500



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
    user_warehouse_id = current_user.warehouse_id  # ID de la bodega del usuario

    # Obtener todas las bodegas menos la del usuario
    warehouses = ModelWarehouse.get_all_warehouses(db)
    warehouses_filtered = [w for w in warehouses if w['warehouse_id'] != user_warehouse_id]

    # Parámetros de búsqueda
    imei = request.args.get('imei')
    productname = request.args.get('productname')
    current_status = request.args.get('current_status')
    warehouse = request.args.get('warehouse_name')
    category = request.args.get('category')

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 18
    offset = (page - 1) * per_page

    # Buscar productos si hay filtros
    if imei or productname or current_status or warehouse or category:
        total = ModelProduct.count_filtered_products(db, imei, productname, current_status, warehouse, category)
        products = ModelProduct.filter_products(
            db, 
            imei=imei, 
            productname=productname, 
            current_status=current_status, 
            warehouse=warehouse, 
            category=category, 
            user_warehouse_id=user_warehouse_id 
        )
    else:
        total = ModelProduct.count_products_in_warehouse(db, user_warehouse_id)
        products = ModelProduct.get_products_in_warehouse_paginated(db, user_warehouse_id, user_warehouse_id)

    # Calcular total de páginas
    total_pages = (total + per_page - 1) // per_page
    
    return render_template(
        'menu/productsUser.html',
        products=products,
        page=page,
        total_pages=total_pages,
        current_status=current_status,
        warehouses=warehouses_filtered, 
    )






import time
from flask import make_response

@app.route('/get_product_by_imei/<imei>', methods=['GET'])
@login_required
def get_product_by_imei(imei):
    try:
        print(f"📡 Solicitud recibida para IMEI: {imei}")

        start_time = time.time()

        product_list = ModelProduct.get_product_imei(db, imei, current_user.warehouse_id)

        if product_list:
            product = product_list[0] 

            response_data = {
                "success": True,
                "product": product,  
                "current_user_warehouse_id": current_user.warehouse_id
            }

            print(f"✅ Producto encontrado en {time.time() - start_time:.4f} segundos")
            response = make_response(jsonify(response_data))
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "-1"

            return response

        print(f"⚠️ Producto no encontrado en {time.time() - start_time:.4f} segundos")
        return make_response(jsonify({"success": False, "message": "Producto no encontrado"}), 200)

    except Exception as e:
        print(f"❌ Error en la búsqueda del IMEI: {e}")
        return make_response(jsonify({"success": False, "message": str(e)}), 500)




@app.route('/products', methods=['GET'])
@login_required
def show_products():
    # Parámetros de búsqueda
    user_warehouse_id = current_user.warehouse_id
    imei = request.args.get('imei')
    productname = request.args.get('productname')
    current_status = request.args.get('current_status')
    category = request.args.get('category')
    warehouse = request.args.get('warehouse_name')

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 18
    offset = (page - 1) * per_page

    # Obtener almacenes y facturas activas
    warehouses = ModelWarehouse.get_all_warehouses(db)
    active_invoices = ModelInvoice.get_invoices_active(db)

    # Si hay filtros, usar `filter_products()`
    if imei or productname or current_status or warehouse or category:
        total = ModelProduct.count_filtered_products(db, imei, productname, current_status, warehouse, category)
        products = ModelProduct.filter_products(
            db, 
            imei=imei, 
            productname=productname, 
            current_status=current_status, 
            warehouse=warehouse, 
            category=category, 
            user_warehouse_id=user_warehouse_id 
        )
    else:
        total = ModelProduct.count_products_in_warehouse(db, user_warehouse_id)
        products = ModelProduct.get_products_in_warehouse_paginated(db, user_warehouse_id, user_warehouse_id)

    # Calcular total de páginas correctamente
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'menu/products.html',
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
    user_warehouse_id = current_user.warehouse_id
    imei = request.args.get('imei')
    productname = request.args.get('productname')
    current_status = request.args.get('current_status')
    category = request.args.get('category')
    warehouse = request.args.get('warehouse_name')

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 18
    offset = (page - 1) * per_page

    # Obtener almacenes y facturas activas
    warehouses = ModelWarehouse.get_all_warehouses(db)
    active_invoices = ModelInvoice.get_invoices_active(db)

     # Si hay filtros, usar `filter_products()`
    if imei or productname or current_status or warehouse or category:
        total = ModelProduct.count_filtered_products(db, imei, productname, current_status, warehouse, category)
        products = ModelProduct.filter_products(
            db, 
            imei=imei, 
            productname=productname, 
            current_status=current_status, 
            warehouse=warehouse, 
            category=category, 
            user_warehouse_id=user_warehouse_id 
        )
    else:
        total = ModelProduct.count_products_in_warehouse(db, user_warehouse_id)
        products = ModelProduct.get_products_in_warehouse_paginated(db, user_warehouse_id, user_warehouse_id)
    # Calcular total de páginas correctamente
    total_pages = (total + per_page - 1) // per_page
    print(f"📦 Datos enviados al frontend: {products}")

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

@app.route('/add_productUser', methods=['POST'])
def add_productUser():
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
    return redirect(url_for('show_productsUser'))


@app.route('/movementsUser', methods=['GET'])
@login_required
def get_movements_user():
    try:
        user_id = current_user.user_id  # Usuario autenticado
        movement_type = request.args.get('movement_type', None)  # Captura el tipo de movimiento
        movement_status = request.args.get('movement_status', None)  # Captura el estado del movimiento

        # Obtener movimientos filtrados
        movements = ModelMovement.get_movements_by_user(db, user_id, movement_type, movement_status)

        return render_template('menu/movementsUser.html', movements=movements)

    except Exception as e:
        flash(f"Error al cargar movimientos: {str(e)}", "danger")
        return redirect(url_for('menu.movementsUser'))



@app.route('/movementsAdmin', methods=['GET'])
@login_required
def get_movements_admin():
    try:
        warehouse_id = current_user.warehouse_id  # Obtiene la bodega del Admin
        movement_type = request.args.get('movement_type')  # Captura el filtro del formulario
        movement_status = request.args.get('movement_status')  # Captura el estado del movimiento

        # Consulta los movimientos filtrados por tipo y estado
        movements = ModelMovement.get_movements_by_admin(db, warehouse_id, movement_type, movement_status)

        return render_template('menu/movementsAdmin.html', movements=movements)

    except Exception as e:
        flash(f"Error al cargar movimientos: {str(e)}", "danger")
        return redirect(url_for('menu.movementsAdmin'))



@app.route('/movementsSuperAdmin', methods=['GET'])
@login_required
def get_movements_superadmin():
    try:
        # Verificar que el usuario sea superAdmin
        if current_user.role != 'superAdmin':
            flash("No tienes permisos para acceder a esta vista.", "danger")
            return redirect(url_for('dashboard'))

        # Obtener los parámetros de filtro del formulario
        movement_type = request.args.get('movement_type')
        movement_status = request.args.get('movement_status')

        # Obtener el número de página actual (por defecto 1)
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Número de movimientos por página

        # Consulta con paginación
        movements, total_movements = ModelMovement.get_all_movements_paginated(
            db, 
            movement_type=movement_type, 
            movement_status=movement_status,
            page=page, 
            per_page=per_page
        )

        # Calcular el número total de páginas
        total_pages = (total_movements // per_page) + (1 if total_movements % per_page > 0 else 0)

        return render_template(
            'menu/movementsSuperAdmin.html',
            movements=movements,
            page=page,
            total_pages=total_pages,
            movement_type=movement_type,
            movement_status=movement_status
        )

    except Exception as e:
        flash(f"Error al cargar movimientos: {str(e)}", "danger")
        return redirect(url_for('dashboard'))





@app.route('/add_productAdmin', methods=['POST'])
def add_productAdmin():
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
    return redirect(url_for('show_productsAdmin'))

@app.route('/edit_productAdmin', methods=['POST'])
@login_required
def edit_productAdmin():
    product_id = request.form.get('edit_product_id')
    productname = request.form.get('edit_productname', '').strip()
    imei = request.form.get('edit_imei', '').strip()
    storage = request.form.get('edit_storage', 0)
    battery = request.form.get('edit_battery', 0)
    color = request.form.get('edit_color', '').strip()
    description = request.form.get('edit_description', '').strip()
    category = request.form.get('edit_category', '').strip()
    units = request.form.get('edit_units', 0)
    supplier = request.form.get('edit_supplier', '').strip()
    document_number = request.form.get('edit_invoice', '').strip()
    invoice_quantity = request.form.get('edit_quantity', 0)
    price = request.form.get('edit_price', 0.0)
    warehouse_id = request.form.get('edit_warehouse_id')
    cost = request.form.get('edit_cost')
    cost = float(cost) if cost and cost.strip() else float('NaN')

    # Nuevo: Capturar el estado del producto
    current_status = request.form.get('edit_current_status', '').strip()

    # Obtiene el usuario actual
    user_id = current_user.user_id  

    # Actualiza el producto en la base de datos
    success = ModelProduct.update_product(
        db, product_id, productname, imei, storage, battery, color, description, cost,
        category, units, supplier, user_id, warehouse_id, current_status
    )

    # Si se proporciona un número de factura y cantidad, actualiza la factura
    success_invoice = False
    if document_number and invoice_quantity:
        success_invoice = ModelInvoice.update_invoicedetail(db, product_id, document_number, invoice_quantity, price)

    # Mensajes Flash
    if success_invoice:
        flash("Factura asociada exitosamente.", "success")
    elif document_number:
        flash("No se asoció el producto a la factura.", "danger")

    if success:
        flash("Producto actualizado exitosamente.", "success")
    else:
        flash("Error al actualizar el producto.", "danger")

    return redirect(url_for('show_productsAdmin'))







@app.route('/edit_product', methods=['POST'])
@login_required
def edit_product():
    product_id = request.form.get('edit_product_id')
    productname = request.form.get('edit_productname', '').strip()
    imei = request.form.get('edit_imei', '').strip()
    storage = request.form.get('edit_storage', 0)
    battery = request.form.get('edit_battery', 0)
    color = request.form.get('edit_color', '').strip()
    description = request.form.get('edit_description', '').strip()
    category = request.form.get('edit_category', '').strip()
    units = request.form.get('edit_units', 0)
    supplier = request.form.get('edit_supplier', '').strip()
    document_number = request.form.get('edit_invoice', '').strip()
    invoice_quantity = request.form.get('edit_quantity', 0)
    price = request.form.get('edit_price', 0.0)
    warehouse_id = request.form.get('edit_warehouse_id')
    cost = request.form.get('edit_cost')
    cost = float(cost) if cost and cost.strip() else float('NaN')

    # Nuevo: Capturar el estado del producto
    current_status = request.form.get('edit_current_status', '').strip()

    # Obtiene el usuario actual
    user_id = current_user.user_id  

    # Actualiza el producto en la base de datos
    success = ModelProduct.update_product(
        db, product_id, productname, imei, storage, battery, color, description, cost,
        category, units, supplier, user_id, warehouse_id, current_status
    )

    # Si se proporciona un número de factura y cantidad, actualiza la factura
    success_invoice = False
    if document_number and invoice_quantity:
        success_invoice = ModelInvoice.update_invoicedetail(db, product_id, document_number, invoice_quantity, price)

    # Mensajes Flash
    if success_invoice:
        flash("Factura asociada exitosamente.", "success")
    elif document_number:
        flash("No se asoció el producto a la factura.", "danger")

    if success:
        flash("Producto actualizado exitosamente.", "success")
    else:
        flash("Error al actualizar el producto.", "danger")

    return redirect(url_for('show_products'))








@app.route('/movements/<string:imei>', methods=['GET'])
def get_movements_by_imei(imei):
    try:
        
        
        movements = ModelMovement.get_movements_by_imei(db, imei)
        
        
        return jsonify({"movements": [movement for movement in movements]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
from PIL import Image
from reportlab.lib.utils import ImageReader
from io import BytesIO
import barcode
from barcode.writer import ImageWriter

def generate_barcode(code):
    try:
        # Generar código de barras con Code128
        barcode_class = barcode.get_barcode_class('code128')
        ean_barcode = barcode_class(code, writer=ImageWriter())

        # Guardar el código de barras en BytesIO
        barcode_bytes = BytesIO()
        ean_barcode.write(barcode_bytes, options={'write_text': False})
        barcode_bytes.seek(0)

        # Abrir la imagen con PIL
        img = Image.open(barcode_bytes)
        img = img.convert("RGB")  # Convertir la imagen a RGB si es necesario

        # Guardar la imagen en formato PNG en BytesIO
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return img_bytes  # Devolver el objeto BytesIO con la imagen

    except Exception as e:
        print(f"Error generando el código de barras: {str(e)}")
        return None


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

@app.route('/download_excel', methods=['POST'])
@login_required
def download_excel():
    # Obtener los productos desde el formulario
    products_json = request.form.get('products')

    if not products_json:
        return "No se recibieron productos", 400


    try:
        # Convertir la cadena JSON en una lista de Python
        products = json.loads(products_json)

        # Crear un DataFrame con los datos
        df = pd.DataFrame(products)

        # Crear la respuesta HTTP con el archivo Excel
        response = Response()
        response.status_code = 200
        response.mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        response.headers["Content-Disposition"] = "attachment; filename=productos.xlsx"

        # Escribir el DataFrame directamente en la respuesta
        with pd.ExcelWriter(response.stream, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="Productos")

        return response

    except json.JSONDecodeError as e:
        return f"Error al procesar JSON: {e}", 400
    

@app.route('/download_excel_invoices', methods=['POST'])
@login_required
def download_excel_invoices():
    # Obtener los productos desde el formulario
    invoices_json = request.form.get('invoices')

    if not invoices_json:
        return "No se recibieron productos", 400

    try:
        # Convertir la cadena JSON en una lista de Python
        invoices = json.loads(invoices_json)

        # Crear un DataFrame con los datos
        df = pd.DataFrame(invoices)

        # Crear la respuesta HTTP con el archivo Excel
        response = Response()
        response.status_code = 200
        response.mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        response.headers["Content-Disposition"] = "attachment; filename=invoices.xlsx"

        # Escribir el DataFrame directamente en la respuesta
        with pd.ExcelWriter(response.stream, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="invoices")

        return response

    except json.JSONDecodeError as e:
        return f"Error al procesar JSON: {e}", 400



@app.route('/download_invoice/<int:factura_id>', methods=['GET', 'POST'])
@login_required
def download_invoice(factura_id):
    try:
        edit_data = None
        if request.method == 'POST' and request.form.get('edit_data'):
            edit_data = json.loads(request.form.get('edit_data'))

        factura = ModelInvoice.get_invoice_by_id(db, factura_id)
        if not factura:
            return "Factura no encontrada", 404

        query = text("""
            SELECT p.imei, p.productname, id.quantity, id.price
            FROM invoicedetail id
            JOIN products p ON id.product_id = p.product_id
            WHERE id.invoice_id = :invoice_id
        """)
        details = db.session.execute(query, {"invoice_id": factura_id}).mappings().fetchall()
        if not details:
            return "La factura no tiene productos asociados", 404

        items = [
            {"nombre": row["productname"], "imei": row["imei"], "unidad": "Unidad",
             "precio": float(row["price"]), "cantidad": int(row["quantity"]),
             "descuento": 0, "impuesto": 0}
            for row in details
        ]

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        gris_claro = colors.Color(0.9, 0.9, 0.9)
        negro = colors.black
        logo_path = os.path.join(app.root_path, 'static', 'images', 'Logo3.png')

        def draw_header():
            try:
                c.drawImage(logo_path, 50, height - 150, width=100, preserveAspectRatio=True, mask='auto')
            except Exception as e:
                print(f"Error al cargar el logo: {e}")

            text_lines = edit_data['header_lines'] if edit_data and 'header_lines' in edit_data else [
                "CC Monterrey", "Medellín, Antioquia", "Tel: +573002619370",
                "idroid.com.co", "servicioalcliente@idroid.com.co"]

            c.setFont("Helvetica", 8)
            y_position = height - 35
            for line in text_lines:
                text_width = c.stringWidth(line, "Helvetica", 8)
                x_position = (width - text_width) / 2
                c.drawString(x_position, y_position, line)
                y_position -= 10

            c.setFont("Helvetica-Bold", 9)
            c.drawString(width - 150, height - 45, f"No. {factura.invoice_id}")
            c.setFont("Helvetica", 7)
            c.drawString(width - 150, height - 55, "No responsable de IVA")
            c.drawString(width - 150, height - 65, "Cuenta de cobro original")

            y_start = height - 155
            c.setFillColor(gris_claro)
            c.roundRect(40, y_start, width - 100, 75, 10, fill=1, stroke=0)
            c.setFillColor(negro)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(55, y_start + 60, "SEÑOR(ES):")
            c.drawString(220, y_start + 60, "CORREO:")
            c.drawString(350, y_start + 60, "TELÉFONO:")
            c.drawString(460, y_start + 60, "CC:")

            y_row = y_start + 45
            c.setFont("Helvetica", 8)
            c.drawString(55, y_row + 4, factura.client)
            c.drawString(225, y_row + 4, "         ")
            c.drawString(355, y_row + 4, "         ")
            c.drawString(460, y_row + 4, factura.document_number)

            y_start = y_row - 20
            c.setFillColor(gris_claro)
            c.roundRect(50, y_start, 170, 20, 10, fill=1, stroke=0)
            c.roundRect(220, y_start, 120, 20, 10, fill=1, stroke=0)
            c.setFillColor(negro)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(55, y_start + 6, "FECHA DE EXPEDICIÓN")
            c.drawString(220, y_start + 6, "FECHA DE VENCIMIENTO")
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            fecha_vencimiento = datetime.now().strftime("%Y-%m-%d")
            y_row = y_start - 10
            c.setFont("Helvetica", 8)
            c.drawString(55, y_row + 6, fecha_actual)
            c.drawString(225, y_row + 6, fecha_vencimiento)
            return y_row - 40

        def draw_table_header(y_tabla):
            col_widths = [45, 70, 55, 55, 55, 60, 100]
            x_start = 35
            for ancho in col_widths:
                x_start += ancho
                c.line(x_start, y_tabla, x_start, y_tabla + 10)
            c.setFillColor(gris_claro)
            c.rect(35, y_tabla, width - 70, 15, fill=1)
            c.setFillColor(negro)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(45, y_tabla + 4, "Ítem")
            c.drawString(160, y_tabla + 4, "Precio")
            c.drawString(230, y_tabla + 4, "Cantidad")
            c.drawString(300, y_tabla + 4, "Descuento")
            c.drawString(365, y_tabla + 4, "Impuesto")
            c.drawString(430, y_tabla + 4, "Total")
            c.drawString(500, y_tabla + 4, "Código de Barras")

        y_tabla = draw_header()
        draw_table_header(y_tabla)
        y_row = y_tabla

        total = 0
        altura_fila = 50
        items_por_pagina = 8
        item_count = 0

        for idx, item in enumerate(items):
            total_item = item["precio"] * item["cantidad"]
            imei_producto = item.get("imei")
            if not imei_producto:
                continue

            barcode_img = generate_barcode(imei_producto)
            img_reader = ImageReader(barcode_img)

            nombre = item["nombre"]
            partes = [nombre[i:i + 15] for i in range(0, len(nombre), 15)]

            c.setFont("Helvetica", 8)
            for i, parte in enumerate(partes):
                c.drawString(40, y_row - 10 - (i * 10), parte)

            c.drawString(160, y_row - 10, f"${item['precio']:,}")
            c.drawString(230, y_row - 10, str(item["cantidad"]))
            c.drawString(300, y_row - 10, f"${item['descuento']:,}")
            c.drawString(365, y_row - 10, f"${item['impuesto']:,}")
            c.drawString(420, y_row - 10, f"${total_item:,}")

            barcode_width = 100
            barcode_height = 30
            barcode_x = 475
            barcode_y = y_row - 32
            c.drawImage(img_reader, barcode_x, barcode_y, width=barcode_width, height=barcode_height)
            c.drawCentredString(barcode_x + barcode_width / 2, barcode_y - 8, imei_producto)

            y_row -= altura_fila
            total += total_item
            item_count += 1

            if item_count == items_por_pagina and idx != len(items) - 1:
                c.showPage()
                y_tabla = draw_header()
                draw_table_header(y_tabla)
                y_row = y_tabla
                item_count = 0

        # Total en letras
        total_en_letras = num2words(total, lang='es').upper() + " PESOS"
        y_info = y_row - 20
        c.setFont("Helvetica", 8)
        c.drawString(50, y_info, "Moneda: COP")
        c.drawString(50, y_info - 10, f"Fecha de expedición: {datetime.now().strftime('%Y-%m-%d')}")
        c.drawString(50, y_info - 20, "Forma de pago: Contado")
        c.drawString(50, y_info - 30, "Medio de pago: Efectivo")

        y_letras = y_info - 60
        c.setFillColor(gris_claro)
        c.rect(50, y_letras, width - 100, 15, fill=1, stroke=0)
        c.setFillColor(negro)
        c.setFont("Helvetica", 8)
        c.drawString(55, y_letras + 4, total_en_letras)

        warranty_text = edit_data['warranty_text'] if edit_data and 'warranty_text' in edit_data else (
            "La reparación del producto no genera costo siempre y cuando esté dentro del periodo de garantía "
            "y cumpla con los términos señalados dentro de la misma. *No se da garantía por humedades, "
            "no aplica la garantía por bloqueos por no registro, no tienen garantía equipos golpeados, apagados, "
            "por display, por táctil o por software.")

        warranty_lines = []
        words = warranty_text.split()
        current_line = ""
        for word in words:
            if len(current_line + " " + word) <= 100:
                current_line += " " + word if current_line else word
            else:
                warranty_lines.append(current_line)
                current_line = word
        if current_line:
            warranty_lines.append(current_line)

        y_garantia = y_letras - 10
        c.setFont("Helvetica", 7)
        for i, line in enumerate(warranty_lines):
            c.drawString(50, y_garantia - (i * 8), line.strip())

        y_after_warranty = y_garantia - (len(warranty_lines) * 8) - 5

        c.setFont("Helvetica-Bold", 9)
        c.drawString(420, y_after_warranty - -35, "Subtotal:")
        c.drawString(490, y_after_warranty - -35, f"${total:,}")
        c.drawString(420, y_after_warranty - -25, "Total:")
        c.drawString(490, y_after_warranty - -25, f"${total:,}")
        c.drawString(420, y_after_warranty - -15, "Total de Items:")
        c.drawString(500, y_after_warranty - -15, f"{len(items)}")

        legal_text = edit_data['legal_text'] if edit_data and 'legal_text' in edit_data else (
            "Esta factura se asimila en todos sus efectos a una letra de cambio de conformidad con el Art. 774 del código de comercio. "
            "Autorizo que en caso de incumplimiento de esta obligación sea reportado a las centrales de riesgo. "
            "Se cobrarán intereses por mora.")

        legal_lines = []
        words = legal_text.split()
        current_line = ""
        for word in words:
            if len(current_line + " " + word) <= 100:
                current_line += " " + word if current_line else word
            else:
                legal_lines.append(current_line)
                current_line = word
        if current_line:
            legal_lines.append(current_line)

        y_legal = y_after_warranty - 0
        c.setFont("Helvetica", 7)
        for i, line in enumerate(legal_lines):
            c.drawString(50, y_legal - (i * 8), line.strip())

        y_after_legal = y_legal - (len(legal_lines) * 8) - 5

        y_firma = y_after_legal - 20
        c.setFont("Helvetica-Bold", 8)
        c.drawString(50, y_firma, "ELABORADO POR")
        c.drawString(350, y_firma, "ACEPTADA, FIRMA Y/O SELLO Y FECHA")
        c.line(50, y_firma - 30, 250, y_firma - 30)
        c.line(350, y_firma - 30, 550, y_firma - 30)

        c.showPage()
        c.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"factura_{factura_id}.pdf", mimetype='application/pdf')

    except Exception as e:
        print(f"Error al generar el PDF de la factura {factura_id}: {str(e)}")
        return jsonify({"error": "Error al generar el PDF. Intente nuevamente más tarde."}), 500





#Manejo de errores en el servidor
def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1> Página no encontrada</h>", 404

if __name__=='__main__':
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run(host='0.0.0.0', port = '8080')


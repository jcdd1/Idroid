from sqlalchemy import text
from .entities.movement import Movement
from .queries.sql_queries import SQLQueries

class ModelMovement:

    @staticmethod
    def get_pending_movements(db):
        query = text("""
            SELECT * FROM movement
            WHERE status = 'Pendiente'
            ORDER BY creationdate ASC
        """)
        result = db.session.execute(query).fetchall()
        return [Movement(*row) for row in result]


    @staticmethod
    def count_movements(db):
        query = text("SELECT COUNT(*) FROM movement")
        return db.session.execute(query).scalar()

    @staticmethod
    def filter_movements(db, movement_id=None, product_id=None, movement_status=None, limit=10, offset=0):
        query = text("""
            WITH filtered_movements AS (
                SELECT *
                FROM movement
                WHERE 
                    (:movement_id IS NULL OR movementid = :movement_id)
                    AND (:product_id IS NULL OR productid = :product_id)
                    AND (:movement_status IS NULL OR status = :movement_status)
            )
            SELECT 
                (SELECT COUNT(*) FROM filtered_movements) AS total_count,
                fm.*
            FROM movement fm
            ORDER BY movementid ASC
            LIMIT :limit OFFSET :offset;
        """)
        params = {
            "movement_id": movement_id if movement_id else None,
            "product_id": product_id if product_id else None,
            "movement_status": movement_status if movement_status else None,
            "limit": limit,
            "offset": offset
        }
        result = db.session.execute(query, params).mappings().fetchall()

        total_count = result[0]['total_count'] if result else 0
        movements = [Movement(**row) for row in result]

        return movements, total_count

    @staticmethod
    def get_movement_by_id(db, movement_id):
        query = text("""
            SELECT *
            FROM movement
            WHERE movement_id = :movement_id
        """)
        row = db.session.execute(query, {"movement_id": movement_id}).fetchone()
        return Movement(*row) if row else None

    @staticmethod
    def update_movement(db, movement):
        query = text("""
            UPDATE inventory_movements
            SET destination_warehouse_id = :destination_warehouse_id,
                movement_status = :movement_status,
                movement_description = :movement_description
            WHERE movement_id = :movement_id;
        """)
        params = {
            "movement_id": movement.movement_id,
            "destination_warehouse_id": movement.destination_warehouse_id,
            "movement_status": movement.movement_status,
            "movement_description": movement.movement_description
        }
        try:
            db.session.execute(query, params)
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error updating movement: {e}")
            db.session.rollback()
            return False

    @staticmethod
    def approve_movement(db, movement_id, product_id):
        try:

            # Obtener los productos del movimiento en estado Pendiente
            movement_details = db.session.execute(
                text("""
                SELECT movementdetail.product_id, movementdetail.quantity, movement.destination_warehouse_id, 
                     movement.origin_warehouse_id 
                FROM movementdetail
                INNER JOIN movement on movementdetail.movement_id = movement.movement_id
                WHERE movementdetail.movement_id = :movement_id AND movementdetail.status = 'Pendiente'
                     AND movementdetail.product_id = :product_id
                """),
                {"movement_id": movement_id, "product_id": product_id}
            ).fetchall()

            for detail in movement_details:
                product_id = detail.product_id
                units_to_send = detail.quantity
                origin_warehouse = detail.origin_warehouse_id
                destination_warehouse = detail.destination_warehouse_id

                # Reducir stock en la bodega de origen
                query = text("""
                    WITH updated_source AS (
                        UPDATE WarehouseStock
                        SET units = units - :units_to_send
                        WHERE warehouse_id = :origin_warehouse AND product_id = :product_id
                        RETURNING units
                    )
                    INSERT INTO WarehouseStock (warehouse_id, product_id, units)
                    VALUES (:destination_warehouse, :product_id, :units_to_send)
                    ON CONFLICT (warehouse_id, product_id)
                    DO UPDATE SET units = WarehouseStock.units + EXCLUDED.units;
                """)
                db.session.execute(query, {"destination_warehouse": destination_warehouse, 
                                           "product_id": product_id, "units_to_send": units_to_send, 
                                           "origin_warehouse": origin_warehouse})
            # Marcar como aprobado
                db.session.execute(
                    text("""
                    UPDATE movementdetail 
                    SET status = 'Aprobado'
                    WHERE movement_id = :movement_id AND product_id = :product_id
                    """),
                    {"movement_id": movement_id, "product_id": product_id}
                )

                movement_pending = db.session.execute(
                    text("""
                    Select md.movement_id FROM movementdetail as md
                         WHERE md.movement_id = :movement_id AND md.status = 'Pendiente'
                    """),{"movement_id": movement_id}).fetchone()
                if movement_pending is None:
                    # Marcar como aprobado
                    db.session.execute(
                        text("""
                        UPDATE movement 
                        SET status = 'Aprobado'
                        WHERE movement_id = :movement_id
                        """),
                        {"movement_id": movement_id}
                    )

                db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al aprobar movimiento: {e}")
            return False

    @staticmethod
    def reject_movement(db, movement_id, product_id, reason=""):
        try:
            # Imprime los valores recibidos para depurar
            print(f"Rechazando movimiento con ID: {movement_id}, Producto ID: {product_id}, Razón: {reason}")
            
            # Primer UPDATE (movementdetail)
            result = db.session.execute(
                text("""
                UPDATE movementdetail 
                SET status = 'Rechazado', rejection_reason = :reason
                WHERE movement_id = :movement_id AND product_id = :product_id
                """),
                {"movement_id": movement_id, "reason": reason, "product_id": product_id}
            )
            print(f"Filas actualizadas en movementdetail: {result.rowcount}")  # Ver cuántas filas fueron afectadas

            # Verifica si el movimiento aún está pendiente
            movement_pending = db.session.execute(
                text("""
                Select md.movement_id FROM movementdetail as md
                WHERE md.movement_id = :movement_id AND md.status = 'Pendiente'
                """), {"movement_id": movement_id}
            ).fetchone()

            print(f"Estado de movimiento pendiente: {movement_pending}")

            # Si no quedan detalles pendientes, actualiza la tabla principal movement
            if movement_pending is None:
                print(f"Actualizando estado del movimiento principal con ID: {movement_id}")
                result = db.session.execute(
                    text("""
                    UPDATE movement 
                    SET status = 'Rechazado', notes = CONCAT(notes, ' ', :reason)
                    WHERE movement_id = :movement_id
                    """),
                    {"movement_id": movement_id, "reason": reason}
                )
                print(f"Filas actualizadas en movement: {result.rowcount}")  # Ver cuántas filas fueron afectadas

            db.session.commit()
            print(f"Movimiento {movement_id} rechazado con éxito.")
            return True

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al rechazar movimiento: {e}")
            return False






    @staticmethod
    def create_movement(db, movement_type, origin_warehouse_id, destination_warehouse_id, movement_description, user_id, products):
        """ 
        Crea un movimiento y registra los detalles asegurando que product_id sea un INT válido 
        """
        try:
            if movement_type == "sale":
                destination_warehouse_id = origin_warehouse_id  

            # 🔹 Crear el movimiento
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
                        'created',  
                        :movement_description, 
                        :user_id, 
                        :user_id, 
                        :movement_type
                    ) RETURNING movement_id
                """),
                {
                    "movement_type": movement_type,
                    "origin_warehouse_id": origin_warehouse_id,
                    "destination_warehouse_id": destination_warehouse_id,
                    "movement_description": movement_description,
                    "user_id": user_id
                }
            ).scalar()

            if not movement_id:
                print("❌ No se pudo crear el movimiento.")
                return None

            print(f"🚀 Movimiento creado con ID: {movement_id} (Tipo: {movement_type})")

            # 🔹 Registrar cada producto en `movementdetail`
            for product_data in products:
                imei = product_data.get("imei")  
                units_to_move = int(product_data.get("quantity", 0))

                if not imei or units_to_move <= 0:
                    print(f"⚠️ Producto inválido o cantidad incorrecta: {imei}, {units_to_move}")
                    continue

                # 🔹 Obtener el product_id basado en el IMEI
                result = db.session.execute(
                    text("SELECT product_id FROM products WHERE imei = :imei"),
                    {"imei": imei}
                ).fetchone()

                if not result:
                    print(f"⚠️ No se encontró un product_id para IMEI: {imei}, omitiendo...")
                    continue  # Saltar este producto si no existe en la base de datos

                product_id = result[0]  # Ahora product_id es un INT válido

                # 🔹 Insertar en `movementdetail` con el product_id correcto
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
                        'completed'
                    )
                    """),
                    {
                        "movement_id": movement_id,
                        "product_id": product_id,
                        "units": units_to_move
                    }
                )

                # 🔹 Reducir stock en el almacén de origen (ahora en `warehousestock`)
                db.session.execute(
                    text("""
                    UPDATE warehousestock 
                    SET units = units - :units 
                    WHERE product_id = :product_id AND warehouse_id = :origin_warehouse_id
                    """),
                    {
                        "product_id": product_id,
                        "units": units_to_move,
                        "origin_warehouse_id": origin_warehouse_id
                    }
                )

                db.session.execute(
                    text("""
                    UPDATE products 
                    SET units = units - :units 
                    WHERE product_id = :product_id
                    """),
                    {
                        "product_id": product_id,
                        "units": units_to_move
                    }
                )

                # 🔹 Si es transferencia, aumentar stock en el destino
                if movement_type == "transfer":
                    # Verificar si el producto ya existe en el almacén destino
                    existing_product = db.session.execute(
                        text("""
                        SELECT product_id FROM warehousestock 
                        WHERE product_id = :product_id AND warehouse_id = :destination_warehouse_id
                        """),
                        {"product_id": product_id, "destination_warehouse_id": destination_warehouse_id}
                    ).fetchone()

                    if existing_product:
                        # Si ya existe en el destino, aumentar unidades
                        db.session.execute(
                            text("""
                            UPDATE warehousestock 
                            SET units = units + :units 
                            WHERE product_id = :product_id AND warehouse_id = :destination_warehouse_id
                            """),
                            {
                                "product_id": product_id,
                                "units": units_to_move,
                                "destination_warehouse_id": destination_warehouse_id
                            }
                        )
                    else:
                        # Si no existe, crear un nuevo registro en la bodega destino
                        db.session.execute(
                            text("""
                            INSERT INTO warehousestock (
                                warehouse_id, product_id, units
                            ) VALUES (
                                :warehouse_id, :product_id, :units
                            )
                            """),
                            {
                                "warehouse_id": destination_warehouse_id,
                                "product_id": product_id,
                                "units": units_to_move
                            }
                        )

            # 🔹 Confirmar los cambios
            db.session.commit()
            return movement_id

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error en create_movement: {e}")
            return None




    @staticmethod
    def create_movement_invoice(db, movement_type, origin_warehouse_id, 
                            movement_description, user_id, products, invoice_id,destination_warehouse_id):
            try:
                # 1️⃣ Crear el movimiento en la tabla `movement`
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
                            :origin_warehouse_id, 
                            NOW(),
                            'sale',  
                            :movement_description, 
                            :user_id, 
                            :user_id, 
                            :movement_type
                        ) RETURNING movement_id
                    """),
                    {
                        "movement_type": movement_type,
                        "origin_warehouse_id": origin_warehouse_id,
                        "movement_description": movement_description,
                        "user_id": user_id
                    }
                ).scalar()

                if not movement_id:
                    print("❌ No se pudo crear el movimiento.")
                    return None

                print(f"🚀 Movimiento creado con ID: {movement_id} (Tipo: {movement_type})")

                # 2️⃣ Registrar cada producto en `movementdetail`
                for product_data in products:
                    product_id = product_data.get("product_id")  
                    units_to_move = int(product_data.get("quantity", 0))
                    price = product_data.get("price")

                    if not product_id or units_to_move <= 0:
                        print(f"⚠️ Producto inválido o cantidad incorrecta: {product_id}, {units_to_move}")
                        continue
                
                    query = text("""
                        INSERT INTO invoicedetail (invoice_id, product_id, quantity, price)
                        VALUES (:invoice_id, :product_id, :quantity, :price)
                    """)

                    db.session.execute(query, {
                        'invoice_id': invoice_id,
                        'product_id': product_id,
                        'quantity': units_to_move,
                        'price': price
                    })
                    
                    db.session.commit()

                    # Verificar stock en origen
                    product = db.session.execute(
                        text("""
                        SELECT product_id, units FROM warehousestock 
                        WHERE product_id = :product_id AND warehouse_id = :origin_warehouse_id
                        """),
                        {"product_id": product_id, "origin_warehouse_id": origin_warehouse_id}
                    ).fetchone()

                    if not product or product.units < units_to_move:
                        print(f"⚠️ Stock insuficiente para producto {product_id}, omitiendo...")
                        continue

                    # 3️⃣ Insertar en `movementdetail`
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
                            'completed'
                        )
                    """),
                    {
                        "movement_id": movement_id,
                        "product_id": product_id,  # Ahora usamos el ID real del producto (INT)
                        "units": units_to_move
                    }
                )

                # 🔹 Reducir stock en el almacén de origen
                db.session.execute(
                    text("""
                    UPDATE warehousestock 
                    SET units = units - :units 
                    WHERE product_id = :product_id AND warehouse_id = :origin_warehouse_id
                    """),
                    {
                        "product_id": product_id,
                        "units": units_to_move,
                        "origin_warehouse_id": origin_warehouse_id
                    }
                )

                # 🔹 Si es una transferencia, aumentar stock en el destino
                if movement_type == "transfer":
                    existing_product = db.session.execute(
                        text("""
                        SELECT product_id FROM warehousestock 
                        WHERE product_id = :product_id AND warehouse_id = :destination_warehouse_id
                        """),
                        {"product_id": product_id, "destination_warehouse_id": destination_warehouse_id}
                    ).fetchone()

                    if existing_product:
                        # 🔹 Si ya existe en el destino, aumentar unidades
                        db.session.execute(
                            text("""
                            UPDATE warehousestock 
                            SET units = units + :units 
                            WHERE product_id = :product_id AND warehouse_id = :destination_warehouse_id
                            """),
                            {
                                "product_id": product_id,
                                "units": units_to_move,
                                "destination_warehouse_id": destination_warehouse_id
                            }
                        )
                    else:
                        # 🔹 Si no existe, agregarlo al destino
                        db.session.execute(
                            text("""
                            INSERT INTO warehousestock (warehouse_id, product_id, units)
                            VALUES (:warehouse_id, :product_id, :units)
                            """),
                            {
                                "warehouse_id": destination_warehouse_id,
                                "product_id": product_id,
                                "units": units_to_move
                            }
                        )

                # 🔹 Confirmar cambios en la base de datos
                db.session.commit()
                return movement_id

            except Exception as e:
                db.session.rollback()  # Deshacer cambios en caso de error
                print(f"❌ Error en create_movement: {e}")
                return None



    @staticmethod
    def get_all_movements_paginated(db, movement_type=None, movement_status=None, page=1, per_page=10):
        try:
            offset = (page - 1) * per_page
            query = """
                SELECT
                    m.movement_id,
                    p.imei,
                    ow.warehouse_name AS origin_warehouse,
                    dw.warehouse_name AS destination_warehouse,
                    m.creation_date,
                    m.status AS movement_status,
                    m.notes AS movement_notes,
                    LOWER(m.movement_type) AS movement_type,
                    creator.name AS created_by_user,
                    creator.role AS creator_role,
                    handler.name AS handled_by_user,
                    handler.role AS handler_role,
                    md.detail_id,
                    md.product_id,
                    md.quantity AS moved_quantity,
                    md.status AS detail_status,
                    md.rejection_reason,
                    r.return_id,
                    r.quantity AS returned_quantity,
                    r.return_date,
                    r.notes AS return_notes
                FROM movement AS m
                JOIN movementdetail AS md ON m.movement_id = md.movement_id
                LEFT JOIN return AS r ON md.detail_id = r.movement_detail_id
                JOIN warehouses AS ow ON m.origin_warehouse_id = ow.warehouse_id
                JOIN warehouses AS dw ON m.destination_warehouse_id = dw.warehouse_id
                JOIN users AS creator ON m.created_by_user_id = creator.user_id
                JOIN users AS handler ON m.handled_by_user_id = handler.user_id
                JOIN products AS p ON md.product_id = p.product_id
            """
            count_query = """
                SELECT COUNT(*) FROM movement AS m
            """
            params = {}
            where_added = False  
            
            # Filtro por tipo de movimiento
            if movement_type:
                query += " WHERE LOWER(m.movement_type) = LOWER(:movement_type)"
                count_query += " WHERE LOWER(m.movement_type) = LOWER(:movement_type)"
                params['movement_type'] = str(movement_type)
                where_added = True
            
            # Filtro por estado de movimiento
            if movement_status:
                if where_added:
                    query += " AND LOWER(m.status) = LOWER(:movement_status)"
                    count_query += " AND LOWER(m.status) = LOWER(:movement_status)"
                else:
                    query += " WHERE LOWER(m.status) = LOWER(:movement_status)"
                    count_query += " WHERE LOWER(m.status) = LOWER(:movement_status)"
                params['movement_status'] = str(movement_status)
            
            # Agregar la paginación y orden
            query += " ORDER BY m.creation_date DESC LIMIT :per_page OFFSET :offset"
            params['per_page'] = per_page
            params['offset'] = offset
            
            result = db.session.execute(text(query), params).mappings().fetchall()
            total_movements = db.session.execute(text(count_query), params).scalar()
            
            movements = [dict(row) for row in result] if result else []
            return movements, total_movements
        except Exception as e:
            print(f"Error al obtener movimientos: {str(e)}")
            return [], 0



    @staticmethod
    def get_movements_by_admin(db, warehouse_id, movement_type=None, movement_status=None):
        try:
            query = """
                SELECT 
                    m.movement_id,
                    ow.warehouse_name AS origin_warehouse,
                    dw.warehouse_name AS destination_warehouse,
                    m.creation_date,
                    m.status AS movement_status,
                    m.notes AS movement_notes,
                    LOWER(m.movement_type) AS movement_type,
                    creator.name AS created_by_user,
                    creator.role AS creator_role,
                    handler.name AS handled_by_user,
                    handler.role AS handler_role,
                    md.detail_id,
                    md.product_id,
                    md.quantity AS moved_quantity,
                    md.status AS detail_status,
                    md.rejection_reason,
                    r.return_id,
                    r.quantity AS returned_quantity,
                    r.return_date,
                    r.notes AS return_notes,
                    p.imei
                FROM movement AS m
                JOIN movementdetail AS md ON m.movement_id = md.movement_id
                LEFT JOIN return AS r ON md.detail_id = r.movement_detail_id
                JOIN warehouses AS ow ON m.origin_warehouse_id = ow.warehouse_id
                JOIN warehouses AS dw ON m.destination_warehouse_id = dw.warehouse_id
                JOIN users AS creator ON m.created_by_user_id = creator.user_id
                JOIN users AS handler ON m.handled_by_user_id = handler.user_id
                JOIN products AS p ON md.product_id = p.product_id
                WHERE (m.origin_warehouse_id = :warehouse_id OR m.destination_warehouse_id = :warehouse_id)
            """

            # Aplicar filtro opcional por tipo de movimiento
            if movement_type:
                query += " AND LOWER(m.movement_type) = LOWER(:movement_type)"
            
            # Aplicar filtro opcional por estado
            if movement_status:
                query += " AND LOWER(md.status) = LOWER(:movement_status)"

            query += " ORDER BY m.creation_date DESC"

            params = {'warehouse_id': warehouse_id}
            if movement_type:
                params['movement_type'] = movement_type.lower()
            if movement_status:
                params['movement_status'] = movement_status.lower()

            result = db.session.execute(text(query), params).mappings().fetchall()
            movements = [dict(row) for row in result] if result else []

            return movements

        except Exception as e:
            print(f"Error al obtener movimientos de la bodega: {str(e)}")
            return []


    @staticmethod
    def get_all_movements(db, movement_type=None):
        try:
            query = """
                SELECT 
                    m.movement_id,
                    ow.warehouse_name AS origin_warehouse,
                    dw.warehouse_name AS destination_warehouse,
                    m.creation_date,
                    m.status AS movement_status,
                    m.notes AS movement_notes,
                    LOWER(m.movement_type) AS movement_type,
                    creator.name AS created_by_user,
                    creator.role AS creator_role,
                    handler.name AS handled_by_user,
                    handler.role AS handler_role,
                    md.detail_id,
                    md.product_id,
                    md.quantity AS moved_quantity,
                    md.status AS detail_status,
                    md.rejection_reason,
                    r.return_id,
                    r.quantity AS returned_quantity,
                    r.return_date,
                    r.notes AS return_notes
                FROM movement AS m
                JOIN movementdetail AS md ON m.movement_id = md.movement_id
                LEFT JOIN return AS r ON md.detail_id = r.movement_detail_id
                JOIN warehouses AS ow ON m.origin_warehouse_id = ow.warehouse_id
                JOIN warehouses AS dw ON m.destination_warehouse_id = dw.warehouse_id
                JOIN users AS creator ON m.created_by_user_id = creator.user_id
                JOIN users AS handler ON m.handled_by_user_id = handler.user_id
            """

            # Aplicar filtro opcional por tipo de movimiento
            if movement_type:
                query += " WHERE LOWER(m.movement_type) = LOWER(:movement_type)"

            query += " ORDER BY m.creation_date DESC"

            params = {}
            if movement_type:
                params['movement_type'] = movement_type.lower()

            result = db.session.execute(text(query), params).mappings().fetchall()
            movements = [dict(row) for row in result] if result else []

            return movements

        except Exception as e:
            print(f"Error al obtener movimientos: {str(e)}")
            return []



    @staticmethod
    def get_movements_by_user(db, user_id, movement_type=None, movement_status=None):
        try:
            query = """
                SELECT 
                    m.movement_id,
                    p.imei,  
                    ow.warehouse_name AS origin_warehouse,
                    dw.warehouse_name AS destination_warehouse,
                    m.creation_date,
                    m.status AS movement_status,
                    m.notes AS movement_notes,
                    m.movement_type,
                    creator.name AS created_by_user,
                    md.quantity AS moved_quantity
                FROM movement AS m
                JOIN movementdetail AS md ON m.movement_id = md.movement_id
                JOIN warehouses AS ow ON m.origin_warehouse_id = ow.warehouse_id
                JOIN warehouses AS dw ON m.destination_warehouse_id = dw.warehouse_id
                JOIN users AS creator ON m.created_by_user_id = creator.user_id
                JOIN products AS p ON md.product_id = p.product_id
                WHERE (m.created_by_user_id = :user_id OR m.handled_by_user_id = :user_id)
            """

            # Añadir filtros opcionales si se proporcionan
            if movement_type:
                query += " AND LOWER(m.movement_type) = LOWER(:movement_type)"
            if movement_status:
                query += " AND LOWER(m.status) = LOWER(:movement_status)"

            # Añadir el ordenamiento por fecha de creación
            query += " ORDER BY m.creation_date DESC"

            # Configurar los parámetros de la consulta
            params = {'user_id': user_id}
            if movement_type:
                params['movement_type'] = movement_type.lower()
            if movement_status:
                params['movement_status'] = movement_status.lower()

            # Ejecutar la consulta
            result = db.session.execute(text(query), params).mappings().fetchall()

            # Convertir el resultado en un diccionario
            movements = [dict(row) for row in result] if result else []

            return movements

        except Exception as e:
            print(f"Error al obtener movimientos: {str(e)}")
            return []



    @staticmethod
    def get_movements_by_imei(db, product_id):
        try:
            query = text(SQLQueries.get_movements_by_product_query())
            params = {'product_id': product_id}

            print(f"Ejecutando consulta con: {params}")
            result = db.session.execute(query, params).mappings().fetchall()

            print(f"Resultados obtenidos: {result}")  # Verifica si hay datos

            movements = [dict(row) for row in result] if result else []

            return movements

        except Exception as e:
            print(f"Error: {str(e)}")
            return []

    
    @staticmethod
    def get_pending_movements(db, warehouseid, limit, offset):
        try:

            # Consulta SQL
            query = text("""
                            SELECT * FROM movement
                            WHERE (Origin_Warehouse_Id = :warehouseid OR Destination_Warehouse_Id = :warehouseid)
                            AND status = 'Pending'
                            LIMIT :limit OFFSET :offset;               
            """)

            params = {
                    'warehouseid': warehouseid,
                    'limit': limit, 
                    'offset': offset
                    }
            result = db.session.execute(query, params).mappings().fetchall()
            

            movements = [Movement(**row) for row in result]

            return movements

        except Exception as e:
            raise Exception(f"Error retrieving movements: {str(e)}")
        

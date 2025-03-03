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
    def approve_movement(db, movement_id):
        try:

            # Obtener los productos del movimiento en estado Pendiente
            movement_details = db.session.execute(
                text("""
                SELECT movementdetail.product_id, movementdetail.quantity, movement.destination_warehouse_id, 
                     movement.origin_warehouse_id 
                FROM movementdetail
                INNER JOIN movement on movementdetail.movement_id = movement.movement_id
                WHERE movementdetail.movement_id = :movement_id AND movementdetail.status = 'Pendiente'
                """),
                {"movement_id": movement_id}
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
                    WHERE movement_id = :movement_id
                    """),
                    {"movement_id": movement_id}
                )
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
    def reject_movement(db, movement_id, reason=""):
        try:
            db.session.execute(
                text("""
                UPDATE movementdetail 
                SET status = 'Rechazado', rejection_reason = :reason
                WHERE movement_id = :movement_id
                """),
                {"movement_id": movement_id, "reason": reason}
            )

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al rechazar movimiento: {e}")
            return False


    @staticmethod
    def create_movement(db, origin_warehouse_id, destination_warehouse_id, 
                        movement_description, destination_user_id, user_id, products):
        try:
            # 1️⃣ Crear el registro del movimiento en la tabla `movement`
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
                    "user_id": user_id,
                    "destination_user_id": destination_user_id
                }
            ).scalar()

            # 2️⃣ Procesar cada producto y registrar en `movementdetail`
            for product_data in products:
                product_id = product_data.get("product_id")  
                units_to_send = int(product_data.get("units_to_send", 0))

                if not product_id or units_to_send <= 0:
                    return False  # Datos inválidos, terminamos aquí

                # Obtener stock del producto en el almacén de origen
                product = db.session.execute(
                    text("""
                    SELECT product_id, units FROM products 
                    WHERE product_id = :product_id AND warehouse_id = :origin_warehouse_id
                    """),
                    {"product_id": product_id, "origin_warehouse_id": origin_warehouse_id}
                ).fetchone()

                if not product or product.units < units_to_send:
                    return False  # No hay suficiente stock

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
                        'Pendiente'
                    )
                    """),
                    {
                        "movement_id": movement_id,
                        "product_id": product_id,
                        "units": units_to_send
                    }
                )

                # 4️⃣ Restar stock en almacén de origen
                db.session.execute(
                    text("""
                    UPDATE products 
                    SET units = units - :units 
                    WHERE product_id = :product_id AND warehouse_id = :origin_warehouse_id
                    """),
                    {
                        "product_id": product_id,
                        "units": units_to_send,
                        "origin_warehouse_id": origin_warehouse_id
                    }
                )

                # 5️⃣ Verificar si el producto ya existe en el almacén destino
                existing_product = db.session.execute(
                    text("""
                    SELECT product_id FROM products 
                    WHERE product_id = :product_id AND warehouse_id = :destination_warehouse_id
                    """),
                    {"product_id": product_id, "destination_warehouse_id": destination_warehouse_id}
                ).fetchone()

                if existing_product:
                    # Si ya existe en el destino, aumentar unidades
                    db.session.execute(
                        text("""
                        UPDATE products 
                        SET units = units + :units 
                        WHERE product_id = :product_id AND warehouse_id = :destination_warehouse_id
                        """),
                        {"product_id": product_id, "units": units_to_send, "destination_warehouse_id": destination_warehouse_id}
                    )
                else:
                    # Si no existe, crear un nuevo registro en la bodega destino
                    product_info = db.session.execute(
                        text("""
                        SELECT productname, imei, price, product_category_id 
                        FROM products WHERE product_id = :product_id
                        """),
                        {"product_id": product_id}
                    ).fetchone()

                    db.session.execute(
                        text("""
                        INSERT INTO products (
                            productname, imei, price, units, warehouse_id, product_category_id
                        ) VALUES (
                            :productname, :imei, :price, :units, :warehouse_id, :product_category_id
                        )
                        """),
                        {
                            "productname": product_info.productname,
                            "imei": product_info.imei,
                            "price": product_info.price,
                            "units": units_to_send,
                            "warehouse_id": destination_warehouse_id,
                            "product_category_id": product_info.product_category_id
                        }
                    )

            # 6️⃣ Confirmar los cambios
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error en create_movement: {e}")
            return False



            

    @staticmethod
    def get_movements_by_imei(db, product_id):
        query = text(SQLQueries.get_movements_by_product_query())
        params = {
                'product_id': product_id
            }

        result = db.session.execute(query, params).mappings().fetchall()
                            
        if result:
            movements = [dict(row) for row in result]
        else:
            movements = []
        
        return movements
    
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
        

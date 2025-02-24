from sqlalchemy import text
from .entities.movement import Movement
from .queries.sql_queries import SQLQueries

class ModelMovement:

    @staticmethod
    def get_movements_paginated(db, limit, offset):
        query = text("""
            SELECT *
            FROM movement
            ORDER BY creationdate ASC
            LIMIT :limit OFFSET :offset;
        """)
        result = db.session.execute(query, {"limit": limit, "offset": offset}).fetchall()
        return [
            Movement(*row) for row in result
        ]

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
            WHERE movementid = :movement_id
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
    def create_movement(db, product_id, origin_warehouse_id, destination_warehouse_id, movement_description, user_id):
        try:
            query = text("""
            INSERT INTO movement (
                created_by_user_id, 
                origin_warehouse_id, 
                destination_warehouse_id, 
                creation_date, 
                movement_type, 
                status, 
                notes
            )
            VALUES (
                :user_id,  -- Usuario que crea el movimiento (ajustar según sistema de usuarios)
                :origin_warehouse_id, 
                :destination_warehouse_id, 
                CURRENT_TIMESTAMP, 
                'Transfer',  -- Tipo de movimiento (ajustar si es necesario)
                'New',  -- Estado del movimiento
                :movement_description
            )
        """)

            db.session.execute(query, {
            'origin_warehouse_id': origin_warehouse_id,
            'destination_warehouse_id': destination_warehouse_id,
            'movement_description': movement_description,
            'user_id': user_id
            })
            db.session.commit()

            print(f" Movimiento creado correctamente: Origen {origin_warehouse_id} → Destino {destination_warehouse_id}")
            return True

        except Exception as e:
            print(f" Error al crear el movimiento: {e}")
            db.session.rollback()
            return False


            

    @staticmethod
    def get_movements_by_imei(db, imei):
        query = text(SQLQueries.get_movements_by_imei_query())
        params = {
                'imei': imei
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
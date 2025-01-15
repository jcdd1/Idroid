from sqlalchemy import text
from .entities.movement import Movement

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
    def create_movement(db, product_id, origin_warehouse_id, destination_warehouse_id, movement_description):
        try:
            query = text("""
                INSERT INTO inventory_movements (
                    product_id, 
                    origin_warehouse_id, 
                    destination_warehouse_id, 
                    sender_user_id, 
                    send_date, 
                    receive_date, 
                    movement_status, 
                    movement_description
                )
                VALUES (
                    :product_id, 
                    :origin_warehouse_id, 
                    :destination_warehouse_id, 
                    1,  -- Asume un ID de usuario para enviar
                    CURRENT_TIMESTAMP, 
                    NULL, 
                    'New', 
                    :movement_description
                )
            """)
            db.session.execute(query, {
                'product_id': product_id,
                'origin_warehouse_id': origin_warehouse_id,
                'destination_warehouse_id': destination_warehouse_id,
                'movement_description': movement_description
            })
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error al crear el movimiento: {e}")
            db.session.rollback()
            return False
            

    @staticmethod
    def get_movements_by_imei(db, imei):
        query = text("""
                SELECT 
                    m.movement_id,
                    m.origin_warehouse_id,
                    m.destination_warehouse_id,
                    m.creation_date,
                    m.status AS movement_status,
                    m.notes AS movement_notes,
                    d.detail_id,
                    d.product_id,
                    d.quantity,
                    d.status AS detail_status,
                    d.rejection_reason,
                    r.return_id,
                    r.quantity AS returned_quantity,
                    r.return_date,
                    r.notes AS return_notes
                FROM 
                    Movement m
                LEFT JOIN 
                    MovementDetail d
                ON 
                    m.movement_id = d.movement_id
                LEFT JOIN 
                    Return r
                ON 
                    d.detail_id = r.movement_detail_id
                WHERE 
                    d.product_id = :imei;
        """)
        result = db.execute(query, {"imei": imei})
        
        # Convertir los resultados a una lista de diccionarios
        movements = [
            {
                "movement_id": row["movement_id"],
                "origin_warehouse_id": row["origin_warehouse_id"],
                "destination_warehouse_id": row["destination_warehouse_id"],
                "creation_date": row["creation_date"],
                "movement_status": row["movement_status"],
                "movement_notes": row["movement_notes"],
                "detail_id": row["detail_id"],
                "product_id": row["product_id"],
                "quantity": row["quantity"],
                "detail_status": row["detail_status"],
                "rejection_reason": row["rejection_reason"],
                "return_id": row["return_id"],
                "returned_quantity": row["returned_quantity"],
                "return_date": row["return_date"],
                "return_notes": row["return_notes"],
            }
            for row in result
        ]
        
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

            # return [
            #     {
            #         "movement_id": row[0],
            #         "origin_warehouse_id": row[1],
            #         "destination_warehouse_id": row[2],
            #         "creation_date": row[3],
            #         "status": row[4],
            #         "notes": row[5],
            #         "sender_user_id": row[6],
            #         "receiver_user_id": row[7]
            #     }
            #     for row in result
            # ]
        except Exception as e:
            raise Exception(f"Error retrieving movements: {str(e)}")
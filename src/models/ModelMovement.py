from sqlalchemy import text
from .entities.movement import Movement

class ModelMovement:

    @staticmethod
    def get_movements_paginated(db, limit, offset):
        query = text("""
            SELECT movement_id, product_id, origin_warehouse_id, destination_warehouse_id, 
                   sender_user_id, receiver_user_id, send_date, receive_date, 
                   movement_status, movement_description
            FROM inventory_movements
            ORDER BY movement_id ASC
            LIMIT :limit OFFSET :offset;
        """)
        result = db.session.execute(query, {"limit": limit, "offset": offset}).fetchall()
        return [
            Movement(*row) for row in result
        ]

    @staticmethod
    def count_movements(db):
        query = text("SELECT COUNT(*) FROM inventory_movements")
        return db.session.execute(query).scalar()

    @staticmethod
    def filter_movements(db, movement_id=None, product_id=None, movement_status=None, limit=10, offset=0):
        query = text("""
            WITH filtered_movements AS (
                SELECT *
                FROM inventory_movements
                WHERE 
                    (:movement_id IS NULL OR movement_id = :movement_id)
                    AND (:product_id IS NULL OR product_id = :product_id)
                    AND (:movement_status IS NULL OR movement_status = :movement_status)
            )
            SELECT 
                (SELECT COUNT(*) FROM filtered_movements) AS total_count,
                fm.*
            FROM filtered_movements fm
            ORDER BY movement_id ASC
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
            SELECT movement_id, product_id, origin_warehouse_id, destination_warehouse_id, 
                   sender_user_id, receiver_user_id, send_date, receive_date, 
                   movement_status, movement_description
            FROM inventory_movements
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

from sqlalchemy import text

class ModelReturn():
    @staticmethod
    def get_returns_paginated(db, limit=20, offset=0):
        query = text("""
        SELECT 
            r.return_id, 
            r.movement_detail_id, 
            p.product_id, 
            p.productname,
            r.quantity, 
            r.return_date, 
            r.notes
        FROM return r
        LEFT JOIN movementdetail md ON r.movement_detail_id = md.movement_id
        LEFT JOIN movement m ON md.movement_id = m.movement_id
        LEFT JOIN products p ON m.movement_id = p.product_id
        ORDER BY r.return_date DESC
        LIMIT :limit OFFSET :offset
    """)
        result = db.session.execute(query, {"limit": limit, "offset": offset}).mappings().fetchall()
        return [dict(row) for row in result]


    @staticmethod
    def count_returns(db):
        query = text("SELECT COUNT(*) FROM return")
        result = db.session.execute(query).scalar()
        return result

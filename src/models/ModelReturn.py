from sqlalchemy import text

class ModelReturn():
    @staticmethod
    def filter_returns(db, return_id=None, movement_detail_id=None, limit=20, offset=0):
        try:
            query = """
                SELECT 
                    r.return_id, 
                    r.movement_detail_id, 
                    p.product_id, 
                    p.productname,
                    r.quantity, 
                    r.return_date, 
                    r.notes
                FROM "return" r  -- <---- Escapamos "return" con comillas dobles
                LEFT JOIN movementdetail md ON r.movement_detail_id = md.movement_id
                LEFT JOIN movement m ON md.movement_id = m.movement_id
                LEFT JOIN products p ON m.movement_id = p.product_id
                WHERE 1=1
            """
            params = {}

            if return_id:
                query += " AND r.return_id = :return_id"
                params["return_id"] = return_id

            if movement_detail_id:
                query += " AND r.movement_detail_id = :movement_detail_id"
                params["movement_detail_id"] = movement_detail_id

            query += " ORDER BY r.return_date DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            print(f"🛠 SQL Generado: {query}")
            print(f"📊 Parámetros: {params}")

            result = db.session.execute(text(query), params).mappings().fetchall()
            return [dict(row) for row in result], len(result)

        except Exception as e:
            print(f"❌ Error filtering returns: {e}")
            return [], 0

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
            FROM "return" r  -- <---- Escapamos "return" con comillas dobles
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
        query = text('SELECT COUNT(*) FROM "return"')  # <---- Escapamos "return"
        result = db.session.execute(query).scalar()
        return result



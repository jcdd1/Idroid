from sqlalchemy import text
from .entities.product import Products


class ModelProduct():

    @staticmethod
    def get_products_paginated(db, limit, offset):
        query = text("""
            SELECT * FROM products
            LIMIT :limit OFFSET :offset
        """)
        result = db.session.execute(query, {"limit": limit, "offset": offset}).fetchall()
        # Convierte las tuplas a objetos Product
        return [
            Products(
                product_id=row[0],
                productname=row[9],
                imei=row[1],
                storage=row[2],
                battery=row[3],
                color=row[4],
                description=row[5],
                cost=row[6],
                current_status=row[7],
                acquisition_date = row[8]
            )
            for row in result
        ]


    @staticmethod
    def count_products(db):
        query = text("SELECT COUNT(*) FROM products")
        total = db.session.execute(query).scalar()
        return total
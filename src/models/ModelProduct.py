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
    
    @staticmethod
    def add_product_with_initial_movement(db, productname, imei, storage, battery, color, description, cost, warehouse_id):
        try:
            # Insert product into products table
            query_product = text("""
            INSERT INTO products (productname, imei, storage, battery, color, description, cost, current_status, acquisition_date)
            VALUES (:productname, :imei, :storage, :battery, :color, :description, :cost, 'In Warehouse', CURRENT_DATE)
            RETURNING product_id;
            """)
            result = db.session.execute(query_product, {
                'productname': productname,
                'imei': imei,
                'storage': storage,
                'battery': battery,
                'color': color,
                'description': description,
                'cost': cost
            })
            product_id = result.fetchone()[0]

            # Register initial movement in inventory_movements table
            query_movement = text("""
            INSERT INTO inventory_movements (product_id, origin_warehouse_id, destination_warehouse_id, sender_user_id, send_date, receive_date, movement_status, movement_description)
            VALUES (:product_id, :warehouse_id, :warehouse_id, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'New', 'Initial registration in warehouse');
            """)
            db.session.execute(query_movement, {
                'product_id': product_id,
                'warehouse_id': warehouse_id
            })
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error adding product: {e}")
            db.session.rollback()  # Rollback on error
            return False

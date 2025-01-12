from sqlalchemy import text
from .entities.product import Products
import datetime

class ModelProduct():

    @staticmethod
    def get_products_paginated(db, limit, offset):
        query = text("""
                SELECT 
                    p.*,
                    w.warehouse_name
                FROM 
                    products p
                JOIN 
                    (
                        SELECT 
                            product_id,
                            destination_warehouse_id,
                            MAX(receive_date) AS last_receive_date
                        FROM 
                            inventory_movements
                        WHERE 
                            receive_date IS NOT NULL
                        GROUP BY 
                            product_id, destination_warehouse_id
                    ) im ON p.product_id = im.product_id
                JOIN 
                    warehouses w ON im.destination_warehouse_id = w.warehouse_id

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
                acquisition_date=row[8][0] if isinstance(row[8], tuple) else row[8],
                warehouse_name=row[10],
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

    @staticmethod
    def filter_products(db, imei=None, productname=None, current_status=None, limit=10, offset=0):
        try:
            print(imei, " ", productname, " ", current_status)
            query = text("""
            WITH filtered_products AS (
                SELECT *
                FROM products
                WHERE 
                   
                    (:imei IS NOT NULL AND imei = :imei)

                    
                    OR (
                        :imei IS NULL 
                        AND :productname IS NOT NULL 
                        AND :current_status IS NOT NULL 
                        AND productname ILIKE :productname 
                        AND current_status = :current_status
                    )

                    
                    OR (
                        :imei IS NULL 
                        AND :productname IS NOT NULL 
                        AND productname ILIKE ':productname'
                    )

                    
                    OR (
                        :imei IS NULL 
                        AND :productname IS NULL 
                        AND :current_status IS NOT NULL 
                        AND current_status ILIKE :current_status
                    )
                )
            SELECT 
                (SELECT COUNT(*) FROM filtered_products) AS total_count,
                fp.*
            FROM filtered_products fp
            LIMIT :limit OFFSET :offset;

            """)

            params = {
                'imei': imei,
                'productname': f'%{productname}%' if productname else None,
                'current_status': f'%{current_status}%' if current_status else None,
                'limit': limit,
                'offset': offset
            }
            # Usa mappings() para obtener un diccionario
            result = db.session.execute(query, params).mappings().fetchall()
            
            # Extrae los resultados
            total_count = result[0]['total_count'] if result else 0
            products = [row for row in result]

            return products, total_count

        except Exception as e:
            print(f"Error filtering products: {e}")
            return [], 0

        



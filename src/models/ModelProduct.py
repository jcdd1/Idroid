
from sqlalchemy import text
from .entities.product import Products
import datetime

class ModelProduct():

    @staticmethod
    def get_products_paginated(db, limit, offset):
        query = text("""
            SELECT 
                p.*,  
                w.warehouse_name,
                f.document_number
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
            LEFT JOIN 
                invoice_products ip ON p.product_id = ip.product_id
            LEFT JOIN 
                invoices f ON ip.invoice_id = f.invoice_id
            LIMIT :limit OFFSET :offset;
        """)
        result = db.session.execute(query, {"limit": limit, "offset": offset}).fetchall()
        # Convierte las tuplas a objetos Product
        return [
            Products(
                product_id=row[0],
                imei=row[1],
                storage=row[2],
                battery=row[3],
                color=row[4],
                description=row[5],
                cost=row[6],
                current_status=row[7],
                acquisition_date=row[8][0] if isinstance(row[8], tuple) else row[8],
                productname=row[9],
                price=row[10],
                category=row[11],
                units = row[12],
                supplier=row[13],
                warehouse_name=row[14] if not isinstance(row[11], tuple) else row[11][0],  # Extraer de tupla si es necesario
                document_number=row[15] if not isinstance(row[12], tuple) else row[12][0]

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
    def filter_products(db, imei=None, productname=None, current_status=None, warehouse = None,category = None,limit=20, offset=0):
        # Inicializa la variable total_count
        total_count = 0
        try:

            match (imei, productname, current_status, warehouse, category):
                case (imei, _, _, _, _) if imei:
                    
                    query = text("""
                    WITH filtered_products AS (
                    SELECT
                        P.*,
                        w.warehouse_name,
                        f.document_number
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
                    LEFT JOIN 
                        invoice_products ip ON p.product_id = ip.product_id
                    LEFT JOIN 
                        invoices f ON ip.invoice_id = f.invoice_id
                    WHERE 
                        p.imei = :imei)
                    SELECT 
                        (SELECT COUNT(*) FROM filtered_products) AS total_count,
                        fp.*
                    FROM filtered_products fp
                    """)

                    params = {
                        'imei': imei
                    }

                    result = db.session.execute(query, params).mappings().fetchall()
                    
                    # Verifica si hay resultados y si el campo 'total_count' existe
                    # Verifica si result no está vacío
                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [
                            Products(
                                product_id=row['product_id'],
                                imei=row['imei'],
                                storage=row['storage'],
                                battery=row['battery'],
                                color=row['color'],
                                description=row['description'],
                                cost=row['cost'],
                                current_status=row['current_status'],
                                acquisition_date=row['acquisition_date'][0] if isinstance(row['acquisition_date'], tuple) else row['acquisition_date'],
                                productname=row['productname'],
                                price=row['price'],
                                category=row['category'],
                                units = row['units'],
                                supplier=row['supplier'],
                                warehouse_name=row['warehouse_name'] if not isinstance(row['warehouse_name'], tuple) else row['warehouse_name'][0],
                                document_number=row['document_number'] if not isinstance(row['document_number'], tuple) else row['document_number'][0]
                            )
                            for row in result
                        ]
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count
            # match (imei, productname, current_status, warehouse, category):
                case (_, productname, _, _, _) if productname:

                    query = text("""
                        WITH filtered_products AS (
                        SELECT
                            P.*,
                            w.warehouse_name,
                            f.document_number
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
                        LEFT JOIN 
                            invoice_products ip ON p.product_id = ip.product_id
                        LEFT JOIN 
                            invoices f ON ip.invoice_id = f.invoice_id
                        WHERE 
                            productname ILIKE :productname)
                        SELECT 
                            (SELECT COUNT(*) FROM filtered_products) AS total_count,
                            fp.*
                        FROM filtered_products fp
                        """)
                    
                    params = params = {'productname': f"%{productname}%"}

                    result = db.session.execute(query, params).mappings().fetchall()
                    
                    # Verifica si hay resultados y si el campo 'total_count' existe
                    # Verifica si result no está vacío
                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [
                            Products(
                                product_id=row['product_id'],
                                imei=row['imei'],
                                storage=row['storage'],
                                battery=row['battery'],
                                color=row['color'],
                                description=row['description'],
                                cost=row['cost'],
                                current_status=row['current_status'],
                                acquisition_date=row['acquisition_date'][0] if isinstance(row['acquisition_date'], tuple) else row['acquisition_date'],
                                productname=row['productname'],
                                price=row['price'],
                                category=row['category'],
                                units = row['units'],
                                supplier=row['supplier'],
                                warehouse_name=row['warehouse_name'] if not isinstance(row['warehouse_name'], tuple) else row['warehouse_name'][0],
                                document_number=row['document_number'] if not isinstance(row['document_number'], tuple) else row['document_number'][0]
                            )
                            for row in result
                        ]
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count

                case (_, _, current_status, _, _) if current_status:

                    query = text("""
                    WITH filtered_products AS (
                    SELECT
                        P.*,
                        w.warehouse_name,
                        f.document_number
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
                    LEFT JOIN 
                        invoice_products ip ON p.product_id = ip.product_id
                    LEFT JOIN 
                        invoices f ON ip.invoice_id = f.invoice_id
                    WHERE 
                        p.current_status = :current_status)
                    SELECT 
                        (SELECT COUNT(*) FROM filtered_products) AS total_count,
                        fp.*
                    FROM filtered_products fp
                    """)
                    print(current_status)
                    params = {
                        'current_status': current_status
                    }

                    result = db.session.execute(query, params).mappings().fetchall()
                    
                    # Verifica si hay resultados y si el campo 'total_count' existe
                    # Verifica si result no está vacío
                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [
                            Products(
                                product_id=row['product_id'],
                                imei=row['imei'],
                                storage=row['storage'],
                                battery=row['battery'],
                                color=row['color'],
                                description=row['description'],
                                cost=row['cost'],
                                current_status=row['current_status'],
                                acquisition_date=row['acquisition_date'][0] if isinstance(row['acquisition_date'], tuple) else row['acquisition_date'],
                                productname=row['productname'],
                                price=row['price'],
                                category=row['category'],
                                units = row['units'],
                                supplier=row['supplier'],
                                warehouse_name=row['warehouse_name'] if not isinstance(row['warehouse_name'], tuple) else row['warehouse_name'][0],
                                document_number=row['document_number'] if not isinstance(row['document_number'], tuple) else row['document_number'][0]
                            )
                            for row in result
                        ]
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count
                case (_, _, _, warehouse, _) if warehouse:
                    print(warehouse)
                    query = text("""
                    WITH filtered_products AS (
                    SELECT
                        P.*,
                        w.warehouse_name,
                        f.document_number
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
                    LEFT JOIN 
                        invoice_products ip ON p.product_id = ip.product_id
                    LEFT JOIN 
                        invoices f ON ip.invoice_id = f.invoice_id
                    WHERE 
                        w.warehouse_name = :warehouse)
                    SELECT 
                        (SELECT COUNT(*) FROM filtered_products) AS total_count,
                        fp.*
                    FROM filtered_products fp
                    """)
                    
                    params = {
                        'warehouse': warehouse
                    }

                    result = db.session.execute(query, params).mappings().fetchall()
                    
                    # Verifica si hay resultados y si el campo 'total_count' existe
                    # Verifica si result no está vacío
                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [
                            Products(
                                product_id=row['product_id'],
                                imei=row['imei'],
                                storage=row['storage'],
                                battery=row['battery'],
                                color=row['color'],
                                description=row['description'],
                                cost=row['cost'],
                                current_status=row['current_status'],
                                acquisition_date=row['acquisition_date'][0] if isinstance(row['acquisition_date'], tuple) else row['acquisition_date'],
                                productname=row['productname'],
                                price=row['price'],
                                category=row['category'],
                                units = row['units'],
                                supplier=row['supplier'],
                                warehouse_name=row['warehouse_name'] if not isinstance(row['warehouse_name'], tuple) else row['warehouse_name'][0],
                                document_number=row['document_number'] if not isinstance(row['document_number'], tuple) else row['document_number'][0]
                            )
                            for row in result
                        ]
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count 
                case (_, _, _, _, category) if category:
                    print(warehouse)
                    query = text("""
                    WITH filtered_products AS (
                    SELECT
                        P.*,
                        w.warehouse_name,
                        f.document_number
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
                    LEFT JOIN 
                        invoice_products ip ON p.product_id = ip.product_id
                    LEFT JOIN 
                        invoices f ON ip.invoice_id = f.invoice_id
                    WHERE 
                        p.category = :category)
                    SELECT 
                        (SELECT COUNT(*) FROM filtered_products) AS total_count,
                        fp.*
                    FROM filtered_products fp
                    """)
                    
                    params = {'category': f"%{category}%"}

                    result = db.session.execute(query, params).mappings().fetchall()
                    
                    # Verifica si hay resultados y si el campo 'total_count' existe
                    # Verifica si result no está vacío
                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [
                            Products(
                                product_id=row['product_id'],
                                imei=row['imei'],
                                storage=row['storage'],
                                battery=row['battery'],
                                color=row['color'],
                                description=row['description'],
                                cost=row['cost'],
                                current_status=row['current_status'],
                                acquisition_date=row['acquisition_date'][0] if isinstance(row['acquisition_date'], tuple) else row['acquisition_date'],
                                productname=row['productname'],
                                price=row['price'],
                                category=row['category'],
                                units = row['units'],
                                supplier=row['supplier'],
                                warehouse_name=row['warehouse_name'] if not isinstance(row['warehouse_name'], tuple) else row['warehouse_name'][0],
                                document_number=row['document_number'] if not isinstance(row['document_number'], tuple) else row['document_number'][0]
                            )
                            for row in result
                        ]
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count 
                case _:
                    return f"x is {imei}, y is {productname}."


            return products, total_count

        except Exception as e:
            print(f"Error filtering products: {e}")
            return [], 0

        

    @staticmethod
    def update_product(db, product_id, productname, imei, storage, battery, color, description, cost, current_status):
        try:
            query = text("""
                UPDATE products
                SET 
                    productname = :productname,
                    imei = :imei,
                    storage = :storage,
                    battery = :battery,
                    color = :color,
                    description = :description,
                    cost = :cost,
                    current_status = :current_status
                WHERE product_id = :product_id
            """)
            db.session.execute(query, {
                "productname": productname,
                "imei": imei,
                "storage": storage,
                "battery": battery,
                "color": color,
                "description": description,
                "cost": cost,
                "current_status": current_status,
                "product_id": product_id
            })
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False
       
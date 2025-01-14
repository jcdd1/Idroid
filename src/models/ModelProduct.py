
from sqlalchemy import text
from .entities.product import Products
from .queries.sql_queries import SQLQueries
import datetime

class ModelProduct():

    @staticmethod
    def get_product_full_info(db, limit, offset):
        query = text(SQLQueries.get_all_products_query())
        result = db.session.execute(query, {"limit": limit, "offset": offset}).mappings().all()
        return [dict(row) for row in result]

    @staticmethod
    def count_products(db):
        query = text(SQLQueries.count_products_query())
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
                    print(imei)
                    query = text(SQLQueries.filter_products_imei())
                    params = {
                        'imei': imei
                    }

                    result = db.session.execute(query, params).mappings().fetchall()

                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [dict(row) for row in result]
                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count
                
                case (_, productname, current_status, warehouse, category) if productname and current_status and warehouse and category:
                    query = text(SQLQueries.filter_products_all_fields())
                    
                    params = params = {'productname': f"%{productname}%", 
                                       'current_status': current_status,
                                       'warehouse': warehouse,
                                       'category': f"%{category}%"
                                       }

                    result = db.session.execute(query, params).mappings().fetchall()

                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [dict(row) for row in result]
                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count
           
                case (_, productname, current_status, warehouse, _) if productname and current_status and warehouse:
                    query = text(SQLQueries.filter_products_no_category())
                    
                    params = params = {'productname': f"%{productname}%", 
                                       'current_status': current_status,
                                       'warehouse': warehouse
                                       }
                    result = db.session.execute(query, params).mappings().fetchall()

                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [dict(row) for row in result]
                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count

                case (_, productname, current_status, _, category) if productname and current_status and category:
                    query = text(SQLQueries.filter_products_no_warehouse())
                    
                    params = params = {'productname': f"%{productname}%", 
                                       'current_status': current_status,
                                       'category': f"%{category}%"
                                       }
                    result = db.session.execute(query, params).mappings().fetchall()

                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [dict(row) for row in result]
                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count
                
                case (_, productname, _, warehouse, category) if productname and warehouse and category:
                    
                    query = text(SQLQueries.filter_products_no_status())
                    
                    params = params = {'productname': f"%{productname}%", 
                                       'warehouse': warehouse,
                                       'category': f"%{category}%"
                                       }
                    result = db.session.execute(query, params).mappings().fetchall()

                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [dict(row) for row in result]
                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count
                
                case (_, _, current_status, warehouse, category) if current_status and warehouse and category:
                    query = text(SQLQueries.filter_products_no_product())
                    
                    params = params = {'current_status': current_status,
                                       'warehouse': warehouse,
                                       'category': f"%{category}%"
                                       }

                    result = db.session.execute(query, params).mappings().fetchall()

                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [dict(row) for row in result]
                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count
                
                case (_, productname, current_status, _, _) if productname and current_status:
                    
                    query = text(SQLQueries.filter_products_name_status())
                    
                    params = params = {'productname': f"%{productname}%", 
                                       'current_status': current_status
                                       }
                    result = db.session.execute(query, params).mappings().fetchall()

                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [dict(row) for row in result]
                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count
                
                case (_, productname, _, warehouse, _) if productname  and warehouse:
                    query = text(SQLQueries.filter_products_name_warehouse())
                    
                    params = params = {'productname': f"%{productname}%",
                                       'warehouse': warehouse
                                       }

                    result = db.session.execute(query, params).mappings().fetchall()

                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [dict(row) for row in result]
                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count
                
                case (_, _, current_status, _, category) if current_status and category:
                    query = text(SQLQueries.filter_products_status_category())
                    
                    params = params = {'current_status': current_status,
                                       'category': f"%{category}%"
                                       }

                    result = db.session.execute(query, params).mappings().fetchall()

                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [dict(row) for row in result]
                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count

                case (_, _, _, warehouse, category) if warehouse and category:
                    query = text(SQLQueries.filter_products_warehouse_category())
                    
                    params = params = {'warehouse': warehouse,
                                       'category': f"%{category}%"
                                       }

                    result = db.session.execute(query, params).mappings().fetchall()

                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [dict(row) for row in result]
                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count
                
                case (_, productname, _, _, _) if productname:

                    query = text(SQLQueries.filter_products_name())
                    
                    params = params = {'productname': f"%{productname}%"}

                    result = db.session.execute(query, params).mappings().fetchall()

                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [dict(row) for row in result]
                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count

                case (_, _, current_status, _, _) if current_status:

                    query = text(SQLQueries.filter_products_status())
                    print(current_status)
                    params = {
                        'current_status': current_status
                    }

                    result = db.session.execute(query, params).mappings().fetchall()
                    
                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [dict(row) for row in result]
                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count
                 
                case (_, _, _, warehouse, _) if warehouse:
                    print(warehouse)
                    query = text(SQLQueries.filter_products_warehouse())
                    
                    params = {
                        'warehouse': warehouse
                    }

                    result = db.session.execute(query, params).mappings().fetchall()
                    
                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [dict(row) for row in result]
                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count
                
                case (_, _, _, _, category) if category:
                    print(warehouse)
                    query = text(SQLQueries.filter_products_category())
                    
                    params = {'category': f"%{category}%"}

                    result = db.session.execute(query, params).mappings().fetchall()
                    
                    if result and 'total_count' in result[0]:
                        # Convierte el RowMapping a un diccionario
                        row_dict = dict(result[0])
                        
                        # Captura el valor de 'total_count'
                        total_count = row_dict.pop('total_count')
                        
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [dict(row) for row in result]
                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products, total_count
                case _:
                    products = []
                    return products, 0
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
       
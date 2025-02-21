from sqlalchemy import text
from .entities.product import Products
from .queries.sql_queries import SQLQueries
import datetime
import pandas as pd

class ModelProduct():


    @staticmethod
    def update_units(db, imei, amount):
            try:
                # Actualizar las unidades del producto
                query = text("""
                    UPDATE products
                    SET units = units + :amount
                    WHERE imei = :imei
                    RETURNING units
                """)
                result = db.session.execute(query, {'amount': amount, 'imei': imei})
                updated_units = result.fetchone()

                if updated_units:
                    db.session.commit()
                    return {"success": True, "new_units": updated_units[0]}
                else:
                    return {"success": False, "error": "Producto no encontrado"}

            except Exception as e:
                db.session.rollback()
                return {"success": False, "error": str(e)}

    @staticmethod
    def update_status(db, imei, new_status):
        try:
            # Actualización del estado con sintaxis corregida
            query = text("""
                UPDATE products 
                SET current_status = :new_status 
                WHERE imei = :imei
            """)
            result = db.session.execute(query, {'imei': imei, 'new_status': new_status})
            db.session.commit()

            # Verificar si algún registro fue actualizado
            if result.rowcount > 0:
                return {"success": True}
            else:
                return {"success": False, "error": "Producto no encontrado"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_products_units(db, warehouse_id):
        try:
            query = text(SQLQueries.get_products_units())
            result = db.session.execute(query, {'warehouse_id': warehouse_id}).mappings().all()

            result = [dict(row) for row in result]
            # df = pd.DataFrame(result)
            # filtered_df = df.loc[df.groupby('product_id')['units'].idxmax()]
            #     # Convertir a lista de diccionarios
            # filtered_data = filtered_df.to_dict(orient="records")
            return result
        except Exception as e:
            print(f"Error adding product: {e}")
            db.session.rollback()  # Rollback on error
            return False
    @staticmethod
    def add_product_with_initial_movement(db, productname, imei, storage, battery, color, description, 
                                          cost, category, units, supplier, warehouse_id, current_user):
        try:
            # Insert product into products table
            query_1, query_2, query_3, query_4 = SQLQueries.add_product_with_initial_movement_query()

            query_product = text(query_1)
            result = db.session.execute(query_product, {
                'productname': productname,
                'imei': imei,
                'storage': storage,
                'battery': battery,
                'color': color,
                'description': description,
                'cost': cost,
                'category': category,
                'units': units,
                'supplier': supplier
            })
            product_id = result.fetchone()[0]

            
            query_stock = text(query_2)

            db.session.execute(query_stock, {
                'warehouse_id': warehouse_id,
                'product_id': product_id,
                'units': units
            })
            
            # Crear movimientos iniciales
            query_movement = text(query_3)

            result = db.session.execute(query_movement, {
                'warehouse_id': warehouse_id,
                'current_user': current_user
            })

            movement_id = result.fetchone()[0]

            # Register initial movement in inventory_movements table
            query_movement_detail = text(query_4)
            db.session.execute(query_movement_detail, {
                'product_id': product_id,
                'movement_id': movement_id,
                'units': units
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
                    
                    query = text(SQLQueries.filter_products_imei())
                    params = {
                        'imei': imei
                    }

                    result = db.session.execute(query, params).mappings().fetchall()

                    if result:                       
                        # Construye la lista de productos excluyendo 'total_count'
                        products = [dict(row) for row in result]
                                              
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products
                
                case (_, productname, current_status, warehouse, category) if productname and current_status and warehouse and category:
                    query = text(SQLQueries.filter_products_all_fields())
                    
                    params = params = {'productname': f"%{productname}%", 
                                       'current_status': current_status,
                                       'warehouse': warehouse,
                                       'category': f"%{category}%"
                                       }

                    result = db.session.execute(query, params).mappings().fetchall()
                    
                    if result:
                        products = [dict(row) for row in result]                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products
           
                case (_, productname, current_status, warehouse, _) if productname and current_status and warehouse:
                    query = text(SQLQueries.filter_products_no_category())
                    
                    params = params = {'productname': f"%{productname}%", 
                                       'current_status': current_status,
                                       'warehouse': warehouse
                                       }
                    result = db.session.execute(query, params).mappings().fetchall()
                    if result:
                        products = [dict(row) for row in result]                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products

                case (_, productname, current_status, _, category) if productname and current_status and category:
                    query = text(SQLQueries.filter_products_no_warehouse())
                    
                    params = params = {'productname': f"%{productname}%", 
                                       'current_status': current_status,
                                       'category': f"%{category}%"
                                       }
                    result = db.session.execute(query, params).mappings().fetchall()

                    if result:
                        products = [dict(row) for row in result]                       
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products
                
                case (_, productname, _, warehouse, category) if productname and warehouse and category:
                    
                    query = text(SQLQueries.filter_products_no_status())
                    
                    params = params = {'productname': f"%{productname}%", 
                                       'warehouse': warehouse,
                                       'category': f"%{category}%"
                                       }
                    result = db.session.execute(query, params).mappings().fetchall()

                    if result:
                        products = [dict(row) for row in result]
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products
                
                case (_, _, current_status, warehouse, category) if current_status and warehouse and category:
                    query = text(SQLQueries.filter_products_no_product())
                    
                    params = params = {'current_status': current_status,
                                       'warehouse': warehouse,
                                       'category': f"%{category}%"
                                       }

                    result = db.session.execute(query, params).mappings().fetchall()
                    if result:
                        products = [dict(row) for row in result]                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products
                
                case (_, productname, current_status, _, _) if productname and current_status:
                    
                    query = text(SQLQueries.filter_products_name_status())
                    
                    params = params = {'productname': f"%{productname}%", 
                                       'current_status': current_status
                                       }
                    result = db.session.execute(query, params).mappings().fetchall()
                    if result:
                        products = [dict(row) for row in result]
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products
                
                case (_, productname, _, warehouse, _) if productname  and warehouse:
                    query = text(SQLQueries.filter_products_name_warehouse())
                    
                    params = params = {'productname': f"%{productname}%",
                                       'warehouse': warehouse
                                       }

                    result = db.session.execute(query, params).mappings().fetchall()

                    if result:
                        products = [dict(row) for row in result]                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products
                
                case (_, _, current_status, _, category) if current_status and category:
                    query = text(SQLQueries.filter_products_status_category())
                    
                    params = params = {'current_status': current_status,
                                       'category': f"%{category}%"
                                       }

                    result = db.session.execute(query, params).mappings().fetchall()

                    if result:
                        products = [dict(row) for row in result]                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products

                case (_, _, _, warehouse, category) if warehouse and category:
                    query = text(SQLQueries.filter_products_warehouse_category())
                    
                    params = params = {'warehouse': warehouse,
                                       'category': f"%{category}%"
                                       }

                    result = db.session.execute(query, params).mappings().fetchall()

                    if result:
                        products = [dict(row) for row in result]                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products
                
                case (_, productname, _, _, _) if productname:

                    query = text(SQLQueries.filter_products_name())
                    
                    params = params = {'productname': f"%{productname}%"}

                    result = db.session.execute(query, params).mappings().fetchall()

                    if result:
                        products = [dict(row) for row in result]
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products

                case (_, _, current_status, _, _) if current_status:

                    query = text(SQLQueries.filter_products_status())
                    
                    params = {
                        'current_status': current_status
                    }

                    result = db.session.execute(query, params).mappings().fetchall()
                    
                    if result:
                        products = [dict(row) for row in result]                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products
                 
                case (_, _, _, warehouse, _) if warehouse:
                    
                    query = text(SQLQueries.filter_products_warehouse())
                    
                    params = {
                        'warehouse': warehouse
                    }

                    result = db.session.execute(query, params).mappings().fetchall()
                    if result:
                        products = [dict(row) for row in result]                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products
                
                case (_, _, _, _, category) if category:
                    
                    query = text(SQLQueries.filter_products_category())
                    
                    params = {'category': f"%{category}%"}

                    result = db.session.execute(query, params).mappings().fetchall()
                    
                    if result:
                        products = [dict(row) for row in result]
                        df = pd.DataFrame(result)
                        filtered_df = df.loc[df.groupby('product_id')['units'].idxmax()]
                            # Convertir a lista de diccionarios
                        filtered_data = filtered_df.to_dict(orient="records")
                        products = filtered_data 
                        
                    else:
                        products = []  # Si no hay resultados, inicializa la lista vacía
                    return products
                case _:
                    products = []
                    return products, 0
            return products, 0

        except Exception as e:
            print(f"Error filtering products: {e}")
            return [], 0
        
    @staticmethod
    def get_product_imei(db, imei):
        try:
            query = text(SQLQueries.get_product_imei())
            params = {
                'imei': imei
            }

            result = db.session.execute(query, params).mappings().fetchall()

            if result:                       
                # Construye la lista de productos excluyendo 'total_count'
                products = [dict(row) for row in result]
                                        
            else:
                products = []  # Si no hay resultados, inicializa la lista vacía
            return products
        except Exception as e:
            print(f"Error searching products: {e}")


    @staticmethod
    def update_product(db, product_id, productname, imei, storage, battery, color, description, cost, 
                       category, units, supplier, current_user, warehouse_id):
    
        try:
            query, query_2, query_3 = text(SQLQueries.update_product_query())
            params = {
                    "productname": productname,
                    "imei": imei,
                    "storage": storage,
                    "battery": battery,
                    "color": color,
                    "description": description,
                    "cost": cost,
                    "category": category,
                    "units": units,
                    "supplier": supplier,
                    "product_id": product_id
                    }
            db.session.execute(query, params)

            query_movement = text(query_2)

            result = db.session.execute(query_movement, {
                'warehouse_id': warehouse_id,
                'current_user': current_user
            })

            movement_id = result.fetchone()[0]

            # Register initial movement in inventory_movements table
            query_movement_detail = text(query_3)
            db.session.execute(query_movement_detail, {
                'product_id': product_id,
                'movement_id': movement_id
            })
            db.session.commit()

            return True
        except Exception as e:
            db.session.rollback()
            return False
       
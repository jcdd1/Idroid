from sqlalchemy import text
from .entities.product import Products
from .queries.sql_queries import SQLQueries
import datetime
import pandas as pd

class ModelProduct():

    @staticmethod
    def get_product_id_by_imei(db, imei):
        try:
            query = text("""
                SELECT product_id FROM products WHERE imei = :imei
            """)

            result = db.session.execute(query, {"imei": imei}).fetchone()
            
            return result[0] if result else None  # Retorna el product_id si existe
        except Exception as e:
            print(f"❌ Error al obtener product_id por IMEI: {e}")
            return None



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
    def get_products_units_ws(db, warehouse_id):
        try:
            query = text(SQLQueries.get_products_units_ws())
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
    def get_units_product(db, product_id, warehouse_id):
        try:
            query = text(SQLQueries.get_units_product_query())
            result = db.session.execute(query, {'warehouse_id': warehouse_id, 'product_id': product_id}).mappings().all()

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
            print(productname)
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
    def filter_products(db, imei=None, productname=None, current_status=None, warehouse=None, category=None, limit=20, offset=0):
        try:
            # Caso de filtrado por IMEI
            if imei:
                query = text("""
                    SELECT p.*, w.warehouse_name, w.warehouse_id,
                        (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transfer' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    LEFT JOIN movementdetail md ON md.product_id = p.product_id AND md.status = 'Transfer'
                    WHERE p.imei = '355237865723042'
                    GROUP BY p.product_id, w.warehouse_id, ws.units
                    HAVING (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transfer' THEN md.quantity ELSE 0 END), 0)) > 0
                    LIMIT :limit OFFSET :offset
                """)
                params = {'imei': imei, 'limit': limit, 'offset': offset}

            # Caso: filtrado por nombre del producto, estado, bodega y categoría
            elif productname and current_status and warehouse and category:
                query = text("""
                    SELECT p.*, w.warehouse_name, w.warehouse_id, ws.units AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    WHERE p.productname ILIKE :productname
                    AND p.current_status = :current_status
                    AND w.warehouse_name ILIKE :warehouse
                    AND p.category ILIKE :category
                    LIMIT :limit OFFSET :offset
                """)
                params = {
                    'productname': f"%{productname}%",
                    'current_status': current_status,
                    'warehouse': f"%{warehouse}%",
                    'category': f"%{category}%",
                    'limit': limit,
                    'offset': offset
                }

            # Caso: filtrado solo por bodega
            elif warehouse:
                query = text("""
                    SELECT p.*, w.warehouse_name, w.warehouse_id,
                        (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transfer' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    LEFT JOIN movementdetail md ON md.product_id = p.product_id AND md.status = 'Transfer'
                    WHERE w.warehouse_name ILIKE :warehouse
                    GROUP BY p.product_id, w.warehouse_id, ws.units
                    HAVING (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transfer' THEN md.quantity ELSE 0 END), 0)) > 0
                    LIMIT :limit OFFSET :offset
                """)
                params = {
                    'warehouse': f"%{warehouse}%",
                    'limit': limit,
                    'offset': offset
                }

            # Caso: filtrado solo por nombre de producto
            elif productname:
                query = text("""
                    SELECT p.*, w.warehouse_name, w.warehouse_id, ws.units AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    WHERE p.productname ILIKE :productname
                    LIMIT :limit OFFSET :offset
                """)
                params = {
                    'productname': f"%{productname}%",
                    'limit': limit,
                    'offset': offset
                }

            # Caso: filtrado solo por categoría
            elif category:
                query = text("""
                    SELECT p.*, w.warehouse_name, w.warehouse_id,
                        (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transfer' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    LEFT JOIN movementdetail md ON md.product_id = p.product_id AND md.status = 'Transfer'
                    WHERE p.category ILIKE :category
                    GROUP BY p.product_id, w.warehouse_id, ws.units
                    HAVING (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transfer' THEN md.quantity ELSE 0 END), 0)) > 0
                    LIMIT :limit OFFSET :offset
                """)
                params = {
                    'category': f"%{category}%",
                    'limit': limit,
                    'offset': offset
                }

            # Caso: filtrado solo por estado
            elif current_status:
                query = text("""
                    SELECT p.*, w.warehouse_name, w., ws.units AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    WHERE p.current_status = :current_status
                    LIMIT :limit OFFSET :offset
                """)
                params = {
                    'current_status': current_status,
                    'limit': limit,
                    'offset': offset
                }

            # Si no se aplican filtros, devuelve todos los productos con paginación
            else:
                query = text("""
                    SELECT p.*, w.warehouse_name, w.warehouse_id, ws.units AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    LIMIT :limit OFFSET :offset
                """)
                params = {
                    'limit': limit,
                    'offset': offset
                }

            # Ejecutar la consulta
            result = db.session.execute(query, params).mappings().fetchall()

            # Procesar resultados
            if result:
                products = [dict(row) for row in result]
            else:
                products = []

            return products

        except Exception as e:
            print(f"⚠️ Error filtering products: {e}")
            return []

        
    @staticmethod
    def get_product_imei(db, imei):
        try:
            print(f" IMEI recibido (sin procesar): '{imei}'")

            # Limpieza del IMEI robusta
            imei = imei.encode('utf-8', 'ignore').decode('utf-8-sig').strip().replace('\ufeff', '')
            print(f" IMEI después de limpieza avanzada: '{imei}'")

            query = text("""
                SELECT p.product_id, p.productname, p.storage, p.battery, p.color, p.units, ws.warehouse_id
                FROM products p
                LEFT JOIN warehousestock ws ON p.product_id = ws.product_id
                WHERE TRIM(BOTH FROM p.imei) = :imei
            """)
            params = {'imei': imei}

            result = db.session.execute(query, params).mappings().fetchall()

            print(f" Resultado de búsqueda para IMEI '{imei}': {result}")

            return [dict(row) for row in result] if result else []
        except Exception as e:
            print(f" Error searching products: {e}")
            return []


    @staticmethod
    def update_product(db, product_id, productname, imei, storage, battery, color, description, cost, 
                    category, units, supplier, current_user_id, warehouse_id):
        
        try:
            # Obtener las tres consultas de SQL
            queries = SQLQueries.update_product_query()

            if len(queries) != 3:
                raise ValueError("Error en SQLQueries.update_product_query(), se esperaban 3 queries.")

            query, query_2, query_3 = map(text, queries)

            # Actualizar el producto
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

            # Registrar el movimiento en la bodega
            result = db.session.execute(query_2, {
                'warehouse_id': warehouse_id,
                'current_user': current_user_id
            })

            # Verificar si se obtuvo un movement_id
            movement_row = result.fetchone()
            if movement_row is None:
                raise ValueError("No se pudo obtener el ID del movimiento.")

            movement_id = movement_row[0]

            # Registrar el detalle del movimiento
            db.session.execute(query_3, {
                'product_id': product_id,
                'movement_id': movement_id
            })

            # Confirmar transacción
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Error al actualizar el producto: {e}")
            return False

       
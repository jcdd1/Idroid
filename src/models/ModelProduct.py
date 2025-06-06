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
    def update_units(db, imei, amount, warehouse_id):
        try:
            # 1️⃣ **Actualizar las unidades del producto en products**
            query_1 = text("""
                UPDATE products
                SET units = units + :amount
                WHERE imei = :imei
                RETURNING units
            """)
            result_1 = db.session.execute(query_1, {'amount': amount, 'imei': imei})
            updated_units = result_1.fetchone()

            if updated_units:
                # 2️⃣ **Actualizar las unidades en warehousestock**
                query_2 = text("""
                    UPDATE warehousestock
                    SET units = units + :amount
                    WHERE product_id = (SELECT product_id FROM products WHERE imei = :imei)
                    AND warehouse_id = :warehouse_id
                    RETURNING units
                """)
                result_2 = db.session.execute(query_2, {'amount': amount, 'imei': imei, 'warehouse_id': warehouse_id})
                updated_units = result_2.fetchone()

                if updated_units:
                    # Si ambos updates son exitosos, hacer commit
                    db.session.commit()
                    return {"success": True, "new_units": updated_units[0], "new_units": updated_units[0]}
                else:
                    db.session.rollback()
                    return {"success": False, "error": "No se pudo actualizar el stock en el almacén"}
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
            print(f"Producto ID recibido: {product_id}, Bodega ID recibido: {warehouse_id}")

            # Consulta SQL para obtener las unidades disponibles del producto en la bodega especificada
            query = text("""
                SELECT p.product_id, p.productname, p.storage, p.battery, p.color, p.units, ws.warehouse_id,
                    (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible
                FROM products p
                LEFT JOIN warehousestock ws ON p.product_id = ws.product_id
                LEFT JOIN movementdetail md ON md.product_id = p.product_id AND md.status = 'Transferencia'
                WHERE p.product_id = :product_id AND ws.warehouse_id = :warehouse_id
                GROUP BY p.product_id, p.productname, p.storage, p.battery, p.color, ws.units, ws.warehouse_id
            """)

            # Parámetros de la consulta
            params = {'product_id': product_id, 'warehouse_id': warehouse_id}

            # Ejecutar la consulta
            result = db.session.execute(query, params).mappings().fetchall()


            # Verificar si se obtuvieron resultados y devolver el stock disponible
            return [dict(row) for row in result] if result else []

        except Exception as e:
            print(f"❌ Error al obtener las unidades: {e}")
            return []



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
    def count_products_in_warehouse(db, warehouse_id):
        query = text("""
                SELECT COUNT(*) 
                FROM (
                     SELECT p.*, w.warehouse_name, w.warehouse_id,
                            (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible
                        FROM products p
                        JOIN warehousestock ws ON p.product_id = ws.product_id
                        JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                        LEFT JOIN movementdetail md ON md.product_id = p.product_id AND md.status = 'Transferencia'
                        WHERE ws.warehouse_id = :warehouse_id
                        GROUP BY p.product_id, w.warehouse_id, ws.units
                        HAVING (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) > 0)
                     """)
        result = db.session.execute(query, {"warehouse_id": warehouse_id}).scalar()
        return result if result else 0

    @staticmethod
    def get_products_in_warehouse_paginated(db, warehouse_id, user_warehouse_id):
        query = text("""
            SELECT p.*, w.warehouse_name, w.warehouse_id,
                    (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible
                FROM products p
                JOIN warehousestock ws ON p.product_id = ws.product_id
                JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                LEFT JOIN movementdetail md ON md.product_id = p.product_id AND md.status = 'Transferencia'
                WHERE ws.warehouse_id = :warehouse_id
                GROUP BY p.product_id, w.warehouse_id, ws.units
                HAVING (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) > 0
        """)
        result = db.session.execute(query, {
            "warehouse_id": warehouse_id
        }).mappings().fetchall()

        products = [dict(row) for row in result] if result else []

        # 🔹 Bloquear productos que no están en la bodega del usuario
        for product in products:
            product["user_has_access"] = (product["warehouse_id"] == user_warehouse_id)

        return products




    @staticmethod
    def count_all_products(db):
        query = text("SELECT COUNT(*) FROM products;")
        result = db.session.execute(query).scalar()
        return result

    @staticmethod
    def count_filtered_products(db, imei=None, productname=None, current_status=None, warehouse=None, category=None):
        try:
            # Base de la consulta de conteo
            query = text("""
                SELECT COUNT(*) 
                FROM (
                    SELECT p.*, w.warehouse_name, w.warehouse_id,
                            (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible
                        FROM products p
                        JOIN warehousestock ws ON p.product_id = ws.product_id
                        JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                        LEFT JOIN movementdetail md ON md.product_id = p.product_id AND md.status = 'Transferencia'
                        WHERE """)
            params = {}

            # Aplicar filtros opcionales
            if imei:
                query = text(str(query) + " p.imei = :imei ")
                params["imei"] = imei
            elif productname and warehouse:
                query = text(str(query) + " p.productname ILIKE :productname AND w.warehouse_name ILIKE :warehouse ")
                params["productname"] = f"%{productname}%"
                params["warehouse"] = f"%{warehouse}%"
            elif productname and current_status:
                query = text(str(query) + " p.productname ILIKE :productname AND p.current_status = :current_status ")
                params["productname"] = f"%{productname}%"
                params["current_status"] = current_status
            elif productname and current_status and warehouse and category:
                query = text(str(query) + " p.productname ILIKE :productname AND p.current_status = :current_status AND w.warehouse_name ILIKE :warehouse AND p.category ILIKE :category ")
                params["productname"] = f"%{productname}%"
                params["current_status"] = current_status
                params["warehouse"] = f"%{warehouse}%"
                params["category"] = f"%{category}%"
            elif productname and current_status and warehouse:
                query = text(str(query) + " p.productname ILIKE :productname AND p.current_status = :current_status AND w.warehouse_name ILIKE :warehouse ")
                params["productname"] = f"%{productname}%"
                params["current_status"] = current_status
                params["warehouse"] = f"%{warehouse}%"
            elif warehouse and current_status:
                query = text(str(query) + " w.warehouse_name ILIKE :warehouse AND p.current_status = :current_status")
            elif category:
                query = text(str(query) + "p.category ILIKE :category ")
                params["category"] = f"%{category}%"
            elif warehouse:
                query = text(str(query) + " w.warehouse_name ILIKE :warehouse ")
                params["warehouse"] = f"%{warehouse}%"
            elif productname:
                query = text(str(query) + " p.productname ILIKE :productname ")
                params["productname"] = f"%{productname}%"
                
            elif category:
                query = text(str(query) + " p.category ILIKE :category ")
                params["category"] = f"%{category}%"
            
            elif current_status:
                query = text(str(query) + " p.current_status = :current_status ")
                params["current_status"] = current_status

            query = text(str(query) + """ GROUP BY p.product_id, w.warehouse_id, ws.units
                    HAVING (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) > -1
                    ) AS resultado""")
            # Ejecutar la consulta

                
            print(query)
            result = db.session.execute(query, params).scalar()

            return result if result else 0

        except Exception as e:
            print(f"⚠️ Error counting products: {e}")
            return 0




    @staticmethod
    def filter_products(db, imei=None, productname=None, current_status=None, warehouse=None, category=None, user_warehouse_id=None):
        try:
            # Caso de filtrado por IMEI
            if current_status == 'Sold':
                units_min = -1
            else:
                units_min = 0

            if imei:
                query = text("""
                    SELECT p.*, w.warehouse_name, w.warehouse_id,
                        (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    LEFT JOIN movementdetail md ON md.product_id = p.product_id AND md.status = 'Transferencia'
                    WHERE p.imei ILIKE :imei
                    GROUP BY p.product_id, w.warehouse_id, ws.units
                    HAVING (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) > -1
                """)
                params = {'imei': imei}

            elif productname and warehouse:
                query = text("""
                    SELECT p.*, w.warehouse_name, w.warehouse_id,
                        (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    LEFT JOIN movementdetail md ON md.product_id = p.product_id AND md.status = 'Transferencia'
                    WHERE p.productname ILIKE :productname
                    AND w.warehouse_name ILIKE :warehouse 
                    GROUP BY p.product_id, w.warehouse_id, ws.units
                    HAVING (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) > 0
                """)
                params = {
                    'productname': f"%{productname}%",
                    'warehouse': f"%{warehouse}%"
                }

            elif productname and current_status:
                query = text("""
                    SELECT p.*, w.warehouse_name, w.warehouse_id,
                        (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    LEFT JOIN movementdetail md ON md.product_id = p.product_id AND md.status = 'Transferencia'
                    WHERE p.productname ILIKE :productname
                    AND p.current_status = :current_status
                    GROUP BY p.product_id, w.warehouse_id, ws.units
                    HAVING (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) > :units_min
                """)
                params = {
                    'productname': f"%{productname}%",
                    'current_status': current_status,
                    'units_min': units_min
                }
                
            elif warehouse and current_status:
                query = text("""
                    SELECT p.*, w.warehouse_name, w.warehouse_id,
                        (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    LEFT JOIN movementdetail md ON md.product_id = p.product_id AND md.status = 'Transferencia'
                    WHERE w.warehouse_name ILIKE :warehouse
                    AND p.current_status = :current_status
                    GROUP BY p.product_id, w.warehouse_id, ws.units
                    HAVING (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) > :units_min
                """)
                params = {
                    'productname': f"%{productname}%",
                    'current_status': current_status,
                    'units_min': units_min
                }

            elif warehouse:
                query = text("""
                    SELECT p.*, w.warehouse_name, w.warehouse_id,
                        (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    LEFT JOIN movementdetail md ON md.product_id = p.product_id AND md.status = 'Transferencia'
                    WHERE w.warehouse_name ILIKE :warehouse
                    GROUP BY p.product_id, w.warehouse_id, ws.units
                    HAVING (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) > 0
                """)
                params = {
                    'warehouse': f"%{warehouse}%"
                }

            elif productname:
                query = text("""
                    SELECT p.*, w.warehouse_name, w.warehouse_id,
                        (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    LEFT JOIN movementdetail md ON md.product_id = p.product_id AND md.status = 'Transferencia'
                    WHERE p.productname ILIKE :productname
                    GROUP BY p.product_id, w.warehouse_id, ws.units
                    HAVING (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) > 0
                """)
                params = {
                    'productname': f"%{productname}%"
                }

            elif category:
                query = text("""
                    SELECT p.*, w.warehouse_name, w.warehouse_id,
                        (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    LEFT JOIN movementdetail md ON md.product_id = p.product_id AND md.status = 'Transferencia'
                    WHERE p.category ILIKE :category
                    GROUP BY p.product_id, w.warehouse_id, ws.units
                    HAVING (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) > 0
                """)
                params = {
                    'category': f"%{category}%"
                }

            elif current_status:
                query = text("""
                    SELECT p.*, w.warehouse_name, w.warehouse_id,
                        (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    LEFT JOIN movementdetail md ON md.product_id = p.product_id AND md.status = 'Transferencia'
                    WHERE p.current_status = :current_status
                    GROUP BY p.product_id, w.warehouse_id, ws.units
                    HAVING (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transferencia' THEN md.quantity ELSE 0 END), 0)) > :units_min
                """)
                params = {
                    'current_status': current_status,
                    'units_min': units_min
                }

            else:
                query = text("""
                    SELECT p.*, w.warehouse_name, w.warehouse_id, ws.units AS stock_disponible
                    FROM products p
                    JOIN warehousestock ws ON p.product_id = ws.product_id
                    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
                    WHERE ws.warehouse_id = :warehouse_id
                    ORDER BY p.product_id
                """)
                params = {}

            # Ejecutar la consulta
            result = db.session.execute(query, params).mappings().fetchall()

            # Procesar resultados
            if result:
                products = [dict(row) for row in result]
            else:
                products = []

            # 🔹 Verificar si el usuario tiene acceso a los productos
            for product in products:
                product["user_has_access"] = (product["warehouse_id"] == user_warehouse_id)

            return products

        except Exception as e:
            print(f"⚠️ Error filtering products: {e}")
            return []


        

    @staticmethod
    def get_product_imei(db, imei, warehouse_id):  # ✅ Se recibe warehouse_id como parámetro
        try:
            print(f" IMEI recibido (sin procesar): '{imei}'")

            # Limpieza del IMEI robusta
            imei = imei.encode('utf-8', 'ignore').decode('utf-8-sig').strip().replace('\ufeff', '')
            print(f" IMEI después de limpieza avanzada: '{imei}'")

            query = text("""
                SELECT 
                    p.product_id, 
                    p.productname, 
                    p.storage, 
                    p.battery, 
                    p.color, 
                    ws.units AS units,      -- ✅ Stock de la bodega específica
                    ws.warehouse_id
                FROM products p
                JOIN warehousestock ws ON p.product_id = ws.product_id
                WHERE TRIM(BOTH FROM p.imei) = :imei
                  AND ws.warehouse_id = :warehouse_id  -- ✅ Filtra por la bodega del usuario
            """)
            params = {
                'imei': imei,
                'warehouse_id': warehouse_id
            }

            result = db.session.execute(query, params).mappings().fetchall()
            print(f" Resultado de búsqueda para IMEI '{imei}': {result}")

            return [dict(row) for row in result] if result else []
        except Exception as e:
            print(f"❌ Error searching products: {e}")
            return []



    @staticmethod
    def update_product(db, product_id, productname, imei, storage, battery, color, description, cost, 
                    category, units, supplier, current_user_id, warehouse_id, current_status):

        try:
            queries = SQLQueries.update_product_query()

            if len(queries) != 4:
                raise ValueError("Error en SQLQueries.update_product_query(), se esperaban 4 queries.")

            query, query_2, query_3, query_4 = map(text, queries)

            # 1️⃣ **Actualizar `products` con estado**
            db.session.execute(query, {
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
                "current_status": current_status,  # ⬅️ Pasar el estado a la consulta
                "product_id": product_id
            })

            # 2️⃣ **Registrar el movimiento en `Movement`**
            result = db.session.execute(query_2, {
                'warehouse_id': warehouse_id,
                'current_user': current_user_id
            })

            movement_row = result.fetchone()
            if movement_row is None:
                raise ValueError("No se pudo obtener el ID del movimiento.")

            movement_id = movement_row[0]

            # 3️⃣ **Registrar el detalle del movimiento en `MovementDetail`**
            db.session.execute(query_3, {
                'product_id': product_id,
                'movement_id': movement_id
            })

            # 4️⃣ **Actualizar la cantidad en `warehousestock`**
            db.session.execute(query_4, {
                "units": units,
                "product_id": product_id,
                "warehouse_id": warehouse_id
            })

            db.session.commit()
            print(f"✅ Producto {product_id} actualizado correctamente con estado {current_status}")

            return True

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al actualizar el producto: {e}")
            return False


       
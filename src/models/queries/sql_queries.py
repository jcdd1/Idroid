class SQLQueries:
    @staticmethod
    def get_products_units_ws():
        query = """
            SELECT  
                p.*,
                w.warehouse_name,
                w.warehouse_id,
                ws.units AS stock_disponible
            FROM 
                warehousestock ws
            JOIN 
                warehouses w ON ws.warehouse_id = w.warehouse_id
            JOIN 
                products p ON ws.product_id = p.product_id
            WHERE
                w.warehouse_id = :warehouse_id and ws.units > 0

            """
        return query

    @staticmethod
    def get_units_product_query():
        query = """
            SELECT  
                p.*,
                w.warehouse_name,
                w.warehouse_id,
                (ws.units - COALESCE(SUM(CASE WHEN md.status = 'Transfer' THEN md.quantity ELSE 0 END), 0)) AS stock_disponible,
                MAX(md.status) AS status
            FROM 
                warehousestock ws
            JOIN 
                warehouses w ON ws.warehouse_id = w.warehouse_id
            JOIN 
                products p ON ws.product_id = p.product_id
            LEFT JOIN
                movementdetail md ON md.product_id = p.product_id AND md.status = 'Transfer'
            WHERE
                w.warehouse_id = :warehouse_id AND p.product_id = :product_id

            """
        return query
    
    @staticmethod
    def filter_products_imei():
        query = """
            SELECT  
                p.*,
                w.warehouse_name,
                w.warehouse_id,
                ws.units AS stock_disponible
            FROM 
                warehousestock ws
            JOIN 
                warehouses w ON ws.warehouse_id = w.warehouse_id
            JOIN 
                products p ON ws.product_id = p.product_id
                WHERE imei = :imei
            GROUP BY 
                p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
            ORDER BY 
                w.warehouse_name;
        """
        return query

    @staticmethod
    def get_product_imei():
        query = """
            SELECT 
                productname,
                imei,
                storage,
                battery,
                color
            FROM 
                Products
            WHERE imei = :imei;
            """
        return query
    
    @staticmethod
    def filter_products_all_fields():
        query = """
                SELECT 
                    p.*,
                    w.warehouse_name,
                    w.warehouse_id,
                    COALESCE(SUM(CASE 
                        WHEN m.movement_type IN ('Entry', 'Update') THEN md.quantity
                        WHEN m.movement_type IN ('Sold') THEN -md.quantity
                        ELSE 0 
                    END), 0) AS available_units_in_warehouse
                FROM 
                    Products p
                LEFT JOIN 
                    MovementDetail md ON p.product_id = md.product_id
                LEFT JOIN 
                    Movement m ON md.movement_id = m.movement_id
                LEFT JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                WHERE
                    p.productname ILIKE :productname
                    AND p.current_status = :current_status
                    AND w.warehouse_name = :warehouse
                    AND p.category ILIKE :category
                GROUP BY 
                    p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
                ORDER BY 
                    w.warehouse_name;
                """
        return query
    
    @staticmethod
    def filter_products_no_category():
        query = """
                SELECT 
                    p.*,
                    w.warehouse_name,
                    w.warehouse_id,
                    COALESCE(SUM(CASE 
                        WHEN m.movement_type IN ('Entry', 'Update') THEN md.quantity
                        WHEN m.movement_type IN ('Sold') THEN -md.quantity
                        ELSE 0 
                    END), 0) AS available_units_in_warehouse
                FROM 
                    Products p
                LEFT JOIN 
                    MovementDetail md ON p.product_id = md.product_id
                LEFT JOIN 
                    Movement m ON md.movement_id = m.movement_id
                LEFT JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                WHERE
                    p.productname ILIKE :productname
                    AND p.current_status = :current_status
                    AND w.warehouse_name = :warehouse
                GROUP BY 
                    p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
                ORDER BY 
                    w.warehouse_name;
                """
        return query
    
    @staticmethod
    def filter_products_no_warehouse():
        query = """
                SELECT 
                    p.*,
                    w.warehouse_name,
                    w.warehouse_id,
                    COALESCE(SUM(CASE 
                        WHEN m.movement_type IN ('Entry', 'Update') THEN md.quantity
                        WHEN m.movement_type IN ('Sold') THEN -md.quantity
                        ELSE 0 
                    END), 0) AS available_units_in_warehouse
                FROM 
                    Products p
                LEFT JOIN 
                    MovementDetail md ON p.product_id = md.product_id
                LEFT JOIN 
                    Movement m ON md.movement_id = m.movement_id
                LEFT JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                WHERE
                    p.productname ILIKE :productname
                    AND p.current_status = :current_status
                    AND p.category ILIKE :category
                GROUP BY 
                    p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
                ORDER BY 
                    w.warehouse_name;
                """
        return query
    
    @staticmethod
    def filter_products_no_status():
        query = """
                SELECT 
                    p.*,
                    w.warehouse_name,
                    w.warehouse_id,
                    COALESCE(SUM(CASE 
                        WHEN m.movement_type IN ('Entry', 'Update') THEN md.quantity
                        WHEN m.movement_type IN ('Sold') THEN -md.quantity
                        ELSE 0 
                    END), 0) AS available_units_in_warehouse
                FROM 
                    Products p
                LEFT JOIN 
                    MovementDetail md ON p.product_id = md.product_id
                LEFT JOIN 
                    Movement m ON md.movement_id = m.movement_id
                LEFT JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                WHERE
                    p.productname ILIKE :productname
                    AND w.warehouse_name = :warehouse
                    AND p.category ILIKE :category
                GROUP BY 
                    p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
                ORDER BY 
                    w.warehouse_name;
                """
        return query
    
    @staticmethod
    def filter_products_no_product():
        query = """
                SELECT 
                    p.*,
                    w.warehouse_name,
                    w.warehouse_id,
                    COALESCE(SUM(CASE 
                        WHEN m.movement_type IN ('Entry', 'Update') THEN md.quantity
                        WHEN m.movement_type IN ('Sold') THEN -md.quantity
                        ELSE 0 
                    END), 0) AS available_units_in_warehouse
                FROM 
                    Products p
                LEFT JOIN 
                    MovementDetail md ON p.product_id = md.product_id
                LEFT JOIN 
                    Movement m ON md.movement_id = m.movement_id
                LEFT JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                WHERE
                    p.current_status = :current_status
                    AND w.warehouse_name = :warehouse
                    AND p.category ILIKE :category
                GROUP BY 
                    p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
                ORDER BY 
                    w.warehouse_name;
                """
        return query
    
    @staticmethod
    def filter_products_name_status():
        query = """
            SELECT 
                p.*,
                w.warehouse_name,
                w.warehouse_id,
                COALESCE(SUM(CASE 
                    WHEN m.movement_type IN ('Entry', 'Update') THEN md.quantity
                    WHEN m.movement_type IN ('Sold') THEN -md.quantity
                    ELSE 0 
                END), 0) AS available_units_in_warehouse
            FROM 
                Products p
            LEFT JOIN 
                MovementDetail md ON p.product_id = md.product_id
            LEFT JOIN 
                Movement m ON md.movement_id = m.movement_id
            LEFT JOIN 
                Warehouses w ON m.destination_warehouse_id = w.warehouse_id
            WHERE
                p.productname ILIKE :productname
                AND p.current_status = :current_status
            GROUP BY 
                p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
            ORDER BY 
                w.warehouse_name;
            """
        return query
    
    
    def filter_products_name_warehouse():
        query = """
                SELECT 
                    p.*,
                    w.warehouse_name,
                    w.warehouse_id,
                    COALESCE(SUM(CASE 
                        WHEN m.movement_type IN ('Entry', 'Update') THEN md.quantity
                        WHEN m.movement_type IN ('Sold') THEN -md.quantity
                        ELSE 0 
                    END), 0) AS available_units_in_warehouse
                FROM 
                    Products p
                LEFT JOIN 
                    MovementDetail md ON p.product_id = md.product_id
                LEFT JOIN 
                    Movement m ON md.movement_id = m.movement_id
                LEFT JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                WHERE
                    p.productname ILIKE :productname
                    AND w.warehouse_name = :warehouse
                GROUP BY 
                    p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
                ORDER BY 
                    w.warehouse_name;
            """
        return query
    
    @staticmethod
    def filter_products_status_category():
        query = """
            SELECT 
                p.*,
                w.warehouse_name,
                w.warehouse_id,
                COALESCE(SUM(CASE 
                    WHEN m.movement_type IN ('Entry', 'Update') THEN md.quantity
                    WHEN m.movement_type IN ('Sold') THEN -md.quantity
                    ELSE 0 
                END), 0) AS available_units_in_warehouse
            FROM 
                Products p
            LEFT JOIN 
                MovementDetail md ON p.product_id = md.product_id
            LEFT JOIN 
                Movement m ON md.movement_id = m.movement_id
            LEFT JOIN 
                Warehouses w ON m.destination_warehouse_id = w.warehouse_id
            WHERE
                p.current_status = :current_status
                AND p.category ILIKE :category
            GROUP BY 
                p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
            ORDER BY 
                w.warehouse_name;
                """
        return query
    
    @staticmethod
    def filter_products_warehouse_category():
        query = """
                SELECT 
                    p.*,
                    w.warehouse_name,
                    w.warehouse_id,
                    COALESCE(SUM(CASE 
                        WHEN m.movement_type IN ('Entry', 'Update') THEN md.quantity
                        WHEN m.movement_type IN ('Sold') THEN -md.quantity
                        ELSE 0 
                    END), 0) AS available_units_in_warehouse
                FROM 
                    Products p
                LEFT JOIN 
                    MovementDetail md ON p.product_id = md.product_id
                LEFT JOIN 
                    Movement m ON md.movement_id = m.movement_id
                LEFT JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                WHERE
                    w.warehouse_name = :warehouse
                    AND p.category ILIKE :category
                GROUP BY 
                    p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
                ORDER BY 
                    w.warehouse_name;
                """
        return query
    
    @staticmethod
    def filter_products_name():
        query = """
                SELECT 
                    p.*,
                    w.warehouse_name,
                    w.warehouse_id,
                    COALESCE(SUM(CASE 
                        WHEN m.movement_type IN ('Entry', 'Update') THEN md.quantity
                        WHEN m.movement_type IN ('Sold') THEN -md.quantity
                        ELSE 0 
                    END), 0) AS available_units_in_warehouse
                FROM 
                    Products p
                LEFT JOIN 
                    MovementDetail md ON p.product_id = md.product_id
                LEFT JOIN 
                    Movement m ON md.movement_id = m.movement_id
                LEFT JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                WHERE
                    p.productname ILIKE :productname
                GROUP BY 
                    p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
                ORDER BY 
                    w.warehouse_name;
                """
        return query
    
    @staticmethod
    def filter_products_status():
        query = """
                SELECT 
                    p.*,
                    w.warehouse_name,
                    w.warehouse_id,
                    COALESCE(SUM(CASE 
                        WHEN m.movement_type IN ('Entry', 'Update') THEN md.quantity
                        WHEN m.movement_type IN ('Sold') THEN -md.quantity
                        ELSE 0 
                    END), 0) AS available_units_in_warehouse
                FROM 
                    Products p
                LEFT JOIN 
                    MovementDetail md ON p.product_id = md.product_id
                LEFT JOIN 
                    Movement m ON md.movement_id = m.movement_id
                LEFT JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                WHERE
                    p.current_status = :current_status
                GROUP BY 
                    p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
                ORDER BY 
                    w.warehouse_name;
                """
        return query
    

    @staticmethod
    def filter_products_warehouse():
        query = """
                SELECT 
                    p.*,
                    w.warehouse_name,
                    w.warehouse_id,
                    COALESCE(SUM(CASE 
                        WHEN m.movement_type IN ('Entry', 'Update') THEN md.quantity
                        WHEN m.movement_type IN ('Sold') THEN -md.quantity
                        ELSE 0 
                    END), 0) AS available_units_in_warehouse
                FROM 
                    Products p
                LEFT JOIN 
                    MovementDetail md ON p.product_id = md.product_id
                LEFT JOIN 
                    Movement m ON md.movement_id = m.movement_id
                LEFT JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                WHERE
                    w.warehouse_name = :warehouse
                GROUP BY 
                    p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
                ORDER BY 
                    w.warehouse_name;
                """
        return query
    
        
    @staticmethod
    def filter_products_category():
        query = """
                SELECT 
                    p.*,
                    w.warehouse_name,
                    w.warehouse_id,
                    COALESCE(SUM(CASE 
                        WHEN m.movement_type IN ('Entry', 'Update') THEN md.quantity
                        WHEN m.movement_type IN ('Sold') THEN -md.quantity
                        ELSE 0 
                    END), 0) AS available_units_in_warehouse
                FROM 
                    Products p
                LEFT JOIN 
                    MovementDetail md ON p.product_id = md.product_id
                LEFT JOIN 
                    Movement m ON md.movement_id = m.movement_id
                LEFT JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                WHERE
                    p.category ILIKE :category
                GROUP BY 
                    p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
                ORDER BY 
                    w.warehouse_name;
                """
        return query
    
    @staticmethod
    def get_invoices_active_query():
        query = """
                SELECT 
                    invoice_id, type, document_number
                FROM invoices
                WHERE status = 'active'
                ORDER BY invoice_id ASC
            """
        return query
    
    @staticmethod
    def update_invoicedetail_query():
        query = """
            INSERT INTO invoicedetail(invoice_id,
	            product_id, quantity, price)
	        VALUES (?, ?, ?, ?);
        """

    @staticmethod
    def update_product_query():
        query = """
            UPDATE products
            SET 
                productname = :productname,
                imei = :imei,
                storage = :storage,
                battery = :battery,
                color = :color,
                description = :description,
                cost = :cost,
                category = :category,
                units = :units,
                supplier = :supplier,
                current_status = :current_status  -- 🔹 Agregamos la actualización del estado
            WHERE product_id = :product_id
        """

        query_movement = """
            INSERT INTO Movement (movement_type, origin_warehouse_id, destination_warehouse_id, 
                    creation_date, status, notes, created_by_user_id, handled_by_user_id)
            VALUES('Update-Data', :warehouse_id, :warehouse_id, CURRENT_TIMESTAMP, 'Update-Data', 'Actualización', :current_user, :current_user)
            RETURNING movement_id;
        """

        query_movement_detail ="""
            INSERT INTO MovementDetail (movement_id, product_id, quantity, status)
            VALUES(:movement_id, :product_id, 0, 'completed')       
        """

        query_update_warehouse_stock = """
            UPDATE warehousestock
            SET units = :units
            WHERE product_id = :product_id AND warehouse_id = :warehouse_id
        """

        return query, query_movement, query_movement_detail, query_update_warehouse_stock


    

    @staticmethod
    def get_movements_by_product_query():
        query = """
                SELECT 
                    m.movement_id,
                    ow.warehouse_name AS origin_warehouse,
                    dw.warehouse_name AS destination_warehouse,
                    m.creation_date,
                    m.status AS movement_status,
                    m.notes AS movement_notes,
                    m.movement_type,
                    creator.name AS created_by_user,
                    creator.role AS creator_role,
                    handler.name AS handled_by_user,
                    handler.role AS handler_role,
                    md.detail_id,
                    md.product_id,
                    md.quantity AS moved_quantity,
                    md.status AS detail_status,
                    md.rejection_reason,
                    r.return_id,
                    r.quantity AS returned_quantity,
                    r.return_date,
                    r.notes AS return_notes
                FROM movement AS m
                JOIN movementdetail AS md ON m.movement_id = md.movement_id
                LEFT JOIN return AS r ON md.detail_id = r.movement_detail_id
                JOIN warehouses AS ow ON m.origin_warehouse_id = ow.warehouse_id
                JOIN warehouses AS dw ON m.destination_warehouse_id = dw.warehouse_id
                JOIN users AS creator ON m.created_by_user_id = creator.user_id
                JOIN users AS handler ON m.handled_by_user_id = handler.user_id
                WHERE md.product_id = :product_id
                ORDER BY
                    m.creation_date ASC;
        """
        return query
    
    @staticmethod
    def add_product_with_initial_movement_query():
        query_product = """
            INSERT INTO Products (imei, storage, battery, color, description, cost, current_status, acquisition_date, productname, category, units, supplier)
            VALUES (:imei, :storage, :battery, :color, :description, :cost, 'In Warehouse', CURRENT_DATE, :productname, :category, :units, :supplier)
            RETURNING product_id;
            """
        query_stock = """
                INSERT INTO WarehouseStock (warehouse_id, product_id, units)
                VALUES(:warehouse_id, :product_id, :units) 
            """
        
        query_movement ="""
            INSERT INTO Movement (movement_type, origin_warehouse_id, destination_warehouse_id, 
                      creation_date, status, notes, created_by_user_id, handled_by_user_id)
            VALUES('Entry', :warehouse_id, :warehouse_id, CURRENT_TIMESTAMP, 'created', 'Inventario inicial', :current_user, :current_user)
            RETURNING movement_id;
            """
        
        query_movement_detail ="""
            INSERT INTO MovementDetail (movement_id, product_id, quantity, status)
            VALUES(:movement_id, :product_id, :units, 'completed')       
            """
        return query_product, query_stock, query_movement, query_movement_detail
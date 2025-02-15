class SQLQueries:

    @staticmethod
    def get_products_units():
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
                    w.warehouse_id = :warehouse_id
                GROUP BY 
                    p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
                ORDER BY 
                    w.warehouse_name;
            """
        return query
    
    @staticmethod
    def filter_products_imei():
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
                WHERE imei = :imei
                GROUP BY 
                    p.product_id, p.productname, p.imei, p.description, p.price, w.warehouse_id, w.warehouse_name
                ORDER BY 
                    w.warehouse_name;
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
                    supplier = :supplier

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

        return query, query_movement, query_movement_detail
    

    @staticmethod
    def get_movements_by_imei_query():
        query = """
                SELECT
                    m.movement_id,
                    m.movement_type,
                    m.creation_date,
                    m.status AS movement_status,
                    m.origin_warehouse_id,
                    origin.warehouse_name AS origin_warehouse_name,
                    m.destination_warehouse_id,
                    destination.warehouse_name AS destination_warehouse_name,
                    md.quantity AS movement_quantity,
                    md.status AS detail_status,
                    md.rejection_reason,
                    r.return_id,
                    r.quantity AS return_quantity,
                    r.return_date,
                    r.notes
                FROM
                    movement m
                JOIN
                    movementdetail md ON m.movement_id = md.movement_id
                JOIN
                    products p ON md.product_id = p.product_id
                LEFT JOIN
                    warehouses origin ON m.origin_warehouse_id = origin.warehouse_id
                LEFT JOIN
                    warehouses destination ON m.destination_warehouse_id = destination.warehouse_id
                LEFT JOIN
                    return r ON md.detail_id = r.movement_detail_id
                WHERE
                    p.imei = :imei
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
class SQLQueries:

    @staticmethod
    def get_products_units():
        query = """
            SELECT 
                    p.*,
                    w.warehouse_name,
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
        return query
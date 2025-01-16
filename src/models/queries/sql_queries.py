class SQLQueries:
    @staticmethod
    def get_all_products_query():
        query = """
               SELECT p.*, d.quantity,d.status AS detail_status, m.movement_id, m.origin_warehouse_id,
                    m.destination_warehouse_id, m.creation_date,m.status AS movement_status, w.warehouse_name,
                    i.invoice_id, i.document_number
                FROM 
                    Products p
                JOIN 
                    MovementDetail d ON p.product_id = d.product_id
                JOIN 
                    Movement m ON d.movement_id = m.movement_id
                JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                LEFT JOIN 
                    InvoiceDetail id ON p.product_id = id.product_id
                LEFT JOIN 
                    Invoices i ON id.invoice_id = i.invoice_id
                WHERE p.current_status = 'In Warehouse'
                LIMIT :limit OFFSET :offset;
        """
        return query
    
    @staticmethod
    def count_products_query():
        query = "SELECT COUNT(*) FROM products"
        return query
    
    @staticmethod
    def filter_products_imei():
        query = """
                    WITH filtered_products AS (
                        SELECT p.*, d.quantity,d.status AS detail_status, m.movement_id, m.origin_warehouse_id,
                            m.destination_warehouse_id, m.creation_date,m.status AS movement_status, w.warehouse_name,
                            i.invoice_id, i.document_number
                        FROM 
                            Products p
                        JOIN 
                            MovementDetail d ON p.product_id = d.product_id
                        JOIN 
                            Movement m ON d.movement_id = m.movement_id
                        JOIN 
                            Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                        LEFT JOIN 
                            InvoiceDetail id ON p.product_id = id.product_id
                        LEFT JOIN 
                            Invoices i ON id.invoice_id = i.invoice_id
                        WHERE imei = :imei)
                        SELECT 
                            (SELECT COUNT(*) FROM filtered_products) AS total_count,
                            fp.*
                        FROM filtered_products fp
                    """
        return query
    
    @staticmethod
    def filter_products_all_fields():
        query = """
                WITH filtered_products AS (
                SELECT p.*, d.quantity,d.status AS detail_status, m.movement_id, m.origin_warehouse_id,
                    m.destination_warehouse_id, m.creation_date,m.status AS movement_status, w.warehouse_name,
                    i.invoice_id, i.document_number
                FROM 
                    Products p
                JOIN 
                    MovementDetail d ON p.product_id = d.product_id
                JOIN 
                    Movement m ON d.movement_id = m.movement_id
                JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                LEFT JOIN 
                    InvoiceDetail id ON p.product_id = id.product_id
                LEFT JOIN 
                    Invoices i ON id.invoice_id = i.invoice_id
                WHERE
                    productname ILIKE :productname
                    AND p.current_status = :current_status
                    AND w.warehouse_name = :warehouse
                    AND p.category ILIKE :category)
                SELECT 
                    (SELECT COUNT(*) FROM filtered_products) AS total_count,
                    fp.*
                FROM filtered_products fp
                """
        return query
    
    @staticmethod
    def filter_products_no_category():
        query = """
                WITH filtered_products AS (
                    SELECT p.*, d.quantity,d.status AS detail_status, m.movement_id, m.origin_warehouse_id,
                    m.destination_warehouse_id, m.creation_date,m.status AS movement_status, w.warehouse_name,
                    i.invoice_id, i.document_number
                    FROM 
                        Products p
                    JOIN 
                        MovementDetail d ON p.product_id = d.product_id
                    JOIN 
                        Movement m ON d.movement_id = m.movement_id
                    JOIN 
                        Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                    LEFT JOIN 
                        InvoiceDetail id ON p.product_id = id.product_id
                    LEFT JOIN 
                        Invoices i ON id.invoice_id = i.invoice_id
                    WHERE
                        productname ILIKE :productname
                        AND p.current_status = :current_status
                        AND w.warehouse_name = :warehouse
                    )
                    SELECT 
                        (SELECT COUNT(*) FROM filtered_products) AS total_count,
                        fp.*
                    FROM filtered_products fp
                """
        return query
    
    @staticmethod
    def filter_products_no_warehouse():
        query = """
                WITH filtered_products AS (
                SELECT p.*, d.quantity,d.status AS detail_status, m.movement_id, m.origin_warehouse_id,
                    m.destination_warehouse_id, m.creation_date,m.status AS movement_status, w.warehouse_name,
                    i.invoice_id, i.document_number
                    FROM 
                        Products p
                    JOIN 
                        MovementDetail d ON p.product_id = d.product_id
                    JOIN 
                        Movement m ON d.movement_id = m.movement_id
                    JOIN 
                        Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                    LEFT JOIN 
                        InvoiceDetail id ON p.product_id = id.product_id
                    LEFT JOIN 
                        Invoices i ON id.invoice_id = i.invoice_id
                WHERE
                    productname ILIKE :productname
                    AND p.current_status = :current_status
                    AND p.category ILIKE :category)
                SELECT 
                    (SELECT COUNT(*) FROM filtered_products) AS total_count,
                    fp.*
                FROM filtered_products fp
                """
        return query
    
    @staticmethod
    def filter_products_no_status():
        query = """
                WITH filtered_products AS (
                SELECT p.*, d.quantity,d.status AS detail_status, m.movement_id, m.origin_warehouse_id,
                    m.destination_warehouse_id, m.creation_date,m.status AS movement_status, w.warehouse_name,
                    i.invoice_id, i.document_number
                    FROM 
                        Products p
                    JOIN 
                        MovementDetail d ON p.product_id = d.product_id
                    JOIN 
                        Movement m ON d.movement_id = m.movement_id
                    JOIN 
                        Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                    LEFT JOIN 
                        InvoiceDetail id ON p.product_id = id.product_id
                    LEFT JOIN 
                        Invoices i ON id.invoice_id = i.invoice_id
                WHERE
                    productname ILIKE :productname
                    AND w.warehouse_name = :warehouse
                    AND p.category ILIKE :category)
                SELECT 
                    (SELECT COUNT(*) FROM filtered_products) AS total_count,
                    fp.*
                FROM filtered_products fp
                """
        return query
    
    @staticmethod
    def filter_products_no_product():
        query = """
                WITH filtered_products AS (
                SELECT p.*, d.quantity,d.status AS detail_status, m.movement_id, m.origin_warehouse_id,
                    m.destination_warehouse_id, m.creation_date,m.status AS movement_status, w.warehouse_name,
                    i.invoice_id, i.document_number
                    FROM 
                        Products p
                    JOIN 
                        MovementDetail d ON p.product_id = d.product_id
                    JOIN 
                        Movement m ON d.movement_id = m.movement_id
                    JOIN 
                        Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                    LEFT JOIN 
                        InvoiceDetail id ON p.product_id = id.product_id
                    LEFT JOIN 
                        Invoices i ON id.invoice_id = i.invoice_id
                WHERE
                    p.current_status = :current_status
                    AND w.warehouse_name = :warehouse
                    AND p.category ILIKE :category)
                SELECT 
                    (SELECT COUNT(*) FROM filtered_products) AS total_count,
                    fp.*
                FROM filtered_products fp
                """
        return query
    
    @staticmethod
    def filter_products_name_status():
        query = """
            WITH filtered_products AS (
            SELECT p.*, d.quantity,d.status AS detail_status, m.movement_id, m.origin_warehouse_id,
                m.destination_warehouse_id, m.creation_date,m.status AS movement_status, w.warehouse_name,
                i.invoice_id, i.document_number
            FROM 
                Products p
            JOIN 
                MovementDetail d ON p.product_id = d.product_id
            JOIN 
                Movement m ON d.movement_id = m.movement_id
            JOIN 
                Warehouses w ON m.destination_warehouse_id = w.warehouse_id
            LEFT JOIN 
                InvoiceDetail id ON p.product_id = id.product_id
            LEFT JOIN 
                Invoices i ON id.invoice_id = i.invoice_id
            WHERE
                productname ILIKE :productname
                AND p.current_status = :current_status
            SELECT 
                (SELECT COUNT(*) FROM filtered_products) AS total_count,
                fp.*
            FROM filtered_products fp
            """
        return query
    
    
    def filter_products_name_warehouse():
        query = """
            WITH filtered_products AS (
            SELECT p.*, d.quantity,d.status AS detail_status, m.movement_id, m.origin_warehouse_id,
                m.destination_warehouse_id, m.creation_date,m.status AS movement_status, w.warehouse_name,
                i.invoice_id, i.document_number
            FROM 
                Products p
            JOIN 
                MovementDetail d ON p.product_id = d.product_id
            JOIN 
                Movement m ON d.movement_id = m.movement_id
            JOIN 
                Warehouses w ON m.destination_warehouse_id = w.warehouse_id
            LEFT JOIN 
                InvoiceDetail id ON p.product_id = id.product_id
            LEFT JOIN 
                Invoices i ON id.invoice_id = i.invoice_id
            WHERE
                productname ILIKE :productname
                AND w.warehouse_name = :warehouse)
            SELECT 
                (SELECT COUNT(*) FROM filtered_products) AS total_count,
                fp.*
            FROM filtered_products fp
            """
        return query
    
    @staticmethod
    def filter_products_status_category():
        query = """
                WITH filtered_products AS (
                SELECT p.*, d.quantity,d.status AS detail_status, m.movement_id, m.origin_warehouse_id,
                    m.destination_warehouse_id, m.creation_date,m.status AS movement_status, w.warehouse_name,
                    i.invoice_id, i.document_number
                FROM 
                    Products p
                JOIN 
                    MovementDetail d ON p.product_id = d.product_id
                JOIN 
                    Movement m ON d.movement_id = m.movement_id
                JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                LEFT JOIN 
                    InvoiceDetail id ON p.product_id = id.product_id
                LEFT JOIN 
                    Invoices i ON id.invoice_id = i.invoice_id
                WHERE
                    p.current_status = :current_status
                    AND p.category ILIKE :category)
                SELECT 
                    (SELECT COUNT(*) FROM filtered_products) AS total_count,
                    fp.*
                FROM filtered_products fp
                """
        return query
    
    @staticmethod
    def filter_products_warehouse_category():
        query = """
                WITH filtered_products AS (
                SELECT p.*, d.quantity,d.status AS detail_status, m.movement_id, m.origin_warehouse_id,
                    m.destination_warehouse_id, m.creation_date,m.status AS movement_status, w.warehouse_name,
                    i.invoice_id, i.document_number
                FROM 
                    Products p
                JOIN 
                    MovementDetail d ON p.product_id = d.product_id
                JOIN 
                    Movement m ON d.movement_id = m.movement_id
                JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                LEFT JOIN 
                    InvoiceDetail id ON p.product_id = id.product_id
                LEFT JOIN 
                    Invoices i ON id.invoice_id = i.invoice_id
                WHERE
                    w.warehouse_name = :warehouse
                    AND p.category ILIKE :category)
                SELECT 
                    (SELECT COUNT(*) FROM filtered_products) AS total_count,
                    fp.*
                FROM filtered_products fp
                """
        return query
    
    @staticmethod
    def filter_products_name():
        query = """
                WITH filtered_products AS (
                SELECT p.*, d.quantity,d.status AS detail_status, m.movement_id, m.origin_warehouse_id,
                    m.destination_warehouse_id, m.creation_date,m.status AS movement_status, w.warehouse_name,
                    i.invoice_id, i.document_number
                FROM 
                    Products p
                JOIN 
                    MovementDetail d ON p.product_id = d.product_id
                JOIN 
                    Movement m ON d.movement_id = m.movement_id
                JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                LEFT JOIN 
                    InvoiceDetail id ON p.product_id = id.product_id
                LEFT JOIN 
                    Invoices i ON id.invoice_id = i.invoice_id
                WHERE
                    p.category ILIKE :category)
                SELECT 
                    (SELECT COUNT(*) FROM filtered_products) AS total_count,
                    fp.*
                FROM filtered_products fp
                """
        return query
    
    @staticmethod
    def filter_products_status():
        query = """
                WITH filtered_products AS (
                SELECT p.*, d.quantity,d.status AS detail_status, m.movement_id, m.origin_warehouse_id,
                    m.destination_warehouse_id, m.creation_date,m.status AS movement_status, w.warehouse_name,
                    i.invoice_id, i.document_number
                FROM 
                    Products p
                JOIN 
                    MovementDetail d ON p.product_id = d.product_id
                JOIN 
                    Movement m ON d.movement_id = m.movement_id
                JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                LEFT JOIN 
                    InvoiceDetail id ON p.product_id = id.product_id
                LEFT JOIN 
                    Invoices i ON id.invoice_id = i.invoice_id
                WHERE
                    p.current_status = :current_status)
                SELECT 
                    (SELECT COUNT(*) FROM filtered_products) AS total_count,
                    fp.*
                FROM filtered_products fp
                """
        return query
    

    @staticmethod
    def filter_products_warehouse():
        query = """
                WITH filtered_products AS (
                SELECT p.*, d.quantity,d.status AS detail_status, m.movement_id, m.origin_warehouse_id,
                    m.destination_warehouse_id, m.creation_date,m.status AS movement_status, w.warehouse_name,
                    i.invoice_id, i.document_number
                FROM 
                    Products p
                JOIN 
                    MovementDetail d ON p.product_id = d.product_id
                JOIN 
                    Movement m ON d.movement_id = m.movement_id
                JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                LEFT JOIN 
                    InvoiceDetail id ON p.product_id = id.product_id
                LEFT JOIN 
                    Invoices i ON id.invoice_id = i.invoice_id
                WHERE
                    w.warehouse_name = :warehouse)
                SELECT 
                    (SELECT COUNT(*) FROM filtered_products) AS total_count,
                    fp.*
                FROM filtered_products fp
                """
        return query
    
        
    @staticmethod
    def filter_products_category():
        query = """
                WITH filtered_products AS (
                SELECT p.*, d.quantity,d.status AS detail_status, m.movement_id, m.origin_warehouse_id,
                    m.destination_warehouse_id, m.creation_date,m.status AS movement_status, w.warehouse_name,
                    i.invoice_id, i.document_number
                FROM 
                    Products p
                JOIN 
                    MovementDetail d ON p.product_id = d.product_id
                JOIN 
                    Movement m ON d.movement_id = m.movement_id
                JOIN 
                    Warehouses w ON m.destination_warehouse_id = w.warehouse_id
                LEFT JOIN 
                    InvoiceDetail id ON p.product_id = id.product_id
                LEFT JOIN 
                    Invoices i ON id.invoice_id = i.invoice_id
                WHERE
                    p.category ILIKE :category)
                SELECT 
                    (SELECT COUNT(*) FROM filtered_products) AS total_count,
                    fp.*
                FROM filtered_products fp
                """
        return query
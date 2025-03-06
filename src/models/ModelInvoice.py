from sqlalchemy import text
from .entities.invoice import Invoice
from .queries.sql_queries import SQLQueries

class ModelInvoice:

    @staticmethod
    def update_invoicedetail(db, invoice_id, product_id, quantity, price):
        try:
            query = text("""
                UPDATE invoice_details
                SET quantity = :quantity, price = :price
                WHERE invoice_id = :invoice_id AND product_id = :product_id
            """)

            params = {
                "invoice_id": invoice_id,
                "product_id": product_id,
                "quantity": quantity,
                "price": price
            }

            result = db.session.execute(query, params)

            # Verificar si se actualizó alguna fila
            if result.rowcount == 0:
                raise ValueError("No se encontró el detalle de factura para actualizar.")

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Error al actualizar el detalle de la factura: {e}")
            return False


    @staticmethod
    def create_invoice_detail(db, invoice_id, product_id, quantity, price):
        try:
            query = text("""
                INSERT INTO invoicedetail (invoice_id, product_id, quantity, price)
                VALUES (:invoice_id, :product_id, :quantity, :price)
            """)

            db.session.execute(query, {
                'invoice_id': invoice_id,
                'product_id': product_id,
                'quantity': quantity,
                'price': price
            })
            
            db.session.commit()
            return True
        except Exception as e:
            print(f"❌ Error al insertar detalle de factura: {e}")
            db.session.rollback()
            return False




    @staticmethod
    def get_invoices_active(db):
        query = text(SQLQueries.get_invoices_active_query())

        result = db.session.execute(query).mappings().fetchall()
        
        if result:           
            # Construye la lista de productos excluyendo 'total_count'
            invoice = [dict(row) for row in result]
            
        else:
            invoice = []  # Si no hay resultados, inicializa la lista vacía
        return invoice


    @staticmethod
    def get_invoices_paginated(db, limit, offset):
        query = text("""
            SELECT 
                *
            FROM invoices
            ORDER BY invoice_id ASC
            LIMIT :limit OFFSET :offset;
        """)
        result = db.session.execute(query, {"limit": limit, "offset": offset}).fetchall()
        
        return [
            Invoice(
                invoice_id=row[0],
                type=row[1],
                document_number=row[2],
                date=row[3],
                client=row[4],
                status=row[5],
            )
            for row in result
        ]

    @staticmethod
    def count_invoices(db):
        query = text("SELECT COUNT(*) FROM invoices")
        total = db.session.execute(query).scalar()
        return total

    @staticmethod
    def filter_invoices(db, document_number=None, client_name=None, invoice_type=None, status=None, limit=10, offset=0):
        try:
            query = """
            WITH filtered_invoices AS (
                SELECT * FROM invoices WHERE 1=1
        """
            params = {}

            if document_number:
                query += " AND document_number ILIKE :document_number"
                params["document_number"] = f"%{document_number}%"

            if client_name:
                query += " AND client ILIKE :client_name"
                params["client_name"] = f"%{client_name}%"

            if invoice_type:
                query += " AND type = :invoice_type"
                params["invoice_type"] = invoice_type

            if status:
                query += " AND status = :status"
                params["status"] = status

            query += """
            )
            SELECT 
                (SELECT COUNT(*) FROM filtered_invoices) AS total_count,
                fi.*
            FROM filtered_invoices fi
            ORDER BY invoice_id ASC
            LIMIT :limit OFFSET :offset;
        """
        
            params["limit"] = limit
            params["offset"] = offset

            print(f"🛠 SQL Generado: {query}")
            print(f"📊 Parámetros: {params}")

            result = db.session.execute(text(query), params).mappings().fetchall()
        
            total_count = result[0]['total_count'] if result else 0
            invoices = [
                Invoice(
                    invoice_id=row['invoice_id'],
                    type=row['type'],
                    document_number=row['document_number'],
                    date=row['date'],
                    client=row['client'],
                    status=row['status']  # Agregamos el estado
                )
                for row in result
            ]

            return invoices, total_count

        except Exception as e:
            print(f"❌ Error filtering invoices: {e}")
            return [], 0



    @staticmethod
    def get_invoice_by_id(db, invoice_id):
        query = text("""
            SELECT invoice_id, type, document_number, date, client
            FROM invoices
            WHERE invoice_id = :invoice_id
        """)
        row = db.session.execute(query, {"invoice_id": invoice_id}).fetchone()
        if row:
            return Invoice(
                invoice_id=row[0],
                type=row[1],
                document_number=row[2],
                date=row[3],
                client=row[4]
            )
        return None

    @staticmethod
    def update_invoice(db, invoice):
        query = text("""
            UPDATE invoices
            SET type = :type,
                document_number = :document_number,
                date = :date,
                client = :client
            WHERE invoice_id = :invoice_id;
        """)
        params = {
            "type": invoice.type,
            "document_number": invoice.document_number,
            "date": invoice.date,
            "client": invoice.client,
            "invoice_id": invoice.invoice_id
        }
        try:
            db.session.execute(query, params)
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error updating invoice: {e}")
            db.session.rollback()
            return False

    @staticmethod
    def get_active_invoices(db):
        query = text("""
            SELECT invoice_id, document_number 
            FROM invoices 
            WHERE status = 'active'
        """)
        result = db.session.execute(query).fetchall()
        return [{"invoice_id": row[0], "document_number": row[1]} for row in result]
    

    @staticmethod
    def create_invoice(db, invoice_type, document_number, date, client, status):
        try:
            query = text("""
                INSERT INTO invoices (type, document_number, date, client, status)
                VALUES (:type, :document_number, :date, :client, :status)
                RETURNING invoice_id;
            """)

            result = db.session.execute(query, {
                'type': invoice_type,
                'document_number': document_number,
                'date': date,
                'client': client,
                'status': status
            })

            invoice_id = result.fetchone()[0]  # Obtiene el ID generado
            db.session.commit()
            return invoice_id  # Devuelve el invoice_id
        except Exception as e:
            print(f"❌ Error al insertar factura: {e}")
            db.session.rollback()
            return None

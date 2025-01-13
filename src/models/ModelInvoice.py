from sqlalchemy import text
from .entities.invoice import Invoice

class ModelInvoice:

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
    def filter_invoices(db, document_number=None, client_name=None, invoice_type=None, limit=10, offset=0):
        try:
            query = text("""
                WITH filtered_invoices AS (
                    SELECT *
                    FROM invoices
                    WHERE 
                        (:document_number IS NULL OR document_number ILIKE :document_number)
                        AND (:client_name IS NULL OR client ILIKE :client_name)
                        AND (:invoice_type IS NULL OR type = :invoice_type)
                )
                SELECT 
                    (SELECT COUNT(*) FROM filtered_invoices) AS total_count,
                    fi.*
                FROM filtered_invoices fi
                ORDER BY invoice_id ASC
                LIMIT :limit OFFSET :offset;
            """)
            
            params = {
                "document_number": f"%{document_number}%" if document_number else None,
                "client_name": f"%{client_name}%" if client_name else None,
                "invoice_type": invoice_type,
                "limit": limit,
                "offset": offset
            }
            
            result = db.session.execute(query, params).mappings().fetchall()
            
            # Extrae el conteo total y los datos de facturas
            total_count = result[0]['total_count'] if result else 0
            invoices = [
                Invoice(
                    invoice_id=row['invoice_id'],
                    type=row['type'],
                    document_number=row['document_number'],
                    date=row['date'],
                    client=row['client']
                )
                for row in result
            ]
            return invoices, total_count

        except Exception as e:
            print(f"Error filtering invoices: {e}")
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
            """)
            db.session.execute(query, {
                'type': invoice_type,
                'document_number': document_number,
                'date': date,
                'client': client,
                'status': status
            })
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error al insertar factura: {e}")
            db.session.rollback()
            return False
class Invoice:
    def __init__(self, invoice_id, type, document_number, date, client, status = None) -> None:
        self.invoice_id = invoice_id
        self.type = type
        self.document_number = document_number
        self.date = date
        self.client = client
        self.status = status

    def to_dict(self):
        return {
            "invoice_id": self.invoice_id,
            "type": self.type,
            "document_number": self.document_number,
            "date": str(self.date),
            "client": self.client,
            "status": self.status
        }

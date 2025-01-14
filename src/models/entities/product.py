import datetime
class Products():

    def __init__(self, product_id,productname, imei, storage, battery, color, description, cost, current_status, warehouse_name = None, acquisition_date = None,document_number = None, price = None, category = None) -> None:
        self.product_id = product_id
        self.productname = productname
        self.imei = imei
        self.storage = storage
        self.battery = battery
        self.color = color
        self.description = description
        self.cost = cost
        self.current_status = current_status
        self.warehouse_name = warehouse_name
        self.acquisition_date = acquisition_date #'2023-12-01'
        self.document_number = document_number
        self.price = price
        self.category = category

    def get_id(self):
        # Flask-Login necesita que esto devuelva una cadena
        return str(self.product_id)

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "productname": self.productname,
            "imei": self.imei,
            "storage": self.storage,
            "battery": self.battery,
            "color": self.color,
            "description": self.description,
            "cost": float(self.cost),
            "current_status": self.current_status,
            "document_number": self.document_number,
            "warehouse_name": self.warehouse_name,
            "acquisition_date": self.acquisition_date[0].strftime("%Y-%m-%d") if isinstance(self.acquisition_date, tuple) else self.acquisition_date.strftime("%Y-%m-%d"),
            "price": float(self.price) if self.price else None,
            "category": self.category
        }
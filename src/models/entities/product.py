
class Products():

    def __init__(self, product_id,productname, imei, storage, battery, color, description, cost, current_status, acquisition_date, warehouse_name = None) -> None:
        self.product_id = product_id
        self.productname = productname
        self.imei = imei
        self.storage = storage
        self.battery = battery
        self.color = color
        self.description = description
        self.cost = cost
        self.current_status = current_status
        self.acquisition_date = acquisition_date, #'2023-12-01'
        self.warehouse_name = warehouse_name

    def get_id(self):
        # Flask-Login necesita que esto devuelva una cadena
        return str(self.product_id)
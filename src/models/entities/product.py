
class Products():

    def __init__(self, product_id,productname, imei, storage, battery, color, description, cost, current_status) -> None:
        self.product_id = product_id
        self.productname = productname
        self.imei = imei
        self.storage = storage
        self.battery = battery
        self.color = color
        self.description = description
        self.cost = cost
        self.current_status = current_status

    def get_id(self):
        # Flask-Login necesita que esto devuelva una cadena
        return str(self.product_id)
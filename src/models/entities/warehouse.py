class Warehouse():

    def __init__(self, warehouse_id,warehouse_name) -> None:
        self.warehouse_id = warehouse_id
        self.warehouse_name = warehouse_name

    def get_id(self):
        # Flask-Login necesita que esto devuelva una cadena
        return str(self.productwarehouse_id)
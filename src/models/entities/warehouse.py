class Warehouse():

    def __init__(self, productwarehouse_id,warehouse_name) -> None:
        self.productwarehouse_id = productwarehouse_id
        self.warehouse_name = warehouse_name

    def get_id(self):
        # Flask-Login necesita que esto devuelva una cadena
        return str(self.productwarehouse_id)
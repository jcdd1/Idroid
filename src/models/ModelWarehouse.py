from sqlalchemy import text
from .entities.warehouse import Warehouse

class ModelWarehouse():

    @staticmethod
    def get_all_warehouses(db):
        query = text("SELECT warehouse_id, warehouse_name FROM warehouses")
        result = db.session.execute(query).mappings().fetchall()
        return result
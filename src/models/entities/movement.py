class Movement:
    def __init__(self, movement_id, origin_warehouse_id, destination_warehouse_id, creation_date, status, notes, created_by_user_id, handled_by_user_id = None) -> None:
        self.movement_id = movement_id
        self.origin_warehouse_id = origin_warehouse_id
        self.destination_warehouse_id = destination_warehouse_id
        self.creation_date = creation_date
        self.status = status
        self.notes = notes
        self.created_by_user_id = created_by_user_id
        self.handled_by_user_id = handled_by_user_id

    def to_dict(self):
        return {
            "movement_id": self.movement_id,
            "origin_warehouse_id": self.origin_warehouse_id,
            "destination_warehouse_id": self.destination_warehouse_id,
            "creation_date": self.creation_date,
            "status": self.status,
            "notes": self.notes,
            "created_by_user_id": self.created_by_user_id,
            "handled_by_user_id": self.handled_by_user_id
        }
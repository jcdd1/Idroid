class Movement:
    def __init__(self, movement_id, product_id, origin_warehouse_id, destination_warehouse_id, 
                 sender_user_id, receiver_user_id, send_date, receive_date, 
                 movement_status, movement_description):
        self.movement_id = movement_id
        self.product_id = product_id
        self.origin_warehouse_id = origin_warehouse_id
        self.destination_warehouse_id = destination_warehouse_id
        self.sender_user_id = sender_user_id
        self.receiver_user_id = receiver_user_id
        self.send_date = send_date
        self.receive_date = receive_date
        self.movement_status = movement_status
        self.movement_description = movement_description

    def to_dict(self):
        return {
            "movement_id": self.movement_id,
            "product_id": self.product_id,
            "origin_warehouse_id": self.origin_warehouse_id,
            "destination_warehouse_id": self.destination_warehouse_id,
            "sender_user_id": self.sender_user_id,
            "receiver_user_id": self.receiver_user_id,
            "send_date": str(self.send_date) if self.send_date else None,
            "receive_date": str(self.receive_date) if self.receive_date else None,
            "movement_status": self.movement_status,
            "movement_description": self.movement_description
        }

document.addEventListener("DOMContentLoaded", () => {
    const editMovementModal = document.getElementById("editMovementModal");
    const editButtons = document.querySelectorAll("button[data-bs-target='#editMovementModal']");

    
    editButtons.forEach(button => {
        button.addEventListener("click", () => {
           
            const movementData = JSON.parse(button.getAttribute("data-movement"));

            
            document.getElementById("movement_id").value = movementData.movement_id || "";
            document.getElementById("product_id").value = movementData.product_id || "";
            document.getElementById("origin_warehouse_id").value = movementData.origin_warehouse_id || "";
            document.getElementById("destination_warehouse_id").value = movementData.destination_warehouse_id || "";
            document.getElementById("sender_user_id").value = movementData.sender_user_id || "";
            document.getElementById("receiver_user_id").value = movementData.receiver_user_id || "";
            document.getElementById("send_date").value = movementData.send_date ? formatDateTime(movementData.send_date) : "";
            document.getElementById("receive_date").value = movementData.receive_date ? formatDateTime(movementData.receive_date) : "";
            document.getElementById("movement_status").value = movementData.movement_status || "New";
            document.getElementById("movement_description").value = movementData.movement_description || "";
        });
    });

    /**
     * Función para formatear una fecha y hora en formato "YYYY-MM-DDTHH:mm".
     * @param {string} dateTimeString 
     * @returns {string} 
     */
    function formatDateTime(dateTimeString) {
        const date = new Date(dateTimeString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        const hours = String(date.getHours()).padStart(2, "0");
        const minutes = String(date.getMinutes()).padStart(2, "0");
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }
});

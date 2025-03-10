document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ ScriptWarehouses.js cargado correctamente.");

    // 📝 Función para cargar datos al editar bodega
    document.querySelectorAll(".edit-warehouse-btn").forEach(button => {
        button.addEventListener("click", function () {
            const warehouseDataString = this.getAttribute("data-warehouse");

            console.log("🔍 Datos recibidos en botón de edición:", warehouseDataString);

            try {
                const warehouseData = JSON.parse(warehouseDataString); // Convertir JSON a objeto

                console.log("✅ Bodega cargada en el modal:", warehouseData);

                // Llenar los campos del formulario de edición
                document.getElementById("edit_warehouse_id").value = warehouseData.warehouse_id || "";
                document.getElementById("edit_warehouse_name").value = warehouseData.warehouse_name || "";
                document.getElementById("edit_address").value = warehouseData.address || "";
                document.getElementById("edit_phone").value = warehouseData.phone || "";

            } catch (error) {
                console.error("❌ Error al parsear JSON:", error);
            }
        });
    });

});

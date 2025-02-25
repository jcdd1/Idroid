document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ ScriptCreateMovement.js cargado correctamente");

    const movementModal = document.getElementById("createMovementModal");
    const saveMovementButton = document.getElementById("saveMovementButton");

    // Evento cuando se muestra el modal
    movementModal.addEventListener("show.bs.modal", function (event) {
        console.log("📌 Modal de movimiento abierto");

        const button = event.relatedTarget;  // Botón que activó el modal
        const row = button.closest("tr");  // Obtener la fila correspondiente en la tabla

        if (!row) {
            console.error("❌ Error: No se pudo encontrar la fila del producto.");
            alert("Error al obtener los datos del producto.");
            return;
        }

        // Extraer información de la fila de la tabla
        const productName = button.getAttribute("data-product-name") || "Desconocido"; // 🔹 Nombre del producto
        const productId = button.getAttribute("data-product-id") || ""; // 🔹 IMEI como ID del producto
        const originWarehouseId = button.getAttribute("data-origin-warehouse-id") || ""; // 🔹 ID del almacén de origen

        console.log("📦 Producto Seleccionado:");
        console.log("   🔹 Nombre:", productName);
        console.log("   🔹 ID (IMEI):", productId);
        console.log("   🔹 Origen ID:", originWarehouseId ? originWarehouseId : "⚠️ NO SE ENCONTRÓ ORIGEN");

        // Validar que el ID del producto y el almacén de origen existan
        if (!productId) {
            console.error("❌ Error: Producto ID vacío.");
            alert("Error: No se pudo obtener correctamente el ID del producto.");
            return;
        }
        if (!originWarehouseId) {
            console.error("❌ Error: La bodega de origen está vacía.");
            alert("Error: No se pudo obtener la bodega de origen del producto.");
            return;
        }

        // Rellenar los campos del modal con los datos obtenidos
        document.getElementById("product_id").value = productId;
        document.getElementById("product_name_movement").value = productName;
        document.getElementById("origin_warehouse_id").value = originWarehouseId;

        // Bloquear los campos que no deben editarse
        document.getElementById("product_name_movement").setAttribute("readonly", true);
        document.getElementById("origin_warehouse_id").setAttribute("readonly", true);

        // Ocultar la opción de destino que corresponde al almacén de origen
        const destinationSelect = document.getElementById("destination_warehouse_id");
        Array.from(destinationSelect.options).forEach(function(option) {
            if (option.value === originWarehouseId) {
                option.style.display = "none";
            }
        });

        // Si la opción actualmente seleccionada es la oculta, seleccionar la primera opción visible
        if (destinationSelect.value === originWarehouseId) {
            let newVal = "";
            for (let option of destinationSelect.options) {
                if (option.style.display !== "none") {
                    newVal = option.value;
                    break;
                }
            }
            destinationSelect.value = newVal;
        }
    });

    // Evento para restaurar las opciones del select al cerrar el modal
    movementModal.addEventListener("hidden.bs.modal", function () {
        const destinationSelect = document.getElementById("destination_warehouse_id");
        Array.from(destinationSelect.options).forEach(function(option) {
            option.style.display = "block";
        });
    });

    // Guardar el movimiento al hacer clic en "Guardar Cambios"
    saveMovementButton.addEventListener("click", function () {
        console.log("📌 Intentando guardar el movimiento...");

        const productId = document.getElementById("product_id").value;
        const originWarehouseId = document.getElementById("origin_warehouse_id").value;
        const destinationWarehouseId = document.getElementById("destination_warehouse_id").value;
        const movementDescription = document.getElementById("movement_description").value;

        // Validar que los datos requeridos estén completos
        if (!destinationWarehouseId) {
            alert("⚠️ Debes seleccionar un almacén de destino.");
            return;
        }
        if (!movementDescription.trim()) {
            alert("⚠️ Debes agregar una descripción del movimiento.");
            return;
        }

        console.log("📦 Enviando datos:");
        console.log("   🔹 Producto ID:", productId);
        console.log("   🔹 Origen ID:", originWarehouseId);
        console.log("   🔹 Destino ID:", destinationWarehouseId);
        console.log("   🔹 Descripción:", movementDescription);

        // Enviar la solicitud POST a Flask
        fetch("/create_movement", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('input[name="csrf_token"]').value
            },
            body: JSON.stringify({
                product_id: productId,
                origin_warehouse_id: originWarehouseId,
                destination_warehouse_id: destinationWarehouseId,
                movement_description: movementDescription
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("✅ Movimiento creado exitosamente.");
                location.reload(); // Recargar la página para actualizar la tabla
            } else {
                console.error("❌ Error al crear el movimiento:", data.message);
                alert("❌ Error al crear el movimiento: " + data.message);
            }
        })
        .catch(error => {
            console.error("❌ Error en la solicitud:", error);
            alert("❌ Ocurrió un error al procesar la solicitud.");
        });
    });
});

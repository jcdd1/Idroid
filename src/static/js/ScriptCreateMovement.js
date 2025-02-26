document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ ScriptCreateMovement.js cargado correctamente");

    const movementModal = document.getElementById("createMovementModal");
    const saveMovementButton = document.getElementById("saveMovementButton");
    const destinationWarehouseSelect = document.getElementById("destination_warehouse_id");
    const destinationUserSelect = document.getElementById("destination_user_id");
    const unitsToSendInput = document.getElementById("units_to_send");
    const maxUnitsDisplay = document.getElementById("max_units_display");
    const availableUnitsField = document.getElementById("available_units");

    // 🟢 Cargar usuarios vinculados al cambiar el almacén destino
    destinationWarehouseSelect.addEventListener("change", function () {
        const warehouseId = this.value;
        destinationUserSelect.innerHTML = '<option value="">Cargando usuarios...</option>';

        if (!warehouseId) {
            destinationUserSelect.innerHTML = '<option value="">Seleccione una bodega primero</option>';
            return;
        }

        fetch(`/get_users_by_warehouse/${warehouseId}`)
            .then(response => response.json())
            .then(data => {
                destinationUserSelect.innerHTML = '';
                if (data.users.length > 0) {
                    data.users.forEach(user => {
                        const option = document.createElement('option');
                        option.value = user.id;
                        option.textContent = user.name;
                        destinationUserSelect.appendChild(option);
                    });
                } else {
                    destinationUserSelect.innerHTML = '<option value="">No hay usuarios vinculados a esta bodega</option>';
                }
            })
            .catch(error => {
                console.error("❌ Error al cargar usuarios:", error);
                destinationUserSelect.innerHTML = '<option value="">Error al cargar usuarios</option>';
            });
    });

    // 🟡 Evento al abrir el modal de movimiento
    movementModal.addEventListener("show.bs.modal", function (event) {
        console.log("📌 Modal de movimiento abierto");

        const button = event.relatedTarget;
        const row = button.closest("tr");

        if (!row) {
            console.error("❌ Error: No se pudo encontrar la fila del producto.");
            alert("Error al obtener los datos del producto.");
            return;
        }

        const productName = button.getAttribute("data-product-name") || "Desconocido";
        const productId = button.getAttribute("data-product-id") || "";
        const originWarehouseId = button.getAttribute("data-origin-warehouse-id") || "";

        console.log("📦 Producto Seleccionado:", productName);

        document.getElementById("product_id").value = productId;
        document.getElementById("product_name_movement").value = productName;
        document.getElementById("origin_warehouse_id").value = originWarehouseId;

        destinationWarehouseSelect.value = "";
        destinationUserSelect.innerHTML = '<option value="">Seleccione una bodega</option>';

        // Ocultar el almacén de origen
        Array.from(destinationWarehouseSelect.options).forEach(option => {
            option.style.display = option.value === originWarehouseId ? "none" : "block";
        });

        //  Obtener unidades disponibles desde el backend
        fetch(`/get_product_units/${productId}/${originWarehouseId}`)
            .then(response => response.json())
            .then(data => {
                const availableUnits = data.available_units || 0;
                console.log("🔢 Unidades disponibles:", availableUnits);

                // 📝 Mostrar unidades disponibles y configurar campo de entrada
                availableUnitsField.textContent = availableUnits;
                unitsToSendInput.max = availableUnits;
                unitsToSendInput.value = 1;
                maxUnitsDisplay.textContent = availableUnits;
            })
            .catch(error => {
                console.error("❌ Error al obtener unidades disponibles:", error);
                availableUnitsField.textContent = "0";
                unitsToSendInput.max = 0;
            });
    });

    // 🟣 Evento para crear el movimiento al hacer clic en "Guardar Cambios"
    saveMovementButton.addEventListener("click", function () {
        const productId = document.getElementById("product_id").value;
        const originWarehouseId = document.getElementById("origin_warehouse_id").value;
        const destinationWarehouseId = destinationWarehouseSelect.value;
        const destinationUserId = destinationUserSelect.value;
        const movementDescription = document.getElementById("movement_description").value;
        const unitsToSend = unitsToSendInput.value;

        if (!destinationWarehouseId || !destinationUserId || unitsToSend <= 0) {
            alert("⚠️ Por favor, complete todos los campos correctamente.");
            return;
        }

        // 🟢 Llamada a la API para crear el movimiento
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
                destination_user_id: destinationUserId,
                movement_description: movementDescription,
                units_to_send: unitsToSend
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert("✅ Movimiento creado exitosamente.");
                    location.reload();
                } else {
                    console.error("❌ Error al crear el movimiento:", data.message);
                    alert("❌ Error: " + data.message);
                }
            })
            .catch(error => {
                console.error("❌ Error en la solicitud:", error);
                alert("❌ Ocurrió un error al procesar la solicitud.");
            });
    });

    // 🟣 Restaurar opciones del select al cerrar el modal
    movementModal.addEventListener("hidden.bs.modal", function () {
        Array.from(destinationWarehouseSelect.options).forEach(option => {
            option.style.display = "block";
        });
        destinationUserSelect.innerHTML = '<option value="">Seleccione una bodega</option>';
    });
});

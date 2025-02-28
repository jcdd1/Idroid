document.addEventListener('DOMContentLoaded', function () {
    const imeiInput = document.getElementById('imei_global');
    const addProductButton = document.getElementById('addMovementRow');
    const alertBox = document.getElementById('imeiAlert');
    const unitsInput = document.getElementById('units_global');
    const productNameInput = document.getElementById('product_name_global');
    const warehouseSelect = document.getElementById('warehouse_global');
    const userSelect = document.getElementById('user_global');
    const productTableBody = document.getElementById('productSummaryTableBody');
    const createMovementButton = document.getElementById('createMassiveMovementButton');
    const notesInput = document.getElementById('notes_global');

    let productsData = [];
    let availableUnits = 0;
    let userWarehouseId = null;
    let lastProductWarehouseId = null;

    // 🔄 Obtener la bodega del usuario
    fetch('/get_user_warehouse')
        .then(response => response.json())
        .then(data => {
            if (data && data.user_warehouse_id) {
                userWarehouseId = String(data.user_warehouse_id).trim();
                loadWarehouses(userWarehouseId);
            } else {
                alert("⚠️ Error al obtener el ID de la bodega del usuario.");
            }
        });

    // 🔄 Cargar bodegas disponibles (excepto la del usuario)
    function loadWarehouses(excludedWarehouseId) {
        warehouseSelect.innerHTML = '<option value="">Seleccione una bodega</option>';
        fetch('/get_all_warehouses')
            .then(response => response.json())
            .then(data => {
                if (data.warehouses && data.warehouses.length > 0) {
                    data.warehouses.forEach(warehouse => {
                        if (String(warehouse.warehouse_id).trim() !== excludedWarehouseId) {
                            const option = document.createElement("option");
                            option.value = warehouse.warehouse_id;
                            option.textContent = warehouse.warehouse_name;
                            warehouseSelect.appendChild(option);
                        }
                    });

                    // Auto-seleccionar la primera bodega si hay opciones
                    if (warehouseSelect.options.length > 1) {
                        warehouseSelect.selectedIndex = 1;
                        fetchUsersByWarehouse(warehouseSelect.value);
                    }
                } else {
                    console.error("❌ No se encontraron bodegas.");
                }
            })
            .catch(error => console.error('❌ Error al obtener bodegas:', error));
    }

    // 🔄 Obtener usuarios según la bodega seleccionada
    warehouseSelect.addEventListener('change', function () {
        const warehouseId = this.value;
        if (warehouseId) fetchUsersByWarehouse(warehouseId);
    });

    function fetchUsersByWarehouse(warehouseId) {
        userSelect.innerHTML = '<option value="">Cargando usuarios...</option>';
        fetch(`/get_users_by_warehouse/${warehouseId}`)
            .then(response => response.json())
            .then(data => {
                userSelect.innerHTML = '<option value="">Seleccione un usuario</option>';
                data.users.forEach(user => {
                    const option = document.createElement("option");
                    option.value = user.id;
                    option.textContent = user.name;
                    userSelect.appendChild(option);
                });
            })
            .catch(() => userSelect.innerHTML = '<option value="">Error al cargar usuarios</option>');
    }

    // 🔎 Buscar producto por IMEI
    imeiInput.addEventListener('input', function () {
        clearTimeout(this.typingTimer);
        this.typingTimer = setTimeout(fetchProductData, 500);
    });

    function fetchProductData() {
        const imei = imeiInput.value.trim();
        if (imei.length >= 5) {
            fetch(`/get_product_by_imei/${imei}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.product) {
                        productNameInput.value = data.product.productname || '';
                        availableUnits = data.product.units;
                        unitsInput.max = availableUnits;
                        unitsInput.placeholder = `Máximo ${availableUnits}`;

                        lastProductWarehouseId = String(data.product.warehouse_id).trim();

                        if (userWarehouseId === lastProductWarehouseId) {
                            addProductButton.disabled = false;
                            hideAlert();
                        } else {
                            showAlert("⚠️ El producto no se encuentra en tu bodega.");
                            addProductButton.disabled = true;
                        }
                    } else {
                        showAlert(data.message || '⚠️ Producto no encontrado.');
                        addProductButton.disabled = true;
                        clearProductFields();
                    }
                })
                .catch(() => {
                    showAlert('⚠️ Error al obtener la información del producto.');
                    addProductButton.disabled = true;
                    clearProductFields();
                });
        } else {
            clearProductFields();
            addProductButton.disabled = true;
            hideAlert();
        }
    }

    // ✅ Añadir producto a la tabla resumen
    addProductButton.addEventListener('click', function () {
        const imei = imeiInput.value.trim();
        const productName = productNameInput.value.trim();
        const units = unitsInput.value.trim();
        const warehouse = warehouseSelect.options[warehouseSelect.selectedIndex]?.text;
        const warehouseId = warehouseSelect.value;
        const user = userSelect.options[userSelect.selectedIndex]?.text;
        const userId = userSelect.value;

        if (!imei || !productName || !units || !warehouseId || !userId) {
            alert("⚠️ Todos los campos son obligatorios.");
            return;
        }

        if (productsData.some(product => product.imei === imei)) {
            alert("⚠️ Este producto ya ha sido añadido.");
            return;
        }

        productsData.push({ imei, productName, units, warehouse, warehouseId, user, userId });

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${imei}</td>
            <td>${productName}</td>
            <td>${units}</td>
            <td>${warehouse}</td>
            <td>${user}</td>
            <td><button type="button" class="btn btn-danger btn-sm remove-row">✖</button></td>
        `;
        productTableBody.appendChild(row);

        row.querySelector('.remove-row').addEventListener('click', function () {
            row.remove();
            productsData = productsData.filter(p => p.imei !== imei);
        });

        clearFormFields();
    });

    // ✅ Enviar datos al backend con fetch()
    createMovementButton.addEventListener('click', function (e) {
        e.preventDefault();
    
        if (productsData.length === 0) {
            alert("⚠️ Debe añadir al menos un producto antes de crear el movimiento.");
            return;
        }
    
        // Get the CSRF token from your form
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;
    
        // Format products data correctly
        const formattedProducts = productsData.map(product => ({
            product_id: product.imei,
            units_to_send: parseInt(product.units)
        }));
    
        const requestData = {
            products: formattedProducts,
            origin_warehouse_id: userWarehouseId,
            destination_warehouse_id: productsData[0].warehouseId,
            destination_user_id: productsData[0].userId,
            movement_description: ""  // Remove notesInput reference if it doesn't exist
        };
        
        console.log("Sending data to server:", requestData);
    
        fetch('/create_movement', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    try {
                        // Try to parse as JSON first
                        const data = JSON.parse(text);
                        console.error("Server error:", data);
                        throw new Error(data.message || "Error en el servidor");
                    } catch (e) {
                        // If not valid JSON, log the HTML response
                        console.error("Server returned HTML error:", text);
                        throw new Error("Error en el servidor - respuesta no válida");
                    }
                });
            }
            return response.json();
        })
        .then(data => {
            alert(data.success ? "✅ Movimiento creado exitosamente." : `❌ Error: ${data.message}`);
            if (data.success) location.reload();
        })
        .catch((error) => {
            console.error("Error in fetch:", error);
            alert(`❌ Error: ${error.message || "Error en el envío"}`);
        });
    });

    function clearProductFields() {
        productNameInput.value = '';
        unitsInput.value = '';
        availableUnits = 0;
        lastProductWarehouseId = null;
    }

    function clearFormFields() {
        imeiInput.value = '';
        clearProductFields();
        warehouseSelect.selectedIndex = 0;
        userSelect.innerHTML = '<option value="">Seleccione un usuario</option>';
    }

    function showAlert(message) {
        alertBox.textContent = message;
        alertBox.classList.remove('d-none');
    }

    function hideAlert() {
        alertBox.classList.add('d-none');
    }

    // ✅ El botón siempre está activo, pero valida si hay productos antes de enviar
    createMovementButton.disabled = false;
});


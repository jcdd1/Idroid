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
    const massiveMovementForm = document.getElementById('massiveMovementForm');
    const notesInput = document.getElementById('notes_global');

    let productsData = [];
    let availableUnits = 0;
    let userWarehouseId = null;
    let lastProductWarehouseId = null;

    const debugInfo = document.createElement('div');
    debugInfo.style.color = 'red';
    debugInfo.style.fontWeight = 'bold';
    debugInfo.id = 'debugInfo';
    document.querySelector('.modal-body').appendChild(debugInfo);

    //  Obtener bodega del usuario
    fetch('/get_user_warehouse')
        .then(response => response.json())
        .then(data => {
            if (data && data.user_warehouse_id) {
                userWarehouseId = String(data.user_warehouse_id).trim();
                document.getElementById('debugInfo').textContent = ` userWarehouseId: ${userWarehouseId}`;
                loadWarehouses(userWarehouseId);
            } else {
                alert("⚠️ Error al obtener el ID de la bodega del usuario.");
            }
        });

    //  Cargar bodegas disponibles (excepto la del usuario) con logs
    function loadWarehouses(excludedWarehouseId) {
        warehouseSelect.innerHTML = '<option value="">Seleccione una bodega</option>';
        fetch('/get_all_warehouses')
            .then(response => {
                console.log('📡 Estado respuesta:', response.status); 
                return response.json();
            })
            .then(data => {
                console.log("🏬 Bodegas recibidas:", data.warehouses); 
                if (data.warehouses && data.warehouses.length > 0) {
                    data.warehouses.forEach(warehouse => {
                        if (String(warehouse.warehouse_id).trim() !== excludedWarehouseId) {
                            const option = document.createElement("option");
                            option.value = warehouse.warehouse_id;
                            option.textContent = warehouse.warehouse_name;
                            warehouseSelect.appendChild(option);
                        }
                    });

                    //  Forzar selección de la primera bodega si existe
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

    //  Obtener usuarios por bodega
    warehouseSelect.addEventListener('change', function () {
        const warehouseId = this.value;
        console.log("🏢 Bodega seleccionada (ID):", warehouseId); 
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
                console.log("👤 Usuarios cargados:", data.users); 
            })
            .catch(() => userSelect.innerHTML = '<option value="">Error al cargar usuarios</option>');
    }

    //  Buscar producto por IMEI
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
                        document.getElementById('debugInfo').textContent = `📝 userWarehouseId: ${userWarehouseId} | productWarehouseId: ${lastProductWarehouseId}`;

                        if (userWarehouseId === lastProductWarehouseId) {
                            addProductButton.disabled = false;
                            hideAlert();
                        } else {
                            showAlert("⚠️ El producto no se encuentra en tu bodega. No se puede añadir.");
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

        if (lastProductWarehouseId !== userWarehouseId) {
            alert(`⚠️ Error: No puedes añadir el producto porque no pertenece a tu bodega.`);
            return;
        }

        if (!imei || !productName || !units || !warehouseId || !userId) {
            alert("⚠️ Todos los campos son obligatorios para añadir el producto.");
            return;
        }

        if (parseInt(units) > availableUnits) {
            alert(`⚠️ Solo hay ${availableUnits} unidades disponibles.`);
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
            <td class="text-end">
                <button type="button" class="btn btn-danger btn-sm remove-row">✖</button>
            </td>
        `;
        productTableBody.appendChild(row);

        row.querySelector('.remove-row').addEventListener('click', function () {
            row.remove();
            productsData = productsData.filter(p => p.imei !== imei);
            toggleSubmitButton();
            toggleRequiredFields();
        });

        clearFormFields();
        toggleSubmitButton();
        toggleRequiredFields();
    });

    // ✅ Crear movimiento masivo con validaciones y logs
    createMovementButton.addEventListener('click', function (e) {
        e.preventDefault();
        console.log(" Bodega seleccionada:", warehouseSelect.value); // 🔍 Debug
        console.log(" Usuario seleccionado:", userSelect.value); // 🔍 Debug

        if (productsData.length >= 2) {
            if (!warehouseSelect.value) {
                alert("⚠️ Debe seleccionar una bodega de destino.");
                console.error("❌ Bodega de destino vacía."); // 🔍 Debug
                return;
            }
            if (!userSelect.value) {
                alert("⚠️ Debe seleccionar un usuario vinculado.");
                console.error("❌ Usuario vinculado vacío."); // 🔍 Debug
                return;
            }

            imeiInput.removeAttribute('required');
            unitsInput.removeAttribute('required');
            warehouseSelect.removeAttribute('required');
            userSelect.removeAttribute('required');

            const formData = new FormData();
            formData.append('origin_warehouse_id', userWarehouseId);
            formData.append('destination_warehouse_id', warehouseSelect.value);
            formData.append('created_by_user_id', userSelect.value);
            formData.append('notes', notesInput ? notesInput.value : '');
            formData.append('csrf_token', document.querySelector('input[name="csrf_token"]').value);

            productsData.forEach((product, index) => {
                formData.append(`imei_${index}`, product.imei);
                formData.append(`units_${index}`, product.units);
            });

            console.log("📩 FormData enviado:", [...formData.entries()]);

            fetch(massiveMovementForm.action, {
                method: 'POST',
                body: formData
            })
                .then(response => {
                    console.log('📩 Estado de la respuesta:', response.status);
                    return response.json();
                })
                .then(data => {
                    console.log(' Respuesta del servidor:', data);
                    if (data.success) {
                        alert(" Movimiento masivo creado exitosamente.");
                        location.reload();
                    } else {
                        alert(`❌ Error: ${data.message}`);
                    }
                })
                .catch(error => console.error('❌ Error al enviar el formulario:', error));
        } else {
            alert("⚠️ Debe añadir al menos dos productos para crear el movimiento masivo.");
        }
    });

    // ✅ Funciones auxiliares
    function toggleRequiredFields() {
        if (productsData.length < 2) {
            imeiInput.setAttribute('required', true);
            unitsInput.setAttribute('required', true);
            warehouseSelect.setAttribute('required', true);
            userSelect.setAttribute('required', true);
        }
    }

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

    function toggleSubmitButton() {
        createMovementButton.disabled = productsData.length < 2;
    }

    toggleSubmitButton();
    toggleRequiredFields();
});

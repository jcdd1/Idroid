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

    let typingTimer;
    const typingInterval = 500;
    let productsData = [];
    let availableUnits = 0;

    imeiInput.addEventListener('input', function () {
        clearTimeout(typingTimer);
        typingTimer = setTimeout(fetchProductData, typingInterval);
    });

    warehouseSelect.addEventListener('change', function () {
        const warehouseId = this.value;
        if (warehouseId) fetchUsersByWarehouse(warehouseId);
    });

    addProductButton.addEventListener('click', function () {
        const imei = imeiInput.value.trim();
        const productName = productNameInput.value.trim();
        const units = unitsInput.value.trim();
        const warehouse = warehouseSelect.options[warehouseSelect.selectedIndex]?.text;
        const warehouseId = warehouseSelect.value;
        const user = userSelect.options[userSelect.selectedIndex]?.text;
        const userId = userSelect.value;

        if (!imei || !productName || !units || !warehouseId || !userId) {
            alert("⚠️ Todos los campos son obligatorios para añadir el producto.");
            return;
        }

        if (parseInt(units) > availableUnits) {
            alert(`⚠️ Solo hay ${availableUnits} unidades disponibles.`);
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
        });

        clearFormFields();
        toggleSubmitButton();
    });

    document.getElementById('massiveMovementForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const formData = new FormData();
        productsData.forEach((product, index) => {
            formData.append(`imei_${index}`, product.imei);
            formData.append(`product_name_${index}`, product.productName);
            formData.append(`units_${index}`, product.units);
            formData.append(`warehouse_id_${index}`, product.warehouseId);
            formData.append(`user_id_${index}`, product.userId);
        });
        console.log("Datos enviados:", Object.fromEntries(formData.entries()));
        this.submit();
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

                        if (data.product.warehouse_id !== data.current_user_warehouse_id) {
                            addProductButton.disabled = true;
                            showAlert("⚠️ El producto no se encuentra en tu bodega.");
                        } else {
                            addProductButton.disabled = false;
                            hideAlert();
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

    function clearProductFields() {
        productNameInput.value = '';
        unitsInput.value = '';
        availableUnits = 0;
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
        createMovementButton.disabled = productsData.length === 0;
    }

    toggleSubmitButton();
});
